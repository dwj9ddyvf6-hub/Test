#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import compile_state
if __name__ == "__main__":
    import json; s = compile_state(); print(s["regime"], s.get("composite_percentile"))
