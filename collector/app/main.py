import time
import argparse
import sys
from .config import config
from .collector import LocalCollectorEngine
from .heartbeat import CollectorHeartbeat

def run_collector(scenario: str = None, iterations: int = 0):
    print("=" * 70)
    print("CYNERA — INDEPENDENT LOCAL COLLECTOR (Tier 1 Perimeter)")
    print(f"Collector ID:   {config.COLLECTOR_ID}")
    print(f"Tenant ID:      {config.TENANT_ID}")
    print(f"Backend Target: {config.BACKEND_URL}")
    print(f"Queue Storage:  {config.LOCAL_QUEUE_PATH}")
    print(f"Mode:           {'Live Telemetry (psutil)' if not scenario else f'Scenario: {scenario}'}")
    print("Security:       Local Redaction ACTIVE | Strict Allowlist ACTIVE")
    print("=" * 70)

    engine = LocalCollectorEngine()
    if scenario:
        engine.set_scenario(scenario)

    heartbeat = CollectorHeartbeat(engine.queue)

    count = 0
    last_hb = 0

    try:
        while True:
            # 1. Telemetry cycle
            result = engine.process_cycle()
            count += 1
            print(f"[{time.strftime('%H:%M:%S')}] Cycle #{count} | Payload: {result['payload_id']} | "
                  f"CPU: {result['outgoing_payload']['cpu_utilization_pct']}% | "
                  f"Queue Backlog: {result['queue_depth']} | Health: {result['outgoing_payload']['health_state']}")

            # 2. Heartbeat cycle
            now = time.time()
            if now - last_hb > config.HEARTBEAT_INTERVAL_SECONDS:
                hb_ok = heartbeat.send("online")
                last_hb = now
                if hb_ok:
                    print(f"[{time.strftime('%H:%M:%S')}] Heartbeat acknowledged by SaaS backend.")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Heartbeat queued locally (backend unreachable).")

            if iterations > 0 and count >= iterations:
                print(f"[Collector] Completed {iterations} requested test cycles.")
                break

            time.sleep(config.COLLECTION_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[Collector] Graceful shutdown initiated. Heartbeat status updating...")
        heartbeat.send("offline")
        print("[Collector] Local queue safely persisted on disk. Exiting.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CYNERA Local Collector")
    parser.add_argument("--scenario", type=str, default=None, help="Trigger specific scenario")
    parser.add_argument("--iterations", type=int, default=0, help="Number of cycles to run (0 for infinite)")
    args = parser.parse_args()

    run_collector(scenario=args.scenario, iterations=args.iterations)

