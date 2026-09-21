#!/usr/bin/env python3
"""Start VPinConfig: ./run.py [--host 127.0.0.1] [--port 1111]   (also the entry point of the built executable)"""
import argparse

from vpinconfig import __version__
from vpinconfig.server import serve

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--host", default="127.0.0.1", help="interface to listen on (default: localhost only)")
ap.add_argument("--port", type=int, default=1111)
ap.add_argument("--version", action="version", version=f"VPinConfig {__version__}")
args = ap.parse_args()
serve(args.host, args.port)
