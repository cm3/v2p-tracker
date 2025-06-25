import csv
import json

input_file = "page_line_mentions_grouped_requests_log_116.txt"
output_file = "mentions_in_min116.csv"
target_label = "言及"

rows = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        try:
            record = json.loads(line)
            speaker = record.get("発言者", "")
            uid = record.get("発言ID", "")
            chunk = record.get("発言原文", "")
            raw_response = record.get("raw_response", "")

            # コードブロック記号の除去（APIが ```json ... ``` を返す場合の対処）
            if raw_response.startswith("```json"):
                raw_response = raw_response.replace("```json", "").replace("```", "").strip()

            parsed = json.loads(raw_response)

            for item in parsed:
                rows.append({
                    "発言ID": uid,
                    "発言者": speaker,
                    "発言原文": chunk,
                    "内容": item.get("内容", ""),
                    target_label+"あり": item.get(target_label+"あり", ""),
                    "他の委員の発言参照": item.get("他の委員の発言参照", ""),
                    "参照されたページ・行": item.get("参照されたページ・行", ""),
                    "理由": item.get("理由", "")
                })

        except Exception as e:
            print(f"Parse error: {e}")
            continue

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "発言ID", "発言者", "発言原文", "内容", target_label+"あり", "他の委員の発言参照", "参照されたページ・行", "理由"
    ])
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ CSVファイル出力完了: {output_file}")
