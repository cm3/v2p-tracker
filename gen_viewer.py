import pandas as pd
import json
from bs4 import BeautifulSoup

# 入力ファイルパス
CSV_PATH = "page_line_mentions_grouped_requests_output.csv"
DRAFT_PATH = "env6plan_draft.html"
FINAL_DRAFT_PATH = "env6plan_final_draft.html"
MATCHED_DRAFT_PATH = "matched_to_draft.json"
MATCHED_FINAL_DRAFT_PATH = "matched_to_final_draft.json"
MATCHED_MINUTES_PATH = "matched_to_minutes.json"
OUTPUT_HTML = "viewer.html"

# 表示する関連候補の最大数
MAX_MATCHES = 3

# 議事録CSVの読み込み（要求ありに絞らず全体取得）
df_all = pd.read_csv(CSV_PATH)
df = df_all[df_all["要求あり"] == "Yes"].dropna(subset=["内容"])

# 発言本文全体を辞書化（←「要求あり」絞らず）
all_minutes_texts = df_all.set_index("min115-contents-ID")["内容"].to_dict()

# ページなどの補足情報（要求ありのみでOK）
info_fields = ["要求あり", "他の委員の発言参照", "理由", "参照されたページ・行", "発言者", "発言原文"]
info_dict = df.set_index("min115-contents-ID")[info_fields].to_dict(orient="index")

# HTMLから段落を抽出しIDと本文の辞書にする関数
def extract_paragraphs(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    return {p.get("id"): p.get_text(strip=True) for p in soup.find_all("p") if p.get("id")}

def get_minutes_link(seg_id, csv_path):
    try:
        df = pd.read_csv(csv_path)
        id_map = dict(zip(df["min115-contents-ID"].astype(str), df["発言ID"].astype(str)))

        original_id = id_map.get(str(seg_id), None)
        if pd.notna(original_id):
            return f'<a href="minutes.html#{original_id}" target="_blank">{original_id}</a> （発言内容ID: {seg_id}）'
        else:
            return seg_id
    except Exception as e:
        print(f"Error reading minutes mapping: {e}")
        return seg_id

# HTML段落の取得
draft_paragraphs = extract_paragraphs(DRAFT_PATH)
final_draft_paragraphs = extract_paragraphs(FINAL_DRAFT_PATH)

# JSON 読み込み
def load_json_grouped_by_request_id(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    grouped = {}
    for item in raw:
        grouped.setdefault(str(item["request_id"]), []).append(item)
    return grouped

matched_draft = load_json_grouped_by_request_id(MATCHED_DRAFT_PATH)
matched_final_draft = load_json_grouped_by_request_id(MATCHED_FINAL_DRAFT_PATH)
matched_minutes = load_json_grouped_by_request_id(MATCHED_MINUTES_PATH)

# HTML構築
html = ['<html lang="ja"><head><meta charset="utf-8"><title>要求対応ビューワー</title><style>body{font-family:sans-serif;} section{margin-bottom:2em;} .match{margin-left:1em;}</style></head><body>']
html.append("<h1>要求と関連候補</h1>")

grouped = df.groupby("発言ID")

for speaker_id, group in grouped:
    html.append(f"<section><h2>発言ID: {speaker_id}</h2>")

    # 発言IDの最初の行の補足情報
    row0 = group.iloc[0]
    html.append("<ul>")
    for key in info_fields:
        val = row0.get(key)
        if pd.notna(val):
            html.append(f"<li>{key}: {val}</li>")
    html.append("</ul>")

    for _, row in group.iterrows():
        cid = str(row["min115-contents-ID"])
        content = row["内容"]
        html.append(f"<div><h3>発言内の変更の要求の概要:</h3><p>{content}</p>")

        # 類似：計画案
        if cid in matched_draft:
            html.append("<h4>案の中の関連箇所:</h4><ul>")
            for match in matched_draft[cid][:MAX_MATCHES]:
                pid = match["matched_id"]
                text = draft_paragraphs.get(pid, "[該当段落なし]")
                score = round(match["score"], 4)
                link = f'env6plan_draft.html#{pid}'
                html.append(f'<li class="match">ID: <a href="{link}" target="_blank">{pid}</a>（score: {score}）<br><blockquote>{text}</blockquote></li>')
            html.append("</ul>")

        # 類似：答申案
        if cid in matched_final_draft:
            html.append("<h4>答申案の中の関連箇所:</h4><ul>")
            for match in matched_final_draft[cid][:MAX_MATCHES]:
                pid = match["matched_id"]
                text = final_draft_paragraphs.get(pid, "[該当段落なし]")
                score = round(match["score"], 4)
                link = f'env6plan_final_draft.html#{pid}'
                html.append(f'<li class="match">ID: <a href="{link}" target="_blank">{pid}</a>（score: {score}）<br><blockquote>{text}</blockquote></li>')
            html.append("</ul>")

        # 類似：議事録
        if cid in matched_minutes:
            html.append("<h4>関連議事録:</h4><ul>")
            for match in matched_minutes[cid][:MAX_MATCHES]:
                pid = match["matched_id"]
                text = all_minutes_texts.get(int(pid), "[該当発言なし]")
                score = round(match["score"], 4)
                linked_id = get_minutes_link(pid, "page_line_mentions_grouped_requests_output.csv")
                html.append(f'<li class="match">ID: {linked_id}（score: {score}）<br><blockquote>{text}</blockquote></li>')
            html.append("</ul>")

        html.append("</div>")
    html.append("</section>")

html.append("</body></html>")

# 出力
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"✅ ビューアーHTMLを生成しました: {OUTPUT_HTML}")
