import pandas as pd
import json
from bs4 import BeautifulSoup

# 入力ファイルパス
CSV_PATH = "mentions_in_min116.csv"
DRAFT_PATH = "env6plan_draft.html"
FINAL_DRAFT_PATH = "env6plan_final_draft.html"
MATCHED_DRAFT_PATH = "matched_min116_to_draft.json"
MATCHED_FINAL_DRAFT_PATH = "matched_min116_to_final_draft.json"
MATCHED_MINUTES115_PATH = "matched_min116_to_min115.json"
MATCHED_MINUTES116_PATH = "matched_min116_to_min116.json"
OUTPUT_HTML = "viewer_min116.html"

# 表示する関連候補の最大数
MAX_MATCHES = 10

# 議事録CSVの読み込み（言及ありに絞らず全体取得）
df_all = pd.read_csv(CSV_PATH)
df = df_all[df_all["言及あり"] == "Yes"].dropna(subset=["内容"])

# 発言本文全体を辞書化（←「言及あり」絞らず）
all_minutes_texts = df_all.set_index("min116-contents-ID")["内容"].to_dict()

# ページなどの補足情報（言及ありのみでOK）
info_fields = ["言及あり", "他の委員の発言参照", "理由", "参照されたページ・行", "発言者", "発言原文"]
info_dict = df.set_index("min116-contents-ID")[info_fields].to_dict(orient="index")

# HTMLから段落を抽出しIDと本文の辞書にする関数
def extract_paragraphs(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    return {p.get("id"): p.get_text(strip=True) for p in soup.find_all("p") if p.get("id")}

def get_minutes_link(seg_id, csv_path, id_column):
    try:
        df = pd.read_csv(csv_path)
        id_map = dict(zip(df[id_column].astype(str), df["発言ID"].astype(str)))

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
matched_min115 = load_json_grouped_by_request_id(MATCHED_MINUTES115_PATH)
matched_min116 = load_json_grouped_by_request_id(MATCHED_MINUTES116_PATH)

# HTML構築
html = ['<html lang="ja"><head><meta charset="utf-8"><title>変更言及対応ビューワー</title><style>body{font-family:sans-serif;} section{margin-bottom:2em;} .match{margin-left:1em;}</style></head><body>']
html.append("<h1>変更言及と関連候補</h1>")

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
        cid = str(row["min116-contents-ID"])
        content = row["内容"]
        html.append(f"<div><h3>発言内の変更の言及の概要:</h3><p>{content}</p>")

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
        if cid in matched_min115:
            html.append("<h4>関連議事録(115):</h4><ul>")
            for match in matched_min115[cid][:MAX_MATCHES]:
                pid = match["matched_id"]
                text = all_minutes_texts.get(int(pid), "[該当発言なし]")
                score = round(match["score"], 4)
                linked_id = get_minutes_link(pid, "requests_in_min115.csv", "min115-contents-ID")
                html.append(f'<li class="match">ID: {linked_id}（score: {score}）<br><blockquote>{text}</blockquote></li>')
            html.append("</ul>")

        # 類似：議事録
        if cid in matched_min116:
            html.append("<h4>関連議事録(116):</h4><ul>")
            for match in matched_min116[cid][:MAX_MATCHES]:
                pid = match["matched_id"]
                text = all_minutes_texts.get(int(pid), "[該当発言なし]")
                score = round(match["score"], 4)
                linked_id = get_minutes_link(pid, CSV_PATH, "min116-contents-ID")
                html.append(f'<li class="match">ID: {linked_id}（score: {score}）<br><blockquote>{text}</blockquote></li>')
            html.append("</ul>")

        html.append("</div>")
    html.append("</section>")

html.append("</body></html>")

# 出力
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write("\n".join(html))

print(f"✅ ビューアーHTMLを生成しました: {OUTPUT_HTML}")
