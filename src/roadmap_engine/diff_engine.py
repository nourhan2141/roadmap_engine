import json
import os

def compute_diff(prev_file_path, current_topics, current_subtopics):
    with open(prev_file_path, 'r', encoding='utf-8') as f:
        prev_data = json.load(f)
        
    p_map = {n["id"]: n for n in prev_data.get("topics", []) + prev_data.get("subtopics", [])}
    c_map = {n["id"]: n for n in current_topics + current_subtopics}
    
    added = []
    removed = []
    modified = []
    
    for n_id, c_node in c_map.items():
        if n_id not in p_map:
            added.append(n_id)
        else:
            # simple JSON check
            if json.dumps(c_node, sort_keys=True) != json.dumps(p_map[n_id], sort_keys=True):
                modified.append(n_id)
                
    for n_id in p_map:
        if n_id not in c_map:
            removed.append(n_id)
            
    return {"added": added, "removed": removed, "modified": modified}
