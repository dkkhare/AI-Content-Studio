from __future__ import annotations

import sys
import traceback

from desktop.app import AIContentStudio


def main():

    try:

        app = AIContentStudio()

        return app.run()


    except Exception as error:

        print(
            "Application startup failed:"
        )

        print(
            error
        )

        traceback.print_exc()

        return 1



if __name__ == "__main__":

    sys.exit(
        main()
    )