from datetime import datetime


class Brochure:
    DEFAULT_DATE = datetime(1970, 1, 1).date()
    DEFAULT_DATETIME = datetime(1970, 1, 1, 0, 0, 0)

    def __init__(
        self,
        title="",
        thumbnail="",
        shop_name="",
        valid_from=DEFAULT_DATE,
        valid_to=DEFAULT_DATE,
        parsed_time=DEFAULT_DATETIME,
    ) -> None:
        self._title = title
        self._thumbnail = thumbnail
        self._shop_name = shop_name
        self._valid_from = valid_from
        self._valid_to = valid_to
        self._parsed_time = parsed_time  # "%Y-%m-%d %H:%M:%S"

    def verify_actuality(self):
        return self._valid_from <= self._parsed_time <= self._valid_to

    # For checking if all values are non-default
    def is_populated(self):
        return (
            self._title != ""
            and self._thumbnail != ""
            and self._shop_name != ""
            and self._valid_from != self.DEFAULT_DATE
            and self._valid_to != self.DEFAULT_DATE
            and self._parsed_time != self.DEFAULT_DATETIME
        )

    def to_dict(self):
        if self.is_populated():
            return {
                "title": self._title,
                "thumbnail": self._thumbnail,
                "shop_name": self._shop_name,
                "valid_from": self._valid_from.strftime("%Y-%m-%d"),
                "valid_to": self._valid_to.strftime("%Y-%m-%d"),
                "parsed_time": self._parsed_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        else:
            print("Brochure not converted to dict: default value detected")

    def set_title(self, value):
        self._title = value

    def set_thumbnail(self, value):
        self._thumbnail = value

    def set_shop_name(self, value):
        self._shop_name = value

    def set_valid_from(self, value):
        self._valid_from = value

    def set_valid_to(self, value):
        self._valid_to = value

    def set_parsed_time(self, value):
        self._parsed_time = value

    def get_title(self):
        return self._title

    def get_thumbnail(self):
        return self._thumbnail

    def get_shop_name(self):
        return self._shop_name

    def get_valid_from(self):
        return self._valid_from

    def get_valid_to(self):
        return self._valid_to

    def get_parsed_time(self):
        return self._parsed_time
