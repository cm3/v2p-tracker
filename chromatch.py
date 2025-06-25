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

# 要求がある発言のみ抽出
df = pd.read_csv("page_line_mentions_grouped_requests_output.csv")
requests = df[df["要求あり"] == "Yes"].dropna(subset=["内容"])

# 結果リストを分けて保持
results_to_draft = []
results_to_final_draft = []
results_to_minutes = []

for _, row in requests.iterrows():
    content_id = str(row["min115-contents-ID"])

    try:
        # embedding を議事録コレクションから取得
        emb_result = collection_min115.get(ids=[content_id], include=["embeddings"])
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

        # 2. 議事録内の他の発言から類似検索（※自分自身除外）
        matches_minutes = collection_min115.query(query_embeddings=[embedding], n_results=top_n+1)
        for pid, dist in zip(matches_minutes["ids"][0], matches_minutes["distances"][0]):
            if pid != content_id:  # 自分自身を除外
                results_to_minutes.append({
                    "request_id": content_id,
                    "matched_id": pid,
                    "score": dist
                })

    except Exception as e:
        print(f"[Error] ID {content_id}: {e}")

# 結果を保存
with open("matched_to_draft.json", "w", encoding="utf-8") as f1:
    json.dump(results_to_draft, f1, ensure_ascii=False, indent=2)

with open("matched_to_final_draft.json", "w", encoding="utf-8") as f2:
    json.dump(results_to_final_draft, f2, ensure_ascii=False, indent=2)

with open("matched_to_minutes.json", "w", encoding="utf-8") as f3:
    json.dump(results_to_minutes, f3, ensure_ascii=False, indent=2)

print("✅ 保存完了: matched_to_draft.json / matched_to_final_draft.json / matched_to_minutes.json")
