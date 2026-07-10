import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== 1. GET /roadmaps ===")
    r1 = requests.get(f"{BASE_URL}/roadmaps")
    print(r1.status_code)
    print(json.dumps(r1.json()[:3], indent=2))
    print("... (truncated for length) ...\n")

    print("=== 2. GET /roadmaps/backend/topics ===")
    r2 = requests.get(f"{BASE_URL}/roadmaps/backend/topics")
    print(r2.status_code)
    print(json.dumps(r2.json()[:10], indent=2))
    print("\n")

    print("=== 3. POST /generate (Happy path) ===")
    payload3 = {
        "roadmap_id": "backend",
        "known_node_ids": ["BdXbcz4-ar3XOX0wIKzBp"],
        "duration_weeks": 6,
        "hours_per_week": 10.0
    }
    r3 = requests.post(f"{BASE_URL}/generate", json=payload3)
    print(r3.status_code)
    data3 = r3.json()
    print("Top-level keys:", list(data3.keys()))
    if "weeks" in data3 and len(data3["weeks"]) > 0:
        print("Week 1:")
        print(json.dumps(data3["weeks"][0], indent=2))
    print("\n")

    print("=== 4. POST /generate (Invalid roadmap) ===")
    payload4 = {
        "roadmap_id": "invalid-roadmap-name",
        "known_node_ids": [],
        "duration_weeks": 6,
        "hours_per_week": 10.0
    }
    r4 = requests.post(f"{BASE_URL}/generate", json=payload4)
    print(r4.status_code)
    print(r4.json())
    print("\n")

    print("=== 5. POST /generate (Invalid node ID) ===")
    payload5 = {
        "roadmap_id": "backend",
        "known_node_ids": ["some-frontend-id"],
        "duration_weeks": 6,
        "hours_per_week": 10.0
    }
    r5 = requests.post(f"{BASE_URL}/generate", json=payload5)
    print(r5.status_code)
    print(r5.json())
    print("\n")

    print("=== 6. POST /check-staleness ===")
    payload6 = {
        "roadmap_id": "backend",
        "version_generated_against": data3.get("version_generated_against", ""),
        "node_ids_used": data3.get("node_ids_used", [])
    }
    r6 = requests.post(f"{BASE_URL}/check-staleness", json=payload6)
    print(r6.status_code)
    print(r6.json())
    print("\n")

if __name__ == "__main__":
    run_tests()
