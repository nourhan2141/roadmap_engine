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
