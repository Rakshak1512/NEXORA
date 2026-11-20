import sys
import os

collector_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if collector_root not in sys.path:
    sys.path.insert(0, collector_root)

