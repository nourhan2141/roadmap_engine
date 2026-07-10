import requests
import json
import os

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    os.makedirs('outputs', exist_ok=True)
    
    # Re-run Test 6: Self-comparison
    payload6 = {
        "roadmap_id": "backend",
        "version_generated_against": "70ecc31a04739d547d6ebf37213249b275f7565b",
        "node_ids_used": ["BdXbcz4-ar3XOX0wIKzBp"]
    }
    r6 = requests.post(f"{BASE_URL}/check-staleness", json=payload6)
    with open('outputs/test6_staleness.txt', 'w', encoding='utf-8') as f:
        f.write(r6.text)

    # Test Stale Path
    # Create fake diff file
    diff_dir = os.path.join("data", "processed", "diffs", "backend")
    os.makedirs(diff_dir, exist_ok=True)
    
    fake_diff_path = os.path.join(diff_dir, "fake_hash__to__70ecc31a04739d547d6ebf37213249b275f7565b.json")
    with open(fake_diff_path, "w", encoding="utf-8") as f:
        json.dump({"modified": ["BdXbcz4-ar3XOX0wIKzBp"]}, f)
        
    payload_stale = {
        "roadmap_id": "backend",
        "version_generated_against": "fake_hash",
        "node_ids_used": ["BdXbcz4-ar3XOX0wIKzBp"]
    }
    r_stale = requests.post(f"{BASE_URL}/check-staleness", json=payload_stale)
    with open('outputs/test_stale.txt', 'w', encoding='utf-8') as f:
        f.write(r_stale.text)

if __name__ == "__main__":
    run_tests()
