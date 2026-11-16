#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import live_collect
if __name__ == "__main__":
    print(live_collect("estate"))
