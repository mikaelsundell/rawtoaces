# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""One conversion per process, so native calls cannot hold the UI's GIL."""

import json
import sys

from .jobs import ConversionOptions, convert


def main():
    try:
        job = json.load(sys.stdin)
        output = convert(job["filename"], ConversionOptions(job["options"]))
        print("Saved: " + str(output), flush=True)
        return 0
    except Exception as error:
        print("Conversion failed: " + str(error), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
