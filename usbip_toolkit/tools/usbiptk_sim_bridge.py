#!/usr/bin/env python3

import argparse
import sys

from usbip_toolkit.sim_bridge import USBIPSimBridgeServer
from usbip_toolkit.sim_bridge_aioreactive import USBIPSimBridgeServer_aioreactive
from usbip_toolkit.sim_bridge_classic import USBIPSimBridgeServer_classic
from usbip_toolkit.sim_bridge_rx import USBIPSimBridgeServer_rx


def real_main(args):
    if args.aioreactive:
        bridge = USBIPSimBridgeServer_aioreactive()
    elif args.reactivex:
        bridge = USBIPSimBridgeServer_rx()
    elif args.classic:
        bridge = USBIPSimBridgeServer_classic()
    else:
        bridge = USBIPSimBridgeServer()
    bridge.serve()


def main() -> int:
    parser = argparse.ArgumentParser(description="usbiptk-sim-bridge")
    parser.add_argument("--aioreactive", action="store_true", help="Use aioreactive server")
    parser.add_argument("--reactivex", action="store_true", help="Use ReactiveX server")
    parser.add_argument("--classic", action="store_true", help="Use classic server")
    args = parser.parse_args()
    real_main(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
