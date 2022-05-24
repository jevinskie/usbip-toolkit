#!/usr/bin/env python3

import argparse
import sys


def real_main(args):
    pass


def main() -> int:
    parser = argparse.ArgumentParser(description="usbiptk-demo")
    args = parser.parse_args()
    real_main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
