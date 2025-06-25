import os
import json
import time
import xml.etree.ElementTree as ET
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

xml_file = "ENV_113-116.xml"
log_file = "page_line_mentions_grouped_requests_log.txt"
limit = 0

ns = {
    'tei': 'http://www.tei-c.org/ns/1.0',
    'xml': 'http://www.w3.org/XML/1998/namespace'
}
tree = ET.parse(xml_file)
root = tree.getroot()

meeting = root.find(".//tei:*[@xml:id='meeting-115']", ns)
utterances = meeting.findall('.//tei:u', ns)

persons = {}
for person in root.findall('.//tei:person', ns):
    pid = person.attrib.get('{http://www.w3.org/XML/1998/namespace}id')
    pers_name = person.find('.//tei:persName', ns)
    if pers_name is not None:
        surname = pers_name.find('tei:surname', ns)
        forename = pers_name.find('tei:forename', ns)
        if surname is not None and forename is not None:
            name = surname.text.strip() + forename.text.strip()
        else:
            name = ''.join(pers_name.itertext()).strip()
    else:
        name = "(不明)"
    persons[f"#{pid}"] = name

def split_text_into_chunks(segments, max_chars=800):
    chunks = []
    current = []
    total = 0
    for seg in segments:
        seg_text = ''.join(seg.itertext()).strip()
        if total + len(seg_text) > max_chars and current:
            chunks.append(' '.join(current))
            current = [seg_text]
            total = len(seg_text)
        else:
            current.append(seg_text)
            total += len(seg_text)
    if current:
        chunks.append(' '.join(current))
    return chunks

with open(log_file, 'w', encoding='utf-8') as logf:
    for i, u in enumerate(utterances):
        if limit > 0 and i >= limit:
            break

        uid = u.attrib.get('{http://www.w3.org/XML/1998/namespace}id', '')
        who = u.attrib.get('who', '')
        speaker = persons.get(who, who)

        segments = u.findall('.//tei:seg', ns)
        chunks = split_text_into_chunks(segments)

        for part_num, chunk in enumerate(chunks):
            if len(chunk.strip()) <= 15:
                parsed_raw = json.dumps([{
                    "内容": chunk,
                    "要求あり": "No",
                    "他の委員の発言参照": "No",
                    "参照されたページ・行": "",
                    "理由": "15文字以下なのでスキップされた"
                }], ensure_ascii=False)
                prompt = ""
            else:
                prompt = f"""
以下の発言は、行政計画の文書に関する議論中の1人の委員の発言です。

ここでの「要求」とは、行政計画文書の明確な変更を迫る要求のことを指します。議事進行など、行政計画文書の変更に関わらない要求については無視してください。

参照されたページや行があれば、その情報に加えて「見え消し版」「溶け込み版」などの版の種類も取得してください。

この発言に含まれる要求を、まとまり（同じ意図の要求）ごとに分けて抽出してください。

それぞれの要求まとまり（または要求がなければ全体で1件）について、以下の形式でJSON配列として出力してください：

[
  {{
    "内容": "要求の具体的な抜粋（1文〜数文）",
    "要求あり": "Yes または No",
    "他の委員の発言参照": "Yes または No",
    "参照されたページ・行": "例: 12ページ5行（見え消し版）, 13ページ5-6行（溶け込み版）など、あれば。なければ空欄。",
    "理由": "なぜそう判断したかの簡潔な説明"
  }}
]

---
発言: 「{chunk}」
"""
                try:
                    response = client.chat.completions.create(
                        model="gpt-4.1",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=2000
                    )
                    content = response.choices[0].message.content
                    if not content or not content.strip():
                        raise ValueError("Empty or None content from API")
                    parsed_raw = content.strip()
                except Exception as e:
                    parsed_raw = json.dumps([{
                        "内容": chunk,
                        "要求あり": "Error",
                        "他の委員の発言参照": "Error",
                        "参照されたページ・行": "",
                        "理由": str(e)
                    }], ensure_ascii=False)

            json.dump({
                "発言ID": uid,
                "発言者": speaker,
                "発言原文": chunk,
                "prompt": prompt,
                "raw_response": parsed_raw
            }, logf, ensure_ascii=False)
            logf.write("\n")

        time.sleep(0.5)

print(f"✅ JSONログ出力完了: {log_file}")
