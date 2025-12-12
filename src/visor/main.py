from .ui.app import VisorApp
import sys


def main():
    app = VisorApp(sys.argv)
    return app.run()




if __name__ == "__main__":
    raise SystemExit(main())