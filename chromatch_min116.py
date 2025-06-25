import pandas as pd
import json
import chromadb

# 上位 n 件
top_n = 10

# ChromaDB クライアントとコレクション
client = chromadb.PersistentClient(path="./chroma_env6plan")
collection_draft = client.get_collection("env6plan_draft")
collection_final_draft = client.get_collection("env6plan_final_draft")
collection_min115 = client.get_collection("env6plan_min115")
collection_min116 = client.get_collection("env6plan_min116")

# 要求がある発言のみ抽出
df = pd.read_csv("mentions_in_min116.csv")
mentions = df[df["言及あり"] == "Yes"].dropna(subset=["内容"])

# 結果リストを分けて保持
results_to_draft = []
results_to_final_draft = []
results_to_minutes115 = []
results_to_minutes116 = []

for _, row in mentions.iterrows():
    content_id = str(row["min116-contents-ID"])

    try:
        # embedding を議事録コレクションから取得
        emb_result = collection_min116.get(ids=[content_id], include=["embeddings"])
        embedding = emb_result["embeddings"][0]

        # 1-1. 案から類似検索
        matches_draft = collection_draft.query(query_embeddings=[embedding], n_results=top_n)
        for pid, dist in zip(matches_draft["ids"][0], matches_draft["distances"][0]):
            results_to_draft.append({
                "request_id": content_id,
                "matched_id": pid,
                "score": dist
            })

        # 1-2. 答申案から類似検索
        matches_final_draft = collection_final_draft.query(query_embeddings=[embedding], n_results=top_n)
        for pid, dist in zip(matches_final_draft["ids"][0], matches_final_draft["distances"][0]):
            results_to_final_draft.append({
                "request_id": content_id,
                "matched_id": pid,
                "score": dist
            })

        # 2-1. 議事録内の他の発言から類似検索（※自分自身除外）
        matches_minutes_116 = collection_min116.query(query_embeddings=[embedding], n_results=top_n+1)
        for pid, dist in zip(matches_minutes_116["ids"][0], matches_minutes_116["distances"][0]):
            if pid != content_id:  # 自分自身を除外
                results_to_minutes116.append({
                    "request_id": content_id,
                    "matched_id": pid,
                    "score": dist
                })

        # 2-2. 別の回（115）の議事録内から類似検索
        matches_minutes_115 = collection_min115.query(query_embeddings=[embedding], n_results=top_n)
        for pid, dist in zip(matches_minutes_115["ids"][0], matches_minutes_115["distances"][0]):
            results_to_minutes115.append({
                "request_id": content_id,
                "matched_id": pid,
                "score": dist
            })

    except Exception as e:
        print(f"[Error] ID {content_id}: {e}")

# 結果を保存
with open("matched_min116_to_draft.json", "w", encoding="utf-8") as f1:
    json.dump(results_to_draft, f1, ensure_ascii=False, indent=2)

with open("matched_min116_to_final_draft.json", "w", encoding="utf-8") as f2:
    json.dump(results_to_final_draft, f2, ensure_ascii=False, indent=2)

with open("matched_min116_to_min116.json", "w", encoding="utf-8") as f3:
    json.dump(results_to_minutes116, f3, ensure_ascii=False, indent=2)

with open("matched_min116_to_min115.json", "w", encoding="utf-8") as f4:
    json.dump(results_to_minutes115, f4, ensure_ascii=False, indent=2)

print("✅ 保存完了: matched_min116_to_***.json")
