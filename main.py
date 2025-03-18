from BrochureParser import BrochureParser


def main():
    parser = BrochureParser()
    parser.parse()
    parser.brochures_to_json()


if __name__ == "__main__":
    main()
