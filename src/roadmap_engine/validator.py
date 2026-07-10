def validate_parsed(roadmap_id, topics, subtopics, raw_nodes):
    errors = []
    
    # 1. Duplicate ID check
    id_counts = {}
    for n in raw_nodes:
        if n.get("type") in ("topic", "subtopic"):
            n_id = n.get("id")
            id_counts[n_id] = id_counts.get(n_id, 0) + 1
            if id_counts[n_id] > 1:
                errors.append(f"Duplicate node ID found: {n_id}")
                
    # 2. Every subtopic has a resolved parent topic
    missing_parents = [st["id"] for st in subtopics if not st.get("parent_topic_id")]
    if missing_parents:
        errors.append(f"{len(missing_parents)} subtopics missing parent_topic_id")
        
    # 3. Every node referenced anywhere has a non-empty id and title
    empty_ids = [n for n in topics + subtopics if not n.get("id") or not str(n.get("label")).strip()]
    if empty_ids:
        errors.append(f"{len(empty_ids)} nodes have empty id or label")
        
    for err in errors:
        print(f"ERROR [{roadmap_id}]: {err}")
        
    return len(errors) == 0
