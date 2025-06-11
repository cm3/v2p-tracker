import pandas as pd
from sentence_transformers import SentenceTransformer, util
import xml.etree.ElementTree as ET
import numpy as np
import re

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# === XML読み込みと <seg>抽出（id付き）===
def extract_segments_with_ids(xml_file):
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    tree = ET.parse(xml_file)
    root = tree.getroot()
    seg_elements = root.findall('.//tei:seg', ns)
    return [
        {'id': seg.attrib.get('{http://www.w3.org/XML/1998/namespace}id'), 'text': seg.text.strip()}
        for seg in seg_elements
        if seg.text and seg.attrib.get('{http://www.w3.org/XML/1998/namespace}id')
    ]

tei_segments = extract_segments_with_ids("ENV_113-116.xml")
tei_texts = [s['text'] for s in tei_segments]
tei_ids = [s['id'] for s in tei_segments]
tei_embeddings = model.encode(tei_texts, convert_to_tensor=True)

# === CSV読み込み ===
df = pd.read_csv("diff_classified.csv")

# === content_ins, content_del を作る ===
def extract_ins(text):
    return ' '.join(re.findall(r'<ins>(.*?)</ins>', str(text)))

def extract_del(text):
    return ' '.join(re.findall(r'<del>(.*?)</del>', str(text)))

df['content_ins'] = df['content'].map(extract_ins)
df['content_del'] = df['content'].map(extract_del)

# === 類似度算出とCSV出力関数 ===
def compute_and_save_similarity(column_name, output_file):
    texts = df[column_name].fillna("").tolist()
    ids = df['id'].tolist()
    embeddings = model.encode(texts, convert_to_tensor=True)

    results = []
    for idx, emb in enumerate(embeddings):
        cos_scores = util.pytorch_cos_sim(emb, tei_embeddings)[0].cpu().numpy()
        top_indices = np.argpartition(-cos_scores, range(10))[:10]
        top_sorted = top_indices[np.argsort(-cos_scores[top_indices])]
        for i in top_sorted:
            results.append({
                "change_id": ids[idx],
                "matched_seg_id": tei_ids[i],
                "matched_seg_text": tei_texts[i],
                "similarity": float(cos_scores[i])
            })

    pd.DataFrame(results).to_csv(output_file, index=False)
    print(f"✅ {output_file} に保存しました")

# === 各条件で実行 ===
compute_and_save_similarity("justification", "match_justification.csv")
compute_and_save_similarity("content", "match_content.csv")
compute_and_save_similarity("content_ins", "match_content_ins.csv")
compute_and_save_similarity("content_del", "match_content_del.csv")
