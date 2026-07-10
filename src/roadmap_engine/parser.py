import os
import json
import math

def get_position(node):
    if "positionAbsolute" in node and node["positionAbsolute"]:
        x = node["positionAbsolute"].get("x", 0)
        y = node["positionAbsolute"].get("y", 0)
    elif "position" in node and node["position"]:
        x = node["position"].get("x", 0)
        y = node["position"].get("y", 0)
    else:
        x, y = 0, 0
    
    w = node.get("width") or (node.get("measured", {}).get("width") if node.get("measured") else 0) or 0
    h = node.get("height") or (node.get("measured", {}).get("height") if node.get("measured") else 0) or 0
    
    return {"x": x, "y": y, "w": w, "h": h}

def get_distance(n1, n2):
    p1 = get_position(n1)
    p2 = get_position(n2)
    cx1 = p1["x"] + p1["w"] / 2
    cy1 = p1["y"] + p1["h"] / 2
    cx2 = p2["x"] + p2["w"] / 2
    cy2 = p2["y"] + p2["h"] / 2
    return math.sqrt((cx1 - cx2)**2 + (cy1 - cy2)**2)

def parse_roadmap(roadmap_id, json_path, content_dir, commit_hash):
    with open(json_path, 'r', encoding='utf-8') as f:
        r_data = json.load(f)
    
    nodes = r_data.get("nodes", [])
    edges = r_data.get("edges", [])
    
    topics = [n for n in nodes if n.get("type") == "topic"]
    subtopics = [n for n in nodes if n.get("type") == "subtopic"]
    
    # Read MD files
    md_files = {}
    if os.path.exists(content_dir):
        for f in os.listdir(content_dir):
            if f.endswith('.md'):
                parts = f.split('@')
                if len(parts) > 1:
                    n_id = parts[-1].replace('.md', '')
                    md_files[n_id] = f
    
    missing_desc_count = 0
    import re
    def process_node(n):
        nonlocal missing_desc_count
        desc = None
        resources = []
        if n["id"] in md_files:
            with open(os.path.join(content_dir, md_files[n["id"]]), 'r', encoding='utf-8') as mf:
                content = mf.read()
            del md_files[n["id"]]
            
            # Extract resources
            split_pattern = r'(?i)Visit the following resources.*?:'
            parts = re.split(split_pattern, content)
            if len(parts) > 1:
                desc = parts[0].strip()
                res_text = parts[1].strip()
                for match in re.finditer(r'-\s+\[@([^@]+)@([^\]]+)\]\(([^\)]+)\)', res_text):
                    resources.append({
                        "type": match.group(1).strip(),
                        "title": match.group(2).strip(),
                        "url": match.group(3).strip()
                    })
            else:
                desc = content.strip()
        else:
            missing_desc_count += 1
            
        status = "required"
        legend_data = n.get("data", {}).get("legend", {})
        if legend_data and legend_data.get("label"):
            l = legend_data["label"].lower()
            if "personal recommendation" in l: status = "personal_recommendation"
            elif "alternative" in l: status = "alternative"
            elif "order not strict" in l: status = "order_not_strict"
            else: status = f"unknown: {legend_data['label']}"
            
        pos = get_position(n)
        return {
            "id": n["id"],
            "label": n.get("data", {}).get("label", ""),
            "type": n.get("type"),
            "description": desc,
            "resources": resources,
            "status": status,
            "y": pos["y"],
            "x": pos["x"],
            "rawNode": n
        }
        
    p_topics = [process_node(t) for t in topics]
    p_subtopics = [process_node(st) for st in subtopics]
    orphan_files = list(md_files.keys())
    
    # Sequencing
    p_topics.sort(key=lambda t: t["y"])
    rows = []
    current_row = []
    for t in p_topics:
        if not current_row:
            current_row.append(t)
        else:
            ref_y = current_row[0]["y"]
            if abs(t["y"] - ref_y) <= 80:
                current_row.append(t)
            else:
                rows.append(current_row)
                current_row = [t]
    if current_row:
        rows.append(current_row)
        
    seq_counter = 1
    for r in rows:
        r.sort(key=lambda x: x["x"])
        for i, t in enumerate(r):
            t["sequence_row"] = seq_counter
            t["sequence_col"] = i + 1
        seq_counter += 1
        
    # Subtopic assignment
    adj = {}
    undirected = {}
    for e in edges:
        tgt = e.get("target")
        src = e.get("source")
        if tgt and src:
            adj.setdefault(tgt, []).append(src)
            undirected.setdefault(tgt, []).append(src)
            undirected.setdefault(src, []).append(tgt)
            
    fallback_count = 0
    fallback_logs = []
    
    # Pre-build lookup maps for performance
    topic_id_to_id = {t["id"]: t["id"] for t in p_topics}
    for t in p_topics:
        old_id = t.get("rawNode", {}).get("data", {}).get("oldId")
        if old_id: topic_id_to_id[old_id] = t["id"]
    
    for st in p_subtopics:
        assigned_topic_id = None
        use_fallback = False
        
        found_topic = None
        
        # Start queue with st's id AND oldId
        st_ids = [st["id"]]
        st_old_id = st.get("rawNode", {}).get("data", {}).get("oldId")
        if st_old_id: st_ids.append(st_old_id)
        
        # Fast path check
        for sid in st_ids:
            if sid in adj:
                for p_id in adj[sid]:
                    if p_id in topic_id_to_id:
                        found_topic = topic_id_to_id[p_id]
                        break
                if found_topic: break
        
        if not found_topic:
            q = list(st_ids)
            v_set = set()
            while q:
                curr = q.pop(0)
                if curr in v_set: continue
                v_set.add(curr)
                
                if curr in topic_id_to_id:
                    found_topic = topic_id_to_id[curr]
                    break
                    
                if curr in undirected:
                    for nbr in undirected[curr]:
                        q.append(nbr)
                        
        if found_topic:
            assigned_topic_id = found_topic
        else:
            use_fallback = True
            fallback_count += 1
            min_dist = float('inf')
            nearest_t = None
            for t in p_topics:
                d = get_distance(st["rawNode"], t["rawNode"])
                if d < min_dist:
                    min_dist = d
                    nearest_t = t
            if nearest_t: assigned_topic_id = nearest_t["id"]
            
        st["parent_topic_id"] = assigned_topic_id
        if use_fallback and assigned_topic_id:
            parent_label = next((t["label"] for t in p_topics if t["id"] == assigned_topic_id), "Unknown")
            # compute dist again for log
            dist_log = 0
            for t in p_topics:
                if t["id"] == assigned_topic_id: dist_log = round(get_distance(st["rawNode"], t["rawNode"]))
            fallback_logs.append(f"[{roadmap_id}] Subtopic [{st['label']}] -> Topic [{parent_label}] (Dist: {dist_log})")
            
    # Alternative grouping
    for t in p_topics:
        child_subs = [st for st in p_subtopics if st["parent_topic_id"] == t["id"]]
        for st in child_subs:
            if st["status"] == "alternative":
                st["alternative_group"] = t["id"]
                
    # Remove rawNode
    for n in p_topics + p_subtopics:
        if "rawNode" in n: del n["rawNode"]
        
    return {
        "roadmap_id": roadmap_id,
        "commit_hash": commit_hash,
        "topics": p_topics,
        "subtopics": p_subtopics,
        "metrics": {
            "missing_desc_count": missing_desc_count,
            "orphan_files": len(orphan_files),
            "rows": rows,
            "fallback_count": fallback_count,
            "fallback_logs": fallback_logs,
            "nodes": nodes
        }
    }
