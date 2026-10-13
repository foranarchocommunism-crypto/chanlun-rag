"""Pure, read-only structural/evidence checks for reviewed curation batches.

Passing this module does not prove semantic entailment or visual interpretation.
The submitted reviewer and substantive review notes remain necessary provenance.
"""
import gzip
import hashlib
import json
import math
import re
from functools import lru_cache
from pathlib import Path


RELATIONS = ("composed_of", "defines", "distinguishes", "illustrates", "qualifies", "related", "requires")
AUTHOR_ROLES = ("author_body", "author_reply", "author_commentary")
REQUIRED = ("id", "text", "kind", "conditions", "exceptions", "concepts", "review_note", "reviewer", "evidence", "importance_level", "importance_reason")
OPTIONAL = ("ambiguity_status", "derivation", "figure_review_note", "relations")


def j(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def nonblank(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + " 必须是非空字符串")


def string_list(value, field, nonempty=False, unique=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(field + " 必须是" + ("非空" if nonempty else "") + "字符串数组")
    for item in value:
        nonblank(item, field + "[]")
    if unique and len(set(value)) != len(value):
        raise ValueError(field + " 不允许重复项")


def validate_shape(record):
    if not isinstance(record, dict):
        raise ValueError("JSONL每行必须是对象")
    missing = set(REQUIRED) - record.keys()
    if missing:
        raise ValueError("缺少字段：" + ",".join(sorted(missing)))
    unknown = record.keys() - set(REQUIRED + OPTIONAL)
    if unknown:
        raise ValueError("未知字段：" + ",".join(sorted(unknown)))
    for field in ("id", "text", "review_note", "reviewer", "importance_reason"):
        nonblank(record[field], field)
    if record["reviewer"] == "GPT-6.1 Sol xhigh / source curation":
        raise ValueError("新记录必须明确实际复核执行者，不能沿用导入器默认标签")
    if record["kind"] not in ("explicit", "inferred"):
        raise ValueError("未知命题类型")
    if type(record["importance_level"]) is not int or record["importance_level"] not in (1, 2, 3, 4):
        raise ValueError("重要性必须是1-4的整数；boolean不是等级")
    string_list(record["conditions"], "conditions")
    string_list(record["exceptions"], "exceptions")
    string_list(record["concepts"], "concepts", nonempty=True, unique=True)
    if "ambiguity_status" in record:
        nonblank(record["ambiguity_status"], "ambiguity_status")
    if "figure_review_note" in record:
        nonblank(record["figure_review_note"], "figure_review_note")
    derivation = record.get("derivation", {})
    if not isinstance(derivation, dict):
        raise ValueError("derivation必须是对象")
    if record["kind"] == "inferred":
        string_list(derivation.get("supporting_claim_ids"), "supporting_claim_ids", nonempty=True, unique=True)
        nonblank(derivation.get("explanation"), "explanation")
    elif derivation:
        raise ValueError("explicit不能携带推论前提；请正确声明kind")
    citations = record["evidence"]
    if not isinstance(citations, list) or not citations:
        raise ValueError("evidence必须是非空对象数组")
    for citation in citations:
        if not isinstance(citation, dict) or set(citation) - {"passage_id", "quote", "quote_start", "figure_ids"}:
            raise ValueError("证据字段或类型不合法")
        nonblank(citation.get("passage_id"), "passage_id")
        nonblank(citation.get("quote"), "quote")
        if "quote_start" in citation and (type(citation["quote_start"]) is not int or citation["quote_start"] < 0):
            raise ValueError("quote_start必须是非负码点整数")
        string_list(citation.get("figure_ids", []), "figure_ids", unique=True)
        if citation.get("figure_ids") and not record.get("figure_review_note"):
            raise ValueError("关联配图必须单独记录实际视觉复核及来源边界")
    relations = record.get("relations", [])
    if not isinstance(relations, list):
        raise ValueError("relations必须是数组")
    for relation in relations:
        if not isinstance(relation, dict) or set(relation) != {"source", "target", "type"}:
            raise ValueError("关系必须包含source/target/type且没有未知字段")
        nonblank(relation["source"], "relation.source")
        nonblank(relation["target"], "relation.target")
        if relation["type"] not in RELATIONS:
            raise ValueError("未知关系类型")


def validate_records(db, root, records):
    """Return prepared anchors; do not write to the database or filesystem."""
    root = Path(root).resolve()
    prepared, errors, seen = [], [], set()
    labels = {}
    for row in db.execute("SELECT id,label,aliases FROM concepts"):
        for label in [row["label"]] + json.loads(row["aliases"]):
            if label in labels and labels[label] != row["id"]:
                raise ValueError("概念label/alias解析有歧义：" + label)
            labels[label] = row["id"]

    def concept_id(label):
        return labels.get(label, "concept-" + digest(label))

    @lru_cache(maxsize=16)
    def geometry(document_id, page_number):
        page = db.execute("SELECT pg.*,d.page_count FROM pages pg JOIN documents d ON d.id=pg.document_id WHERE pg.document_id=? AND pg.pdf_page=?", (document_id, page_number)).fetchone()
        if not page or not 1 <= page_number <= page["page_count"]:
            raise ValueError("来源页缺失或越界")
        path = (root / page["geometry_path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("geometry资源超出数据包")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            geo = json.load(stream)
        if abs(geo["width"] - page["width"]) > 0.01 or abs(geo["height"] - page["height"]) > 0.01:
            raise ValueError("geometry页面尺寸不一致")
        return geo

    for record, path, line in records:
        cid = record.get("id") if isinstance(record, dict) else None
        try:
            validate_shape(record)
            if cid in seen:
                raise ValueError("批次内命题ID重复")
            seen.add(cid)
            anchors = []
            for index, citation in enumerate(record["evidence"]):
                passage = db.execute("SELECT * FROM passages WHERE id=?", (citation["passage_id"],)).fetchone()
                if not passage:
                    raise ValueError("原文段落不存在：" + citation["passage_id"])
                if passage["role"] not in AUTHOR_ROLES or passage["speaker"] != "缠中说禅":
                    raise ValueError("引用身份未确认是作者：" + passage["id"])
                if passage["role"] == "author_commentary":
                    note = record["review_note"]
                    if not re.search(r"语境[：:]\s*\S", note) or not re.search(r"适用条件[：:]\s*\S", note):
                        raise ValueError("作者解盘技术解释需在review_note中分别记录语境与适用条件")
                if passage["unit_id"]:
                    unit = db.execute("SELECT * FROM units WHERE id=?", (passage["unit_id"],)).fetchone()
                    if not unit or unit["document_id"] != passage["document_id"] or not unit["start_page"] <= passage["pdf_page"] <= unit["end_page"] or unit["kind"] == "compiler_appendix":
                        raise ValueError("段落课程/文档身份不一致或属于未核汇编后记")
                quote = citation["quote"]
                if "quote_start" not in citation and passage["text"].count(quote) > 1:
                    raise ValueError("重复引文必须明确quote_start")
                begin = citation.get("quote_start", passage["text"].find(quote))
                end = begin + len(quote)
                if begin < 0 or passage["text"][begin:end] != quote:
                    raise ValueError("引文不是指定码点区间的精确连续子串")
                mapping = json.loads(passage["normalized_map"])
                raw_indices = json.loads(passage["source_char_indices"])
                if not isinstance(mapping, list) or len(mapping) != len(passage["text"]) or not isinstance(raw_indices, list):
                    raise ValueError("归一文本映射结构或长度错误")
                geo = geometry(passage["document_id"], passage["pdf_page"])
                chars = geo["chars"]
                if any(type(i) is not int or i < 0 or i >= len(chars) for i in mapping + raw_indices):
                    raise ValueError("PDF字符索引无效")
                selected = mapping[begin:end]
                if not set(selected) <= set(raw_indices) or "".join(chars[i][0] for i in selected) != quote:
                    raise ValueError("PDF字符重建与引文不一致")
                boxes, last_top = [], None
                for char_index in dict.fromkeys(selected):
                    char = chars[char_index]
                    if len(char) != 5 or not isinstance(char[0], str):
                        raise ValueError("PDF字符几何结构错误")
                    _, x0, top, x1, bottom = char
                    if any(type(v) not in (int, float) or not math.isfinite(v) for v in char[1:]) or not (-1 <= x0 <= x1 <= geo["width"] + 1 and -1 <= top <= bottom <= geo["height"] + 1):
                        raise ValueError("PDF字符坐标无效或越界")
                    if last_top is None or abs(top - last_top) > 3:
                        boxes.append([x0, top, x1, bottom])
                        last_top = top
                    else:
                        b = boxes[-1]
                        b[:] = [min(b[0], x0), min(b[1], top), max(b[2], x1), max(b[3], bottom)]
                figure_ids = citation.get("figure_ids", [])
                origins = {}
                for fid in figure_ids:
                    figure = db.execute("SELECT * FROM figures WHERE id=?", (fid,)).fetchone()
                    if not figure or figure["document_id"] != passage["document_id"]:
                        raise ValueError("配图不存在或来自另一文档：" + fid)
                    origins[fid] = figure["origin_status"]
                span = {"document_id": passage["document_id"], "pdf_page": passage["pdf_page"], "char_indices": selected, "boxes": boxes, "coordinate_system": "pdf_points_top_left"}
                anchors.append({"id": "evidence-" + digest(cid + ":" + str(index) + ":" + passage["id"]), "passage_id": passage["id"], "quote": quote, "begin": begin, "end": end, "span": span, "figure_ids": figure_ids, "source_role": passage["role"], "figure_origins": origins})
            resolved = list(dict.fromkeys(concept_id(label) for label in record["concepts"]))
            for relation in record.get("relations", []):
                if concept_id(relation["source"]) == concept_id(relation["target"]):
                    raise ValueError("关系不允许自环或同义概念自环")
                if any(concept_id(relation[field]) not in resolved for field in ("source", "target")):
                    raise ValueError("关系端点须在本命题的概念归属中登记")
            old = db.execute("SELECT * FROM claims WHERE id=?", (cid,)).fetchone()
            if old and old["review_status"] == "reviewed":
                expected = {"text": record["text"], "kind": record["kind"], "conditions": record["conditions"], "exceptions": record["exceptions"], "concept_ids": resolved, "derivation": record.get("derivation", {})}
                before = {k: json.loads(old[k]) if k in ("conditions", "exceptions", "concept_ids", "derivation") else old[k] for k in expected}
                old_anchors = sorted((r["passage_id"], r["quote"], r["quote_start"], j(json.loads(r["figure_ids"]))) for r in db.execute("SELECT * FROM evidence WHERE claim_id=?", (cid,)))
                new_anchors = sorted((a["passage_id"], a["quote"], a["begin"], j(a["figure_ids"])) for a in anchors)
                if before != expected or old_anchors != new_anchors:
                    raise ValueError("禁止隐式覆盖已复核命题或证据；需先做显式修订和依赖重审：" + cid)
            prepared.append({"record": record, "path": path, "line": line, "anchors": anchors, "concept_ids": resolved})
        except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as error:
            errors.append({"id": cid, "file": str(path), "line": line, "error": str(error)})
    if errors:
        raise ValueError(j({"batch_rejected_atomically": True, "errors": errors}))
    current = {r["id"]: dict(r) for r in db.execute("SELECT id,kind,review_status,derivation FROM claims")}
    for item in prepared:
        r = item["record"]
        current[r["id"]] = {"id": r["id"], "kind": r["kind"], "review_status": "reviewed", "derivation": j(r.get("derivation", {}))}
    edges = {}
    for cid, record in current.items():
        if record["review_status"] != "reviewed" or record["kind"] != "inferred":
            continue
        derivation = json.loads(record["derivation"])
        string_list(derivation.get("supporting_claim_ids"), "推论前提", nonempty=True, unique=True)
        nonblank(derivation.get("explanation"), "推论说明")
        parents = derivation["supporting_claim_ids"]
        for parent in parents:
            if parent not in current or current[parent]["review_status"] != "reviewed":
                raise ValueError("推论前提不存在或未复核：" + parent)
        edges[cid] = parents
    done, active = set(), set()

    def visit(cid):
        if cid in active:
            raise ValueError("推论前提形成循环：" + cid)
        if cid in done:
            return
        active.add(cid)
        for parent in edges.get(cid, []):
            visit(parent)
        active.remove(cid)
        done.add(cid)

    for cid in edges:
        visit(cid)
    return prepared
