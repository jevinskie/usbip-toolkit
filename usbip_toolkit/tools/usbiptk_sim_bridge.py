#!/usr/bin/env python3

import argparse
import sys

from usbip_toolkit.sim_bridge import USBIPSimBridgeServer


def real_main(args):
    bridge = USBIPSimBridgeServer()
    bridge.serve()


def main() -> int:
    parser = argparse.ArgumentParser(description="usbiptk-sim-bridge")
    args = parser.parse_args()
    real_main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
