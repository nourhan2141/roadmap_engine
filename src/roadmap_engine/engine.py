import os
import json


def load_roadmap(roadmap_id):
    processed_dir = os.path.join('data', 'processed', 'roadmaps', roadmap_id)
    latest_file = os.path.join(processed_dir, 'latest.json')
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        commit_hash = json.load(f)["commit"]
        
    data_file = os.path.join(processed_dir, f"{commit_hash}.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return data, commit_hash

def generate_plan(roadmap_id, known_node_ids, duration_weeks, hours_per_week):
    data, commit_hash = load_roadmap(roadmap_id)
    
    topics = data["topics"]
    subtopics = data["subtopics"]
    
    # 2. Derive Choice Groups
    choice_groups = {} # parent_topic_id -> list of subtopics
    standalone_subtopics = []
    
    for st in subtopics:
        if st.get("status") in ["alternative", "personal_recommendation"]:
            pid = st.get("parent_topic_id")
            if not pid: continue
            if pid not in choice_groups:
                choice_groups[pid] = []
            choice_groups[pid].append(st)
        else:
            standalone_subtopics.append(st)
            
    # 3. Apply Known Topics (Pruning)
    known_set = set(known_node_ids)
    
    # Prune topics
    final_topics = []
    for t in topics:
        if t["id"] in known_set:
            continue
        final_topics.append(t)
        
    final_topic_ids = {t["id"] for t in final_topics}
    
    # Prune choice groups
    final_choice_groups = {}
    for pid, group in choice_groups.items():
        if pid not in final_topic_ids: continue # Parent was pruned
        
        # Check if any member of the choice group is known
        group_satisfied = any(st["id"] in known_set for st in group)
        if not group_satisfied:
            final_choice_groups[pid] = group
            
    # Prune standalone subtopics
    final_standalones = []
    for st in standalone_subtopics:
        if st.get("parent_topic_id") not in final_topic_ids: continue # Parent was pruned
        if st["id"] in known_set: continue # Specific standalone subtopic is known
        final_standalones.append(st)
        
    # 4. Effort Estimation and 5. Sequence
    final_topics.sort(key=lambda t: (t.get("sequence_row", 0), t.get("sequence_col", 0)))
    
    sequenced_items = []
    
    def format_item(node_type, node, is_choice=False, options=None, hours=0.0):
        res = {
            "type": node_type,
            "id": node.get("id") if not is_choice else f"choice_group_{node.get('parent_topic_id', '')}",
            "title": node.get("label", ""),
            "description": node.get("description", ""),
            "resources": node.get("resources", []),
            "is_choice": is_choice,
            "hours": hours
        }
        if is_choice and options:
            res["options"] = [
                {
                    "id": opt.get("id"),
                    "title": opt.get("label", ""),
                    "description": opt.get("description", ""),
                    "resources": opt.get("resources", []),
                    "status": opt.get("status")
                } for opt in options
            ]
            res["title"] = "Select One Option"
        return res
        
    for t in final_topics:
        # Topic overview: 0.5 hours
        t_item = format_item("topic_overview", t, is_choice=False, hours=0.5)
        sequenced_items.append(t_item)
        
        t_standalones = [st for st in final_standalones if st.get("parent_topic_id") == t["id"]]
        for st in t_standalones:
            sequenced_items.append(format_item("subtopic", st, is_choice=False, hours=1.5))
            
        if t["id"] in final_choice_groups:
            cg = final_choice_groups[t["id"]]
            cg_node = {"parent_topic_id": t["id"]}
            sequenced_items.append(format_item("choice_group", cg_node, is_choice=True, options=cg, hours=1.5))

    # 6. Budget Fit
    total_budget_hours = duration_weeks * hours_per_week
    total_accumulated_hours = 0.0
    
    weeks = []
    stretch_goals = []
    node_ids_used = []
    
    current_week_num = 1
    current_week_items = []
    current_week_hours = 0.0
    
    for item in sequenced_items:
        if item["type"] == "choice_group":
            for opt in item.get("options", []):
                node_ids_used.append(opt["id"])
        else:
            node_ids_used.append(item["id"])
            
        if total_accumulated_hours >= total_budget_hours:
            stretch_goals.append(item)
        else:
            current_week_items.append(item)
            current_week_hours += item["hours"]
            total_accumulated_hours += item["hours"]
            
            if current_week_hours >= hours_per_week and total_accumulated_hours < total_budget_hours:
                weeks.append({
                    "week_number": current_week_num,
                    "items": current_week_items
                })
                current_week_num += 1
                current_week_items = []
                current_week_hours = 0.0
                
    if current_week_items:
        weeks.append({
            "week_number": current_week_num,
            "items": current_week_items
        })
        
    # 7. Emit Payload
    return {
        "roadmap_id": roadmap_id,
        "version_generated_against": commit_hash,
        "weeks": weeks,
        "stretch_goals": stretch_goals,
        "node_ids_used": node_ids_used
    }

if __name__ == "__main__":
    pass
