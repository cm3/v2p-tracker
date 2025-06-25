import json
import chromadb

client = chromadb.PersistentClient(path="./chroma_env6plan")

col1 = client.get_or_create_collection("env6plan_draft", metadata={"hnsw:space": "cosine"})
with open("env6plan_draft.jsonl","r",encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        col1.add(
            ids=[str(obj["id"])],
            embeddings=[obj["embedding"]],
            documents=[obj.get("text", "")]
        )

col2 = client.get_or_create_collection("env6plan_final_draft", metadata={"hnsw:space": "cosine"})
with open("env6plan_final_draft.jsonl","r",encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        col2.add(
            ids=[str(obj["id"])],
            embeddings=[obj["embedding"]],
            documents=[obj.get("text", "")]
        )

col3 = client.get_or_create_collection("env6plan_min115", metadata={"hnsw:space": "cosine"})
with open("min115_embeddings.jsonl","r",encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        col3.add(
            ids=[str(obj["id"])],
            embeddings=[obj["embedding"]],
            documents=[obj.get("text", "")]
        )

col4 = client.get_or_create_collection("env6plan_min116", metadata={"hnsw:space": "cosine"})
with open("min116_embeddings.jsonl","r",encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        col4.add(
            ids=[str(obj["id"])],
            embeddings=[obj["embedding"]],
            documents=[obj.get("text", "")]
        )

# 自動的に永続化されます
