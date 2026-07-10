import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from roadmap_engine.engine import generate_plan, load_roadmap
from roadmap_engine.llm import generate_narration

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=== SCENARIO 1: Large Budget (50 weeks, 10.0 hrs/wk) ===")
    data, _ = load_roadmap("backend")
    go_id = next(st["id"] for st in data["subtopics"] if st.get("label") == "Go")
    
    plan1 = generate_plan("backend", known_node_ids=[go_id], duration_weeks=50, hours_per_week=10.0)
    merged_plan1 = generate_narration(plan1, max_retries=2)
    
    # Dump just the narrations to console to avoid huge spam, or full JSON?
    # User said: "full JSON, not a description" for both.
    open("outputs/scenario1_output.json", "w", encoding="utf-8").write(json.dumps(merged_plan1, indent=2))
    print(json.dumps(merged_plan1, indent=2))
    
    print("\n\n=== SCENARIO 2: Small Budget (1 week, 2.0 hrs/wk) ===")
    plan2 = generate_plan("backend", known_node_ids=[], duration_weeks=1, hours_per_week=2.0)
    merged_plan2 = generate_narration(plan2, max_retries=2)
    
    open("outputs/scenario2_output.json", "w", encoding="utf-8").write(json.dumps(merged_plan2, indent=2))
    print(json.dumps(merged_plan2, indent=2))

if __name__ == "__main__":
    main()
