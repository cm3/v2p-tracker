import pandas as pd
import json
import os
import time
from openai import OpenAI

# OpenAI APIキーの取得
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ファイルの読み込み
csv_path = "page_line_mentions_grouped_requests_output.csv"
df = pd.read_csv(csv_path)

# 内容カラムにNaNがある場合は除去
df = df.dropna(subset=['内容'])

# 出力ファイル
output_path = "min115_embeddings.jsonl"

with open(output_path, "w", encoding="utf-8") as f:
    for idx, row in df.iterrows():
        text_id = row['min115-contents-ID']
        text = row['内容']

        try:
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            embedding = response.data[0].embedding
            json_obj = {
                "id": text_id,
                "embedding": embedding
            }
            f.write(json.dumps(json_obj, ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"Error on row {idx} (ID={text_id}): {e}")
            continue

        time.sleep(0.5)  # API制限対策
