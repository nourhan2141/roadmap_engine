from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os

from . import schemas
from . import engine
from . import llm
from . import staleness

SUPPORTED_ROADMAPS = ["frontend", "backend", "full-stack", "devops", "android", "ios", "react", "react-native", "vue", "angular", "nodejs", "javascript", "typescript", "python", "java", "rust", "cpp", "php", "sql", "mongodb", "postgresql-dba", "redis", "graphql", "kubernetes", "aws", "linux", "git-github", "computer-science", "datastructures-and-algorithms", "system-design", "api-design", "software-architect", "ai-engineer", "machine-learning", "data-engineer", "cyber-security", "qa", "product-manager"]

app = FastAPI()

# Note: Permissive CORS configuration for frontend development.
# This should be tightened before any real public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/roadmaps")
def get_roadmaps():
    roadmaps_info = []
    base_dir = os.path.join('data', 'processed', 'roadmaps')
    for r_id in SUPPORTED_ROADMAPS:
        latest_file = os.path.join(base_dir, r_id, 'latest.json')
        if not os.path.exists(latest_file):
            continue
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                commit_hash = json.load(f)["commit"]
            content_file = os.path.join(base_dir, r_id, f"{commit_hash}.json")
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            roadmaps_info.append({"id": r_id, "title": data.get("title", r_id)})
        except Exception:
            continue
    return roadmaps_info

@app.get("/roadmaps/{roadmap_id}/topics")
def get_roadmap_topics(roadmap_id: str):
    if roadmap_id not in SUPPORTED_ROADMAPS:
        raise HTTPException(status_code=400, detail=f"Roadmap '{roadmap_id}' is not supported.")
    
    try:
        data, _ = engine.load_roadmap(roadmap_id)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Roadmap '{roadmap_id}' could not be loaded.")
        
    flattened = []
    for topic in data.get("topics", []):
        flattened.append({
            "id": topic["id"],
            "title": topic.get("title") or topic.get("label", ""),
            "type": "topic",
            "parent_topic_id": None,
            "status": topic.get("status")
        })
    for subtopic in data.get("subtopics", []):
        flattened.append({
            "id": subtopic["id"],
            "title": subtopic.get("title") or subtopic.get("label", ""),
            "type": "subtopic",
            "parent_topic_id": subtopic.get("parent_topic_id"),
            "status": subtopic.get("status")
        })
        
    return flattened

@app.post("/generate")
def generate(req: schemas.GenerateRequest):
    if req.roadmap_id not in SUPPORTED_ROADMAPS:
        raise HTTPException(status_code=400, detail=f"Roadmap '{req.roadmap_id}' is not supported.")

    try:
        data, _ = engine.load_roadmap(req.roadmap_id)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Roadmap '{req.roadmap_id}' could not be loaded.")

    valid_ids = {t["id"] for t in data.get("topics", [])}
    valid_ids.update(st["id"] for st in data.get("subtopics", []))
    
    invalid_ids = [nid for nid in req.known_node_ids if nid not in valid_ids]
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"The following known_node_ids do not exist in roadmap '{req.roadmap_id}': {invalid_ids}"
        )

    try:
        plan_payload = engine.generate_plan(req.roadmap_id, req.known_node_ids, req.duration_weeks, req.hours_per_week)
        merged_payload = llm.generate_narration(plan_payload)
        return merged_payload
    except Exception as e:
        print(f"Internal error during plan generation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during plan generation.")

@app.post("/check-staleness")
def check_staleness(req: schemas.StalenessRequest):
    if req.roadmap_id not in SUPPORTED_ROADMAPS:
        raise HTTPException(status_code=400, detail=f"Roadmap '{req.roadmap_id}' is not supported.")
        
    try:
        diffs_dir = os.path.join("data", "processed", "diffs")
        processed_dir = os.path.join("data", "processed", "roadmaps")
        result = staleness.check_staleness(diffs_dir, processed_dir, req.roadmap_id, req.version_generated_against, req.node_ids_used)
        return result
    except Exception as e:
        print(f"Internal error during staleness check: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during staleness check.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
