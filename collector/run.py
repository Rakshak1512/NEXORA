import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import run_collector

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CYNERA Local Collector")
    parser.add_argument("--scenario", type=str, default=None, help="Trigger specific scenario")
    parser.add_argument("--iterations", type=int, default=0, help="Number of cycles to run (0 for infinite)")
    args = parser.parse_args()

    run_collector(scenario=args.scenario, iterations=args.iterations)
