from .main import main
import argparse


def prerun():
    parser = argparse.ArgumentParser(description="SBot")

    parser.add_argument("--headless", type=bool,
                        help="(optional) set headless browser", default=True)
    args = parser.parse_args()


if __name__ == "__main__":
    try:
        prerun()
        main()
    except KeyboardInterrupt:
        pass
