from BrochureParser import BrochureParser


def main():
    parser = BrochureParser()
    parser.parse()
    # parser.parse(verbose=True)
    parser.brochures_to_json()


if __name__ == "__main__":
    main()
