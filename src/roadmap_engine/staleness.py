import json
import os

def check_staleness(diffs_dir, processed_dir, roadmap_id, version_generated_against, node_ids_used):
    latest_file = os.path.join(processed_dir, roadmap_id, 'latest.json')
    if not os.path.exists(latest_file):
        return {"stale": False, "changed_nodes": []}
        
    with open(latest_file, 'r', encoding='utf-8') as f:
        latest = json.load(f)
        
    if latest.get("commit") == version_generated_against:
        return {"stale": False, "changed_nodes": []}
        
    diff_file = os.path.join(diffs_dir, roadmap_id, f"{version_generated_against}__to__{latest.get('commit')}.json")
    if os.path.exists(diff_file):
        with open(diff_file, 'r', encoding='utf-8') as f:
            diff = json.load(f)
        affected = set(diff.get("added", []) + diff.get("removed", []) + diff.get("modified", []))
        
        changed_nodes = []
        for n_id in node_ids_used:
            if n_id in affected:
                changed_nodes.append(n_id)
        
        if changed_nodes:
            return {"stale": True, "changed_nodes": changed_nodes}
                
    return {"stale": False, "changed_nodes": []}
