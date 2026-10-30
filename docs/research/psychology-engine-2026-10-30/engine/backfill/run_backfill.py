#!/usr/bin/env python3
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import backfill_all
if __name__ == "__main__":
    import json; print(json.dumps(backfill_all(), indent=1, default=str))
