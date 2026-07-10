# Project Files

## File: .python-version
```python-version
3.12
```

## File: Dockerfile
```text
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the project into the image
COPY . /app

# Sync the project into a new environment, using the frozen lockfile
RUN uv sync --frozen --no-dev

# Ensure the installed binary is on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 7860, default for Hugging Face Spaces
EXPOSE 7860

# Run the FastAPI application
CMD ["uvicorn", "src.roadmap_engine.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

## File: merge_files.ps1
```ps1
$outputFile = "merged_project.md"
if (Test-Path $outputFile) { Remove-Item $outputFile }

$excludeDirs = @('\.git\\', '\.venv\\', '\\__pycache__\\', '\\data\\', '\\outputs\\', '\.pytest_cache\\', '\.ruff_cache\\')
$excludeFiles = @('.env', 'uv.lock', 'merged_project.md', '*.json', '*.pyc', '*.png', '*.jpg', '*.pdf')

Set-Content -Path $outputFile -Value "# Project Files`n"

Get-ChildItem -Path . -Recurse -File | Where-Object {
    $path = $_.FullName
    $name = $_.Name
    $exclude = $false
    
    foreach ($dir in $excludeDirs) {
        if ($path -match $dir) { $exclude = $true; break }
    }
    
    foreach ($file in $excludeFiles) {
        if ($name -like $file) { $exclude = $true; break }
    }
    
    return -not $exclude
} | ForEach-Object {
    $relativePath = $_.FullName.Substring((Get-Location).Path.Length + 1).Replace('\', '/')
    $ext = $_.Extension.TrimStart('.')
    if (-not $ext) { $ext = "text" }
    if ($ext -eq "py") { $ext = "python" }
    
    if ($_.Length -gt 500KB) { return }

    Add-Content -Path $outputFile -Value "## File: $relativePath`n``````$ext"
    try {
        Get-Content -Path $_.FullName -ErrorAction Stop | Add-Content -Path $outputFile
    } catch {
        Add-Content -Path $outputFile -Value "<binary or unreadable file>"
    }
    Add-Content -Path $outputFile -Value "```````n"
}
```

## File: pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "roadmap_engine"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "chromadb>=1.5.9",
    "fastapi>=0.139.0",
    "groq>=1.5.0",
    "pydantic-settings>=2.14.2",
    "requests>=2.34.2",
    "sentence-transformers>=5.6.0",
    "streamlit>=1.59.1",
    "uvicorn>=0.51.0",
]
```

## File: README.md
```md
---
title: Roadmap Engine API
emoji: 🗺️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 🗺️ Roadmap Engine API

The Roadmap Engine is a backend service powered by **FastAPI** that provides comprehensive learning roadmaps and personalized learning plans for various technical domains (Frontend, Backend, DevOps, AI/ML, and more).

## 🚀 Features

- **Pre-defined Roadmaps**: Access structured learning paths for dozens of roles and technologies.
- **Topic Granularity**: Fetch detailed topics and subtopics for any given roadmap.
- **AI-Powered Plan Generation**: Generate personalized learning narratives and schedules using LLMs (Groq) based on user's known topics, time availability, and chosen roadmap.
- **Staleness Tracking**: Track when underlying roadmap data has been updated and whether generated plans need refreshing.

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Dependency Management**: [uv](https://github.com/astral-sh/uv)
- **AI Integration**: Groq API
- **Deployment**: Docker (configured for Hugging Face Spaces)

## 📡 API Endpoints

Once running, you can interact with the API or view the interactive Swagger documentation at the root URL (which automatically redirects to `/docs`).

- `GET /roadmaps`: Retrieve a list of all supported roadmaps.
- `GET /roadmaps/{roadmap_id}/topics`: Retrieve a flattened structure of all topics and subtopics for a specific roadmap.
- `POST /generate`: Generate a personalized learning plan. Requires a payload with `roadmap_id`, `known_node_ids`, `duration_weeks`, and `hours_per_week`.
- `POST /check-staleness`: Check if a previously generated plan is outdated relative to the latest roadmap definitions.

## 💻 Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd roadmap
   ```

2. **Install dependencies (using `uv`)**:
   ```bash
   uv sync
   ```

3. **Set up Environment Variables**:
   Ensure you have a `.env` file at the root containing your API keys (e.g., `GROQ_API_KEY`).

4. **Run the FastAPI server**:
   ```bash
   uv run uvicorn src.roadmap_engine.main:app --reload
   ```

5. **View the API Docs**:
   Open your browser and navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## ☁️ Hugging Face Spaces Deployment

This repository is fully configured for deployment on **Hugging Face Spaces**. It utilizes the `docker` SDK to seamlessly serve the FastAPI application. 

When pushed to a Space, Hugging Face will automatically:
1. Build the Docker image defined in `Dockerfile`.
2. Install dependencies using `uv`.
3. Serve the application on port `7860`.

When you open the **App** tab on your Hugging Face Space, you will automatically be redirected to the interactive Swagger UI (`/docs`).
```

## File: scripts/dump_narrations.py
```python
from roadmap_engine import engine, llm
import json

def extract():
    with open('outputs/scenario1_output.json', encoding='utf-8') as f:
        d = json.load(f)
    
    with open('outputs/narration_dump_with_topics.txt', 'w', encoding='utf-8') as out:
        for w in d.get("weeks", []):
            out.write(f"WEEK {w['week_number']}\n")
            
            # Gather all titles
            titles = []
            for item in w.get("items", []):
                if item.get("type") == "choice_group":
                    for opt in item.get("options", []):
                        titles.append(opt.get("title"))
                else:
                    titles.append(item.get("title"))
                    
            out.write(f"Topics Provided:\n  • " + "\n  • ".join(titles) + "\n\n")
            out.write(f"Generated Narration:\n  Intro: {w.get('intro', 'MISSING')}\n")
            out.write(f"  Milestone: {w.get('milestone', 'MISSING')}\n")
            out.write("-" * 80 + "\n\n")

if __name__ == '__main__':
    extract()
```

## File: scripts/print_table.py
```python
import os, json
r_dir = r"data\src\data\roadmaps"
processed_dir = r"data\processed\roadmaps"
SUPPORTED = ["frontend", "backend", "full-stack", "devops", "android", "ios", "react", "react-native", "vue", "angular", "nodejs", "javascript", "typescript", "python", "java", "rust", "cpp", "php", "sql", "mongodb", "postgresql-dba", "redis", "graphql", "kubernetes", "aws", "linux", "git-github", "computer-science", "datastructures-and-algorithms", "system-design", "api-design", "software-architect", "ai-engineer", "machine-learning", "data-engineer", "cyber-security", "qa", "product-manager"]

stats = []
for rd in SUPPORTED:
    j_file = os.path.join(processed_dir, rd, '70ecc31a04739d547d6ebf37213249b275f7565b.json')
    if not os.path.exists(j_file): continue
    with open(j_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    topics = data["topics"]
    subs = data["subtopics"]
    
    # We need fallback counts which are not in the json directly, but we can infer them or just count missing parents? 
    # Wait, fallbacks aren't saved in the JSON. I can't easily reproduce it without running the parser logic.
    
    pass
```

## File: src/roadmap_engine/config.py
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str = "placeholder_key"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
```

## File: src/roadmap_engine/diff_engine.py
```python
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
```

## File: src/roadmap_engine/embedder.py
```python
import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

SUPPORTED = ["frontend", "backend", "full-stack", "devops", "android", "ios", "react", "react-native", "vue", "angular", "nodejs", "javascript", "typescript", "python", "java", "rust", "cpp", "php", "sql", "mongodb", "postgresql-dba", "redis", "graphql", "kubernetes", "aws", "linux", "git-github", "computer-science", "datastructures-and-algorithms", "system-design", "api-design", "software-architect", "ai-engineer", "machine-learning", "data-engineer", "cyber-security", "qa", "product-manager"]

processed_dir = os.path.join('data', 'processed', 'roadmaps')
chroma_dir = os.path.join('data', 'chroma')

os.makedirs(chroma_dir, exist_ok=True)

print("Initializing ChromaDB client...")
client = chromadb.PersistentClient(path=chroma_dir)

# Check if collection exists and has cosine metric
try:
    existing_col = client.get_collection("roadmap_nodes")
    # If it exists, check its metadata
    if existing_col.metadata and existing_col.metadata.get("hnsw:space") != "cosine":
        print("Collection 'roadmap_nodes' exists but without cosine metric. Deleting...")
        client.delete_collection("roadmap_nodes")
except Exception:
    pass

print("Getting or creating collection 'roadmap_nodes' with cosine distance...")
collection = client.get_or_create_collection(
    name="roadmap_nodes",
    metadata={"hnsw:space": "cosine"}
)

print("Loading embedding model BAAI/bge-large-en-v1.5...")
model = SentenceTransformer('BAAI/bge-large-en-v1.5')

total_embedded = 0

for r_id in SUPPORTED:
    r_dir = os.path.join(processed_dir, r_id)
    latest_file = os.path.join(r_dir, 'latest.json')
    if not os.path.exists(latest_file):
        continue
        
    with open(latest_file, 'r', encoding='utf-8') as f:
        latest_data = json.load(f)
    commit_hash = latest_data.get("commit")
    if not commit_hash:
        continue
        
    # Idempotency check: see if we already have entries for this roadmap + commit
    res = collection.get(
        where={"$and": [{"roadmap_id": r_id}, {"source_version": commit_hash}]},
        limit=1
    )
    if res and res["ids"]:
        print(f"Skipping {r_id} - already embedded for commit {commit_hash}")
        continue
        
    json_path = os.path.join(r_dir, f"{commit_hash}.json")
    if not os.path.exists(json_path):
        continue
        
    print(f"Embedding {r_id} (commit {commit_hash})...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    ids = []
    documents = []
    metadatas = []
    embeddings = []
    
    nodes = data.get("topics", []) + data.get("subtopics", [])
    for node in nodes:
        n_id = node["id"]
        chroma_id = f"{r_id}::{n_id}"
        
        title = node.get("label", "")
        desc = node.get("description")
        
        if desc:
            doc_text = f"{title}. {desc}"
        else:
            doc_text = f"{title}"
            
        ids.append(chroma_id)
        documents.append(doc_text)
        metadatas.append({
            "roadmap_id": r_id,
            "node_id": n_id,
            "node_type": node.get("type", "unknown"),
            "status": node.get("status", "unknown"),
            "source_version": commit_hash
        })
        
    if documents:
        # Generate embeddings
        vecs = model.encode(documents, convert_to_numpy=True).tolist()
        
        # Upsert
        collection.upsert(
            ids=ids,
            embeddings=vecs,
            documents=documents,
            metadatas=metadatas
        )
        total_embedded += len(ids)

print(f"\nTotal nodes newly embedded: {total_embedded}")
```

## File: src/roadmap_engine/engine.py
```python
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
```

## File: src/roadmap_engine/llm.py
```python
import json
from groq import Groq
from .config import settings

def generate_narration(plan_payload: dict, max_retries: int = 2) -> dict:
    if not settings.groq_api_key or settings.groq_api_key == "placeholder_key":
        print("Warning: GROQ_API_KEY is not set. Skipping narration.")
        return plan_payload
        
    client = Groq(api_key=settings.groq_api_key)
    
    schema = {
        "type": "object",
        "properties": {
            "overall_intro": {"type": "string"},
            "week_narratives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "week_number": {"type": "integer"},
                        "intro": {"type": "string"},
                        "milestone": {"type": "string"}
                    },
                    "required": ["week_number", "intro", "milestone"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["overall_intro", "week_narratives"],
        "additionalProperties": False
    }

    # Build the prompt payload without resources or ids
    weeks_summary = []
    week_title_sets = {}
    for week in plan_payload.get("weeks", []):
        week_num = week.get("week_number")
        items = []
        titles = set()
        for item in week.get("items", []):
            if item.get("type") == "choice_group":
                options = [opt.get("title") for opt in item.get("options", [])]
                items.append(f"Choice Group: {item.get('title')} (Options: {', '.join(options)})")
                titles.add(item.get("title"))
                for opt in item.get("options", []):
                    titles.add(opt.get("title"))
            else:
                items.append(item.get("title"))
                titles.add(item.get("title"))
        weeks_summary.append({"week_number": week_num, "topics": items})
        week_title_sets[week_num] = titles
        
    system_prompt = """You are writing short motivational and orienting narration ONLY. You will be given a structured weekly plan for a learning roadmap. For each week, write a 1-2 sentence intro connecting that week's topics, and a 1-sentence milestone description of what the learner will be able to do after that week.

CRITICAL RULES:
1. Do NOT mention any URL, link, or resource by name.
2. Do NOT invent additional topics, tools, or technologies not present in the provided plan. Write only about what is explicitly listed.
3. Write only short, direct narration."""

    user_content = f"Here is the weekly plan:\n{json.dumps(weeks_summary, indent=2)}"
    
    retry_prompt_additions = ""
    
    for attempt in range(max_retries + 1):
        try:
            completion = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content + retry_prompt_additions}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "narration",
                        "strict": True,
                        "schema": schema
                    }
                }
            )
            
            raw_response = completion.choices[0].message.content
            if attempt == 0:
                print(f"=== ATTEMPT 0 RAW TEXT ===\n{raw_response}\n========================")
            parsed = json.loads(raw_response)
            
            # Faithfulness Check
            strings_to_check = [parsed.get("overall_intro", "")]
            for w in parsed.get("week_narratives", []):
                strings_to_check.append(w.get("intro", ""))
                strings_to_check.append(w.get("milestone", ""))
                
            has_url = any("http://" in s or "https://" in s for s in strings_to_check)
            
            valid_weeks = {w["week_number"] for w in plan_payload.get("weeks", [])}
            generated_weeks = {w["week_number"] for w in parsed.get("week_narratives", [])}
            has_invalid_weeks = not generated_weeks.issubset(valid_weeks)
            
            # Cross-week leakage check
            import re
            
            # Common dictionary words that appear as standalone titles
            stoplist = {"testing", "base", "internet", "hosting", "dns", "api", "apis", "git", "go", "php"}
            
            leaked_titles = []
            for w in parsed.get("week_narratives", []):
                wn = w.get("week_number")
                if wn not in week_title_sets:
                    continue
                narration_text = (w.get("intro", "") + " " + w.get("milestone", "")).lower()
                
                blocklist = set()
                for other_wn, other_titles in week_title_sets.items():
                    if other_wn != wn:
                        blocklist.update(other_titles)
                        
                # Remove titles that are valid for this week
                blocklist -= week_title_sets[wn]
                
                for b in blocklist:
                    if len(b) >= 4 and b.lower() not in stoplist:
                        # Use word boundary matching to avoid "base" triggering on "database"
                        pattern = r'\b' + re.escape(b.lower()) + r'\b'
                        if re.search(pattern, narration_text):
                            leaked_titles.append(f"'{b}' leaked into Week {wn}")
            
            has_leakage = len(leaked_titles) > 0
            
            if has_url or has_invalid_weeks or has_leakage:
                violation_msg = "\n\nCRITICAL ERROR IN PREVIOUS ATTEMPT:"
                if has_url:
                    violation_msg += "\nYou included a URL (http:// or https://). You MUST NOT include URLs."
                if has_invalid_weeks:
                    violation_msg += f"\nYou generated narratives for week numbers {generated_weeks} but the valid weeks are only {valid_weeks}."
                if has_leakage:
                    violation_msg += f"\nYou hallucinated topics into the wrong weeks: {', '.join(leaked_titles)}. You MUST NOT mention topics from other weeks."
                
                retry_prompt_additions += violation_msg
                if has_leakage:
                    print(f"[LLM] Faithfulness check failed (Attempt {attempt}): {', '.join(leaked_titles)}")
                else:
                    print(f"[LLM] Faithfulness check failed (Attempt {attempt})")
                continue # Retry
                
            # Success! Merge into payload
            merged_payload = dict(plan_payload)
            merged_payload["overall_intro"] = parsed.get("overall_intro")
            
            # Create a lookup for week narratives
            narratives_by_week = {w["week_number"]: w for w in parsed.get("week_narratives", [])}
            
            for week in merged_payload.get("weeks", []):
                wn = week["week_number"]
                if wn in narratives_by_week:
                    week["intro"] = narratives_by_week[wn]["intro"]
                    week["milestone"] = narratives_by_week[wn]["milestone"]
                    
            print(f"[LLM] Narration succeeded after {attempt} retries.")
            return merged_payload
            
        except Exception as e:
            print(f"[LLM] Exception during generation (attempt {attempt}): {e}")
            
    # If we exhaust retries or fail repeatedly
    print(f"[LLM] Narration failed after {max_retries} retries.")
    merged_payload = dict(plan_payload)
    merged_payload["narration_failed"] = True
    return merged_payload
```

## File: src/roadmap_engine/main.py
```python
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
```

## File: src/roadmap_engine/parser.py
```python
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
```

## File: src/roadmap_engine/runner.py
```python
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
```

## File: src/roadmap_engine/schemas.py
```python
from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    roadmap_id: str
    known_node_ids: list[str] = Field(default_factory=list)
    duration_weeks: int = Field(gt=0)
    hours_per_week: float = Field(gt=0.0)

class StalenessRequest(BaseModel):
    roadmap_id: str
    version_generated_against: str
    node_ids_used: list[str]
```

## File: src/roadmap_engine/staleness.py
```python
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
```

## File: src/roadmap_engine/validator.py
```python
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
```

## File: src/roadmap_engine/__init__.py
```python
```

## File: streamlit_app/app.py
```python
import streamlit as st
import requests

# Set page config
st.set_page_config(page_title="Roadmap Generator", page_icon="🗺️", layout="wide")

st.title("🗺️ Personalized Roadmap Generator")

# Sidebar for config
with st.sidebar:
    st.header("Configuration")
    API_BASE_URL = st.text_input("API Base URL", value="http://localhost:8000")

def get_api(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API_BASE_URL}{endpoint} — is the FastAPI server running?")
        st.stop()

def post_api(endpoint, payload):
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=payload)
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API_BASE_URL}{endpoint} — is the FastAPI server running?")
        st.stop()

# --- Step 2: Roadmap Selection ---
st.header("1. Select a Roadmap")
roadmaps = get_api("/roadmaps")
# Convert list of dicts to a dict mapping title/id to id
roadmap_options = {r["title"]: r["id"] for r in roadmaps}
selected_roadmap_title = st.selectbox("Roadmap", options=list(roadmap_options.keys()))

if selected_roadmap_title:
    selected_roadmap_id = roadmap_options[selected_roadmap_title]
    
    # Reset downstream topics if roadmap changes
    if st.session_state.get("current_roadmap_id") != selected_roadmap_id:
        st.session_state["current_roadmap_id"] = selected_roadmap_id
        for key in list(st.session_state.keys()):
            if key.startswith("topic_") or key.startswith("subtopic_"):
                del st.session_state[key]

    # --- Step 3: Known Topics Picker ---
    st.header("2. What do you already know?")
    st.write("Check the topics and subtopics you have already mastered.")
    topics_data = get_api(f"/roadmaps/{selected_roadmap_id}/topics")
    
    # Group topics
    top_level = [t for t in topics_data if t.get("parent_topic_id") is None]
    subtopics = {t["id"]: [] for t in top_level}
    
    for item in topics_data:
        parent_id = item.get("parent_topic_id")
        if parent_id and parent_id in subtopics:
            subtopics[parent_id].append(item)
            
    for topic in top_level:
        with st.expander(topic["title"]):
            st.checkbox("I already know this whole topic", key=f"topic_{topic['id']}")
            for subtopic in subtopics.get(topic["id"], []):
                st.checkbox(subtopic["title"], key=f"subtopic_{subtopic['id']}")
                
    # --- Step 4: Duration Inputs ---
    st.header("3. How much time do you have?")
    col1, col2 = st.columns(2)
    with col1:
        duration_weeks = st.number_input("Duration (weeks)", min_value=1, value=8, step=1)
    with col2:
        hours_per_week = st.number_input("Hours per week", min_value=0.5, value=10.0, step=0.5)

    # --- Step 5: Generate ---
    if st.button("Generate My Roadmap", type="primary"):
        # Calculate known_node_ids directly from session state
        known_node_ids = []
        for key, value in st.session_state.items():
            if (key.startswith("topic_") or key.startswith("subtopic_")) and value is True:
                # Extract the ID by removing the prefix
                node_id = key.split("_", 1)[1]
                known_node_ids.append(node_id)
                
        payload = {
            "roadmap_id": selected_roadmap_id,
            "known_node_ids": known_node_ids,
            "duration_weeks": duration_weeks,
            "hours_per_week": hours_per_week
        }
        
        with st.spinner("Generating your personalized roadmap..."):
            response = post_api("/generate", payload)
            
            if response.status_code == 200:
                st.session_state["generated_plan"] = response.json()
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text
                st.error(f"API Error ({response.status_code}): {error_detail}")

# --- Step 6: Render the Plan ---
if "generated_plan" in st.session_state:
    st.divider()
    plan = st.session_state["generated_plan"]
    
    st.header("Your Personalized Roadmap")
    if plan.get("overall_intro"):
        st.caption(plan["overall_intro"])
        
    if plan.get("narration_failed"):
        st.warning("AI narration wasn't available for this plan — showing the structured schedule only.")
        
    for week in plan.get("weeks", []):
        st.subheader(f"Week {week['week_number']}")
        
        if not plan.get("narration_failed"):
            if week.get("intro"):
                st.write(week["intro"])
            if week.get("milestone"):
                st.info(week["milestone"])
                
        for item in week.get("items", []):
            if item["type"] in ["topic_overview", "subtopic"]:
                st.markdown(f"**{item['title']}**")
                
                # We can use expander for description if it's long, or just render it. Let's do expander if there is a description.
                has_desc = bool(item.get("description"))
                has_res = bool(item.get("resources"))
                
                if has_desc or has_res:
                    with st.expander("View Details"):
                        if has_desc:
                            st.markdown(item["description"])
                        if has_res:
                            st.markdown("**Resources:**")
                            for res in item["resources"]:
                                st.markdown(f"- [{res['title']}]({res['url']})")
            
            elif item["type"] == "choice_group":
                st.markdown("🔀 **Choose one:**")
                for option in item.get("options", []):
                    title = f"⭐ Recommended: {option['title']}" if option.get("status") == "personal_recommendation" else option['title']
                    with st.expander(title):
                        if option.get("description"):
                            st.markdown(option["description"])
                        if option.get("resources"):
                            st.markdown("**Resources:**")
                            for res in option["resources"]:
                                st.markdown(f"- [{res['title']}]({res['url']})")
                                
    if plan.get("stretch_goals"):
        st.divider()
        st.header("Stretch Goals (if you have extra time)")
        for item in plan["stretch_goals"]:
            st.markdown(f"**{item['title']}**")
            has_desc = bool(item.get("description"))
            has_res = bool(item.get("resources"))
            if has_desc or has_res:
                with st.expander("View Details"):
                    if has_desc:
                        st.markdown(item["description"])
                    if has_res:
                        st.markdown("**Resources:**")
                        for res in item["resources"]:
                            st.markdown(f"- [{res['title']}]({res['url']})")

    # --- Step 7: Staleness Check ---
    st.divider()
    if st.button("Check for roadmap updates"):
        staleness_payload = {
            "roadmap_id": plan["roadmap_id"],
            "version_generated_against": plan["version_generated_against"],
            "node_ids_used": plan["node_ids_used"]
        }
        with st.spinner("Checking for updates..."):
            stale_res = post_api("/check-staleness", staleness_payload)
            if stale_res.status_code == 200:
                stale_data = stale_res.json()
                if not stale_data.get("stale"):
                    st.success("Your plan is up to date")
                else:
                    changed_nodes = stale_data.get("changed_nodes", [])
                    st.warning("Your plan is stale. The following nodes have changed: " + ", ".join([f"{n['title']} ({n['id']})" for n in changed_nodes]))
            else:
                st.error("Failed to check staleness.")
```

## File: tests/test_api.py
```python
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
```

## File: tests/test_groq.py
```python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from groq import Groq
from roadmap_engine.config import settings

sys.stdout.reconfigure(encoding='utf-8')

def main():
    if not settings.groq_api_key or settings.groq_api_key == "placeholder_key" or settings.groq_api_key == "your_key_here":
        print("Please set your GROQ_API_KEY in the .env file")
        return
        
    client = Groq(api_key=settings.groq_api_key)
    
    schema = {
        "type": "object", 
        "properties": {
            "greeting": {"type": "string"}
        },
        "required": ["greeting"], 
        "additionalProperties": False
    }

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": "Please greet me."
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema": schema
                }
            }
        )
        
        print("RAW RESPONSE:")
        print(completion.choices[0].message.content)
        
    except Exception as e:
        print("API Call failed:", str(e))

if __name__ == "__main__":
    main()
```

## File: tests/test_llm.py
```python
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
```

## File: tests/test_staleness.py
```python
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
```

