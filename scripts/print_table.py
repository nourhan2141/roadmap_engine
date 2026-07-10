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
