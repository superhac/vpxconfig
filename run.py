#!/usr/bin/env python3
"""Start VPinConfig: ./run.py [--host 127.0.0.1] [--port 1111]"""
import argparse

from vpinconfig.server import serve

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--host", default="127.0.0.1", help="interface to listen on (default: localhost only)")
ap.add_argument("--port", type=int, default=1111)
args = ap.parse_args()
serve(args.host, args.port)
