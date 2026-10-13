"""Extract the fixed PDF corpus; semantic assertions remain pending until reviewed."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

DATE = r"20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}(?:日)?(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?"
LESSON = re.compile(r"^教你炒股票\s*(\d{1,3})\s*[：:]")
ACTOR = re.compile(r"^(.{1,35}?)\s*[：:]\s*(" + DATE + r")\s*$")
TECH = re.compile(r"中枢|走势|级别|背驰|买点|卖点|分型|特征序列|线段|均线|笔|趋势|盘整|区间套|递归|震荡|缺口")
CONCEPTS = {
    "走势中枢": ["缠中说禅走势中枢", "中枢"], "走势类型": [], "走势": [],
    "级别": [], "次级别": [], "最低级别": ["最低不可分解级别"], "趋势": [], "盘整": [],
    "上涨": [], "下跌": [], "背驰": [], "盘整背驰": [], "分型": [], "笔": [], "线段": [],
    "特征序列": [], "第一类买点": [], "第二类买点": [], "第三类买点": [],
    "第一类卖点": [], "第二类卖点": [], "第三类卖点": [], "区间套": [],
    "走势终完美": [], "结合律": [], "中枢震荡": [], "中枢扩展": [], "中枢延伸": [],
    "中枢新生": [], "中枢扩张": [], "包含关系": [], "缺口": [], "K线": ["K 线"], "递归": [],
}


def j(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def norm_with_map(chars, indices):
    out, mapping = [], []
    for i, char in enumerate(chars):
        value = char.get("text", "")
        for c in value:
            if c.isspace():
                prev = out[-1] if out else ""
                nxt = "".join(x.get("text", "") for x in chars[i + 1:i + 3]).lstrip()[:1]
                if prev.isascii() and prev.isalnum() and nxt.isascii() and nxt.isalnum():
                    out.append(" ")
                    mapping.append(indices[i])
                continue
            out.append(c)
            mapping.append(indices[i])
    return "".join(out), mapping


def is_body(line, height):
    t = line["text"].strip()
    return line["top"] >= 48 and line["bottom"] < height - 45 and not t.startswith("全球第一博客")


def extract(sources, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "sources").mkdir(exist_ok=True)
    (output / "geometry").mkdir(exist_ok=True)
    temporary = output / "building.sqlite"
    if temporary.exists():
        raise RuntimeError(f"已有未完成构建 {temporary}；先检查其状态，禁止无意覆盖")
    db = sqlite3.connect(temporary)
    db.executescript((Path(__file__).parents[1] / "contracts/schema.sql").read_text(encoding="utf-8"))
    source_manifest, unit_ids = [], set()
    now = datetime.now(timezone.utc).isoformat()
    db.execute("INSERT INTO metadata VALUES('schema_version',?)", (j("1.1.0"),))
    db.execute("INSERT INTO metadata VALUES('graph_version',?)", (j("0.1.0-source"),))
    db.execute("INSERT INTO metadata VALUES('built_at',?)", (j(now),))
    for label, aliases in CONCEPTS.items():
        db.execute("INSERT INTO concepts(id,label,aliases,description) VALUES(?,?,?,?)", ("concept-" + digest(label), label, j(aliases), ""))
    for source in sources:
        sha = hashlib.file_digest(source.open("rb"), "sha256").hexdigest()
        doc_id = source.stem + "-" + sha[:12]
        target = output / "sources" / source.name
        if not target.exists() or hashlib.file_digest(target.open("rb"), "sha256").hexdigest() != sha:
            shutil.copy2(source, target)
        with pdfplumber.open(source) as pdf:
            db.execute("INSERT INTO documents VALUES(?,?,?,?,?)", (doc_id, source.name, sha, len(pdf.pages), "sources/" + source.name))
            source_manifest.append({"id": doc_id, "filename": source.name, "sha256": sha, "page_count": len(pdf.pages)})
            unit_id, role, speaker, published = None, "unknown", None, None
            for page_no, page in enumerate(pdf.pages, 1):
                chars = page.chars
                lookup = {id(c): i for i, c in enumerate(chars)}
                char_by_key = {(round(c["x0"], 3), round(c["top"], 3), c["text"]): i for i, c in enumerate(chars)}
                lines = page.extract_text_lines(layout=False, strip=True, return_chars=True)
                raw = "\n".join(line["text"] for line in lines)
                printed = next((re.search(r"-\s*(\d+)\s*-", x["text"]).group(1) for x in lines if x["top"] > page.height - 45 and re.search(r"-\s*(\d+)\s*-", x["text"])), None)
                geom_path = f"geometry/{doc_id}-{page_no:04}.json.gz"
                geom = {"width": page.width, "height": page.height, "chars": [[c["text"], round(c["x0"], 3), round(c["top"], 3), round(c["x1"], 3), round(c["bottom"], 3)] for c in chars]}
                with gzip.open(output / geom_path, "wt", encoding="utf-8") as f:
                    json.dump(geom, f, ensure_ascii=False, separators=(",", ":"))
                db.execute("INSERT INTO pages VALUES(?,?,?,?,?,?,?,?)", (f"{doc_id}-p{page_no:04}", doc_id, page_no, printed, page.width, page.height, raw, geom_path))
                for n, image in enumerate(page.images):
                    db.execute("INSERT INTO figures(id,document_id,pdf_page,bbox,pixel_width,pixel_height) VALUES(?,?,?,?,?,?)", (f"{doc_id}-p{page_no:04}-fig{n+1}", doc_id, page_no, j([image["x0"], image["top"], image["x1"], image["bottom"]]), *(image.get("srcsize") or (None, None))))
                body = [line for line in lines if is_body(line, page.height)]
                margin = min((line["x0"] for line in body), default=70)
                blocks, current = [], []
                for line in body:
                    text = line["text"].strip()
                    lesson = LESSON.match(text)
                    stamp = ACTOR.match(text)
                    heading = lesson and (max((c.get("size", 0) for c in line["chars"]), default=0) >= 14 or re.search(DATE, text))
                    section = "缠中说禅回复" in text and len(text) < 35
                    if current and (heading or stamp or section or line["x0"] > margin + 12 or line["top"] - current[-1]["bottom"] > 13):
                        blocks.append(current)
                        current = []
                    current.append(line)
                    if heading or stamp or section:
                        blocks.append(current)
                        current = []
                if current:
                    blocks.append(current)
                for block_no, block in enumerate(blocks):
                    raw_block = "\n".join(line["text"] for line in block)
                    first = block[0]["text"].strip()
                    lesson = LESSON.match(first)
                    heading = lesson and (max((c.get("size", 0) for c in block[0]["chars"]), default=0) >= 14 or re.search(DATE, first))
                    stamp = ACTOR.match(first)
                    if heading:
                        number = int(lesson.group(1))
                        proposed = f"lesson-{number:03}"
                        unit_id = proposed if proposed not in unit_ids else proposed + "-" + digest(doc_id + str(page_no))[:6]
                        unit_ids.add(unit_id)
                        published = (re.search(DATE, raw_block).group(0) if re.search(DATE, raw_block) else None)
                        db.execute("INSERT INTO units(id,title,kind,lesson_number,published_at,document_id,start_page,end_page) VALUES(?,?,?,?,?,?,?,?)", (unit_id, raw_block, "lesson", number, published, doc_id, page_no, page_no))
                        role, speaker = "author_body", "缠中说禅"
                    elif "缠中说禅回复" in first and len(first) < 35:
                        role, speaker, published = "unknown", None, None
                    elif stamp:
                        speaker, published = stamp.group(1).strip(), stamp.group(2)
                        role = "author_reply" if speaker == "缠中说禅" else "reader"
                    # Preserve front matter and content without a trusted article boundary.
                    flat_chars = [c for line in block for c in line["chars"]]
                    indices = [lookup.get(id(c), char_by_key.get((round(c["x0"], 3), round(c["top"], 3), c["text"]), -1)) for c in flat_chars]
                    text, mapping = norm_with_map(flat_chars, indices)
                    boxes = [[round(line["x0"], 3), round(line["top"], 3), round(line["x1"], 3), round(line["bottom"], 3)] for line in block]
                    pid = f"{doc_id}-p{page_no:04}-b{block_no:03}"
                    db.execute("INSERT INTO passages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (pid, unit_id, doc_id, page_no, block_no, role, speaker, published, text, raw_block, j(boxes), j(mapping), j(indices)))
                    db.execute("INSERT INTO passage_fts VALUES(?,?)", (pid, text))
                    if unit_id:
                        db.execute("UPDATE units SET end_page=? WHERE id=?", (page_no, unit_id))
                    if role in ("author_body", "author_reply") and TECH.search(text) and len(text) > 30 and not heading and not stamp:
                        concept_ids = ["concept-" + digest(k) for k, aliases in CONCEPTS.items() if k in text or any(a in text for a in aliases)]
                        cid = "candidate-" + digest(pid)
                        db.execute("INSERT INTO claims(id,text,kind,concept_ids,review_status,review_note) VALUES(?,?,?,?,?,?)", (cid, text, "explicit", j(concept_ids), "pending", "按技术词召回的原文候选，尚未进行语义和身份复核"))
                        db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?)", ("evidence-" + digest(cid), cid, pid, text, 0, len(text), j([{"document_id": doc_id, "pdf_page": page_no, "char_indices": mapping, "boxes": boxes}]), "[]"))
                if page_no % 10 == 0 or page_no == len(pdf.pages):
                    db.commit()
                    print(j({"document": source.name, "page": page_no, "total": len(pdf.pages)}), flush=True)
                page.close()
    db.commit()
    counts = {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("documents", "pages", "units", "passages", "figures", "concepts", "claims")}
    lessons = [row[0] for row in db.execute("SELECT DISTINCT lesson_number FROM units WHERE kind='lesson' ORDER BY lesson_number")]
    if lessons != list(range(1, 109)):
        raise RuntimeError("课程目录边界不完整，不能发布：" + repr(sorted(set(range(1, 109)) - set(lessons))))
    db.execute("INSERT INTO metadata VALUES('source_extraction_complete','true')")
    db.commit()
    db.close()
    final = output / "graph.sqlite"
    if final.exists():
        raise RuntimeError("已有正式图谱，必须使用新的输出版本目录")
    temporary.replace(final)
    manifest = {"schema_version": "1.1.0", "graph_version": "0.1.0-source", "built_at": now, "stage": "source_extracted_semantic_review_pending", "sources": source_manifest, "counts": counts, "review_policy": "reviewed_only_by_default", "fixed_corpus": True}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(j({"complete": True, "counts": counts, "lessons": len(lessons)}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    extract([args.source_dir / "volume_1.pdf", args.source_dir / "volume_2.pdf"], args.output)
