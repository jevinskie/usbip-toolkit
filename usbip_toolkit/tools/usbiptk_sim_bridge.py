#!/usr/bin/env python3

import argparse
import sys

from usbip_toolkit.sim_bridge import USBIPSimBridgeServer
from usbip_toolkit.sim_bridge_aioreactive import USBIPSimBridgeServer_aioreactive


def real_main(args):
    if not args.aioreactive:
        bridge = USBIPSimBridgeServer()
    else:
        bridge = USBIPSimBridgeServer_aioreactive()
    bridge.serve()


def main() -> int:
    parser = argparse.ArgumentParser(description="usbiptk-sim-bridge")
    parser.add_argument("--aioreactive", action="store_true", help="Use aioreactive server")
    args = parser.parse_args()
    real_main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
