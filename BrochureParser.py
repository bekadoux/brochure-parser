import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager
from Brochure import Brochure


class BrochureParser:
    def __init__(self) -> None:
        self._root_url = "https://www.prospektmaschine.de/"
        self._brochures = []
        self._brochure_dicts = []
        self._shop_routes = dict()

    def reset(self):
        self._brochures = []
        self._brochure_dicts = []
        self._shop_routes = dict()

    def parse(self, timeout=10, verbose=False):
        # Reset before parsing
        self.reset()

        self._parse_sidebar()
        self._parse_shop_pages(timeout=timeout, verbose=verbose)
        print(
            f"Parsed {len(self._shop_routes.keys())} shops and found {len(self._brochures)} actual brochures!"
        )

    def _parse_sidebar(self):
        response = requests.get(f"{self._root_url}/hypermarkte")

        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            sidebar_shops = soup.find("ul", id="left-category-shops")
            if sidebar_shops:
                for tag in sidebar_shops.find_all("a"):
                    self._shop_routes[tag.text.strip()] = tag.get("href")
        else:
            print(f"Request failed: {response.status_code}")

    def _parse_shop_pages(self, timeout=10, verbose=False):
        options = Options()
        for arg in "--headless --disable-gpu --no-sandbox".split():
            options.add_argument(arg)
        driver = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()), options=options
        )
        driver.set_page_load_timeout(45)

        try:
            for i, shop_name in enumerate(self._shop_routes.keys()):
                print(
                    f"Parsing shop page {i+1}/{len(self._shop_routes.keys())}: {shop_name}..."
                )

                brochure_class_pattern = re.compile(r"\bbrochure\b")
                try:
                    driver.get(self._root_url + self._shop_routes[shop_name])

                    # Wait for the brochure container element to load
                    brochure_container = WebDriverWait(driver, timeout).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                "div[id^='shop-'][id$='-brochures-prepend']",
                            )
                        )
                    )

                    if brochure_container:
                        # Wait for brochures to load inside the container
                        WebDriverWait(driver, timeout).until(
                            lambda d: brochure_container.find_elements(
                                By.CSS_SELECTOR, "div.brochure-thumb"
                            )
                        )
                        brochure_html = brochure_container.get_attribute("innerHTML")
                        soup = BeautifulSoup(brochure_html, "html.parser")
                        matching_brochure_divs = soup.find_all(
                            "div", class_=brochure_class_pattern
                        )
                        self._parse_brochures(
                            matching_brochure_divs, shop_name, verbose=verbose
                        )
                    else:
                        print("Failed to find brochure HTML container")
                except TimeoutException:
                    print("Timeout waiting for page to load")
                    continue
        finally:
            driver.quit()

    def _parse_brochures(self, matching_brochure_divs, shop_name, verbose=False):
        if not matching_brochure_divs or len(matching_brochure_divs) == 0:
            print(f"Failed to parse brochures from shop {shop_name}")
            return

        brochure_len = len(self._brochures)
        for i, div in enumerate(matching_brochure_divs):
            if verbose:
                print(
                    f"Parsing brochure {i+1}/{len(matching_brochure_divs)} from shop {shop_name}..."
                )
            brochure = Brochure()

            brochure.set_parsed_time(datetime.now())

            date_element = div.find("small", class_="hidden-sm")
            date_str = date_element.get_text(strip=True) if date_element else None
            if not date_str:
                print("Failed to parse brochure actuality date")
                continue

            date_range_pattern = re.compile(
                r"^\d{2}\.\d{2}\.\d{4} - \d{2}\.\d{2}\.\d{4}$"
            )
            date_pattern = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")

            if re.match(date_range_pattern, date_str):
                start_str, end_str = date_str.split(" - ")
            else:
                match = re.search(date_pattern, date_str)
                if match:
                    start_str = match.group()
                    # Now + 7 days for brochures without specified end date
                    end_str = datetime.strftime(
                        datetime.now() + timedelta(days=7),
                        "%d.%m.%Y",
                    )
                else:
                    print("Failed to parse brochure actuality date")
                    continue

            brochure.set_valid_from(datetime.strptime(start_str, "%d.%m.%Y"))
            # Set to end of day
            brochure.set_valid_to(
                datetime.strptime(end_str, "%d.%m.%Y").replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
            )

            # Skip if outdated
            if not brochure.verify_actuality():
                continue

            title = div.find("div", class_="letak-description").find("strong").text
            if title:
                brochure.set_title(title)
            else:
                print("Failed to parse brochure title")
                continue

            thumbnail = div.find("img")
            if thumbnail and (
                thumbnail_url := thumbnail.get("data-src") or thumbnail.get("src")
            ):
                brochure.set_thumbnail(thumbnail_url)
            else:
                print("Failed to parse thumbnail")
                continue

            brochure.set_shop_name(shop_name)
            self._brochures.append(brochure)
            if verbose:
                print(f"Found actual brochure #{i+1} from {shop_name}!")

        brochure_len_diff = len(self._brochures) - brochure_len
        if brochure_len_diff > 0:
            print(
                f"Parsed shop's {shop_name} page and found {len(self._brochures) - brochure_len} actual brochures!"
            )
        else:
            print(f"Parsed shop's {shop_name} page but didn't find actual brochures.")

    def _brochures_to_dicts(self):
        self._brochure_dicts = [brochure.to_dict() for brochure in self._brochures]

    def brochures_to_json(self, path="brochures.json"):
        self._brochures_to_dicts()
        # UTF-8 and ensure_ascii=False to correctly write German symbols
        with open(path, "w", encoding="utf-8") as json_file:
            json.dump(self._brochure_dicts, json_file, indent=4, ensure_ascii=False)
        print(f"Wrote brochure data to {path}")
