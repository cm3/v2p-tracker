import os
import json
import time
import openai
from bs4 import BeautifulSoup

# OpenAI API クライアント初期化
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 入力 HTML ファイル
html_file = "env6plan_final_draft.html"

# 出力ファイル
output_file = "env6plan_final_draft.jsonl"

# HTML を読み込み
with open(html_file, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# 全 <p> タグを取得
paragraphs = soup.find_all("p")

with open(output_file, "w", encoding="utf-8") as out_f:
    for p in paragraphs:
        pid = p.get("id")
        if not pid:
            continue

        # タグの中のテキストだけを取得
        text = p.get_text(strip=True)
        if not text:
            continue

        try:
            response = client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            embedding = response.data[0].embedding
            json.dump({"id": pid, "embedding": embedding}, out_f, ensure_ascii=False)
            out_f.write("\n")

        except Exception as e:
            print(f"❌ Error on paragraph {pid}: {e}")
            continue

        time.sleep(0.5)  # API制限回避のための待機
