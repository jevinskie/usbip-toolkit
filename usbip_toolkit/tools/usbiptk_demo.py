#!/usr/bin/env python3

import argparse
import sys

from usbip_toolkit.demo import DemoServer


def real_main(args):
    demo = DemoServer()
    demo.serve()


def main() -> int:
    parser = argparse.ArgumentParser(description="usbiptk-demo")
    args = parser.parse_args()
    real_main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
