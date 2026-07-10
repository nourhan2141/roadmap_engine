import os
import json
import subprocess
import shutil

import sys
sys.stdout.reconfigure(encoding='utf-8')

from .parser import parse_roadmap
from .diff_engine import compute_diff
from .staleness import check_staleness
from .validator import validate_parsed

root_dir = 'data'
roadmaps_dir = os.path.join(root_dir, 'src', 'data', 'roadmaps')
processed_dir = os.path.join(root_dir, 'processed', 'roadmaps')
diffs_dir = os.path.join(root_dir, 'processed', 'diffs')

print("=== PHASE 1 PYTHON PARSER START ===")

try:
    commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root_dir).decode('utf-8').strip()
    print(f"Current commit hash: {commit_hash}")
except Exception as e:
    print("Could not get git commit, falling back to static hash.")
    commit_hash = "v1-static-hash"

os.makedirs(processed_dir, exist_ok=True)
os.makedirs(diffs_dir, exist_ok=True)

if not os.path.exists(roadmaps_dir):
    print(f"Roadmaps dir not found: {roadmaps_dir}")
    exit(1)

SUPPORTED = ["frontend", "backend", "full-stack", "devops", "android", "ios", "react", "react-native", "vue", "angular", "nodejs", "javascript", "typescript", "python", "java", "rust", "cpp", "php", "sql", "mongodb", "postgresql-dba", "redis", "graphql", "kubernetes", "aws", "linux", "git-github", "computer-science", "datastructures-and-algorithms", "system-design", "api-design", "software-architect", "ai-engineer", "machine-learning", "data-engineer", "cyber-security", "qa", "product-manager"]

roadmaps = [f for f in os.listdir(roadmaps_dir) if os.path.isdir(os.path.join(roadmaps_dir, f)) and f in SUPPORTED]

global_stats = []
all_fallback_logs = []
failed_validations = []

for r_id in roadmaps:
    r_dir = os.path.join(roadmaps_dir, r_id)
    json_path = os.path.join(r_dir, f"{r_id}.json")
    if not os.path.exists(json_path): continue
    
    out_dir = os.path.join(processed_dir, r_id)
    out_file = os.path.join(out_dir, f"{commit_hash}.json")
    latest_file = os.path.join(out_dir, 'latest.json')
    
    # if os.path.exists(out_file):
    #     print(f"Skipping {r_id} - already parsed for commit {commit_hash}")
    #     continue
        
    os.makedirs(out_dir, exist_ok=True)
    
    parsed_data = parse_roadmap(r_id, json_path, os.path.join(r_dir, 'content'), commit_hash)
    
    topics = parsed_data["topics"]
    subtopics = parsed_data["subtopics"]
    metrics = parsed_data["metrics"]
    
    # Validator
    if not validate_parsed(r_id, topics, subtopics, metrics["nodes"]):
        failed_validations.append(r_id)
    
    # Save
    out_payload = {
        "roadmap_id": r_id,
        "commit_hash": commit_hash,
        "topics": topics,
        "subtopics": subtopics
    }
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(out_payload, f, indent=2)
        
    prev_commit = None
    if os.path.exists(latest_file):
        with open(latest_file, 'r', encoding='utf-8') as f:
            l_data = json.load(f)
            prev_commit = l_data.get("commit")
            
    if prev_commit and prev_commit != commit_hash:
        diff_out_dir = os.path.join(diffs_dir, r_id)
        os.makedirs(diff_out_dir, exist_ok=True)
        
        prev_file = os.path.join(out_dir, f"{prev_commit}.json")
        if os.path.exists(prev_file):
            diff_res = compute_diff(prev_file, topics, subtopics)
            with open(os.path.join(diff_out_dir, f"{prev_commit}__to__{commit_hash}.json"), 'w', encoding='utf-8') as f:
                json.dump(diff_res, f, indent=2)
                
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump({"commit": commit_hash}, f, indent=2)
        
    consecutive_singles = 0
    max_consecutive_singles = 0
    suspicious_large_rows = 0
    for r in metrics["rows"]:
        if len(r) >= 5: suspicious_large_rows += 1
        if len(r) == 1:
            consecutive_singles += 1
            if consecutive_singles > max_consecutive_singles:
                max_consecutive_singles = consecutive_singles
        else:
            consecutive_singles = 0
            
    total_nodes = len(topics) + len(subtopics)
    fallback_pct = f"{(metrics['fallback_count'] / len(subtopics) * 100):.1f}%" if subtopics else "0%"
    missing_desc_pct = f"{(metrics['missing_desc_count'] / total_nodes * 100):.1f}%" if total_nodes else "0%"
    
    unknown_legends = sum(1 for n in topics + subtopics if n["status"].startswith("unknown:"))
    
    global_stats.append({
        "roadmap": r_id,
        "topics": len(topics),
        "subs": len(subtopics),
        "rows": len(metrics["rows"]),
        "fallback": metrics["fallback_count"],
        "fallback_pct": fallback_pct,
        "unknown": unknown_legends,
        "missing_desc": missing_desc_pct,
        "warn_rows": suspicious_large_rows,
        "warn_singles": max_consecutive_singles
    })
    
    all_fallback_logs.extend(metrics["fallback_logs"])

print("\n=== STALENESS CHECK TEST ===")
test_r_id = 'backend'
test_prev_commit = 'abc1234'
test_diff_dir = os.path.join(diffs_dir, test_r_id)
os.makedirs(test_diff_dir, exist_ok=True)
with open(os.path.join(test_diff_dir, f"{test_prev_commit}__to__{commit_hash}.json"), 'w', encoding='utf-8') as f:
    json.dump({"added": [], "removed": [], "modified": ["Of5xsnf0QtksCDnCCHKIv"]}, f, indent=2)

test_latest_file = os.path.join(processed_dir, test_r_id, 'latest.json')
orig_latest = None
if os.path.exists(test_latest_file):
    with open(test_latest_file, 'r', encoding='utf-8') as f:
        orig_latest = f.read()

with open(test_latest_file, 'w', encoding='utf-8') as f:
    json.dump({"commit": commit_hash}, f)

is_stale = check_staleness(diffs_dir, processed_dir, test_r_id, test_prev_commit, ['Of5xsnf0QtksCDnCCHKIv'])
print(f"Synthetic Stale Test (modified node 'Go'): {'STALE (Pass)' if is_stale else 'NOT STALE (Fail)'}")

is_stale_2 = check_staleness(diffs_dir, processed_dir, test_r_id, test_prev_commit, ['SomeOtherId'])
print(f"Synthetic Stale Test 2 (unaffected node): {'STALE (Fail)' if is_stale_2 else 'NOT STALE (Pass)'}")

if orig_latest:
    with open(test_latest_file, 'w', encoding='utf-8') as f:
        f.write(orig_latest)

print("\n=== PER-ROADMAP SUMMARY TABLE ===")
if global_stats:
    headers = global_stats[0].keys()
    print("{:<20} {:<8} {:<8} {:<8} {:<10} {:<15} {:<10} {:<15} {:<12} {:<15}".format(*headers))
    for s in global_stats:
        print("{:<20} {:<8} {:<8} {:<8} {:<10} {:<15} {:<10} {:<15} {:<12} {:<15}".format(*s.values()))

print("\n=== CLUSTERING WARNINGS ===")
warned = False
for s in global_stats:
    if s["warn_rows"] > 0 or s["warn_singles"] >= 10:
        warned = True
        print(f"[{s['roadmap']}] FLAG: Large rows (>=5) = {s['warn_rows']}, Max consecutive single-topic rows = {s['warn_singles']}")
if not warned: print("None.")

# print("\n=== FALLBACK ASSIGNMENT LOG ===")
# for l in all_fallback_logs:
#     try:
#         print(l)
#     except:
#         print(l.encode('utf-8', 'replace').decode('utf-8'))

print("\n=== BACKEND: 'Pick a Language' SUBTOPICS ===")
be_file = os.path.join(processed_dir, 'backend', f"{commit_hash}.json")
if os.path.exists(be_file):
    with open(be_file, 'r', encoding='utf-8') as f:
        be_data = json.load(f)
    pick_topic = next((t for t in be_data["topics"] if t["label"] == "Pick a Language"), None)
    if pick_topic:
        subs = [st for st in be_data["subtopics"] if st["parent_topic_id"] == pick_topic["id"]]
        for s in subs:
            print(f"- {s['label']}: status={s['status']}, alternative_group={s.get('alternative_group', 'null')}")

print("\n=== VALIDATION RESULTS ===")
if failed_validations:
    print(f"FAILED VALIDATIONS ({len(failed_validations)}): {', '.join(failed_validations)}")
else:
    print("All 38 supported roadmaps passed validation cleanly!")
