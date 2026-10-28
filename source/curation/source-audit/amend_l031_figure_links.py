"""Explicitly repair five figure attachments omitted by a copied index guard.

Original publication bytes, claim rows, source rows and historical reviews stay
unchanged. Only the five listed evidence.figure_ids fields may change. New review
rows record the before/after attachment and actual visual provenance note.
"""
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = Path(__file__).resolve().parents[2]
KB = AGENT.parent / 'shared-knowledge/v0.1.0'
AUDIT = Path(__file__).resolve().parent
BASE = '0.1.0-review-77ca557fa0f5'
DOC = 'volume_1-a53e99c37ca5'
EXPECTED = {
    'long-pressure-free-funds-and-leverage-story': (219, 1),
    'feb15-center-1048-1129-third-buy-1413': (224, 1),
    'feb16-1405-divergence-and-later-selloff-case': (226, 1),
    'weekly-three-legs-original-explicitly-qualified': (230, 1),
    'weekly-center-first-daily-then-expand-case': (230, 1),
}
sys.path.insert(0, str(AGENT / 'tools'))
from curation_contract import digest, j, validate_records
from graph_release import refresh_version, update_manifest


def rows(db, table):
    return {r['id']: dict(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY id')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    batch = AGENT / 'curation/upper/c_stage_l031.reviewed.jsonl'
    original_hash = sha(batch)
    assert original_hash == '97710084a9065edbbd295d5128aa6fb4670cd3f5b9fd00b38a26cbd12c1a9231'
    source = {r['id']: r for r in map(json.loads, batch.read_text(encoding='utf-8').splitlines()) if r}
    amended_path = AGENT / 'curation/upper/c_stage_l031.figure-links-amended.jsonl'
    assert not amended_path.exists(), 'Do not replay a published amendment'
    db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]) == BASE
        before = {t: rows(db, t) for t in ['documents', 'units', 'pages', 'passages', 'figures', 'concepts', 'claims', 'evidence', 'relations', 'reviews']}
        assert len([r for r in before['claims'].values() if r['review_status'] == 'reviewed']) == 2259
        amended, changes = [], []
        for slug, (page, number) in EXPECTED.items():
            cid = 'upper-l031-c-stage-' + slug
            record = json.loads(j(source[cid]))
            citation = record['evidence'][0]
            figure_id = f'{DOC}-p{page:04d}-fig{number}'
            assert citation.get('figure_ids') == []
            evidence = next(r for r in before['evidence'].values() if r['claim_id'] == cid and r['passage_id'] == citation['passage_id'])
            assert json.loads(evidence['figure_ids']) == []
            figure = before['figures'][figure_id]
            assert figure['document_id'] == DOC
            citation['figure_ids'] = [figure_id]
            record['reviewer'] = 'Codex 主代理 / 第31课配图关联显式修复'
            record['figure_review_note'] = '原批实际已查看整页及完整图；本次修复丢失的关联，不改文字语义：' + figure['note'] + '。图来源状态保持，文字独立支持命题，配图不作唯一证明。'
            amended.append(record)
            changes.append({'claim_id': cid, 'evidence_id': evidence['id'], 'figure_ids_before': [], 'figure_ids_after': [figure_id],
                            'figure_origin': figure['origin_status'], 'figure_review_note': record['figure_review_note']})
        # Full contract check against a private in-memory snapshot; temporarily
        # release these five statuses only inside that disposable copy, since
        # the normal importer correctly prohibits implicit evidence overwrite.
        temporary = sqlite3.connect(':memory:'); temporary.row_factory = sqlite3.Row
        try:
            db.backup(temporary)
            temporary.executemany("UPDATE claims SET review_status='pending' WHERE id=?", [(r['id'],) for r in amended])
            prepared = validate_records(temporary, KB, [(r, amended_path, i + 1) for i, r in enumerate(amended)])
            assert len(prepared) == 5
        finally:
            temporary.close()
        now = datetime.now(timezone.utc)
        backup = KB.parent / 'backups' / (now.strftime('%Y%m%dT%H%M%S%fZ') + '-l031-figure-links')
        backup.mkdir(parents=True, exist_ok=False)
        with sqlite3.connect(backup / 'graph.sqlite') as target:
            db.backup(target)
        shutil.copy2(KB / 'manifest.json', backup / 'manifest.json')
    finally:
        db.close()
    amended_path.write_text(''.join(j(r) + '\n' for r in amended), encoding='utf-8')
    reason = '复制模板时把证据索引i==0误替换为i==6，导致5条有视觉记录的命题漏配图；只补关联，原批字节和历史复核保留。'
    db = sqlite3.connect(KB / 'graph.sqlite'); db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON'); db.execute('BEGIN IMMEDIATE')
        assert json.loads(db.execute("SELECT value FROM metadata WHERE key='graph_version'").fetchone()[0]) == BASE
        for record, change in zip(amended, changes):
            eid = change['evidence_id']
            assert dict(db.execute('SELECT * FROM evidence WHERE id=?', (eid,)).fetchone()) == before['evidence'][eid]
            db.execute('UPDATE evidence SET figure_ids=? WHERE id=?', (j(change['figure_ids_after']), eid))
            checks = {'review_type': 'explicit_figure_attachment_amendment', 'reason': reason, 'change': change,
                      'base_graph_version': BASE, 'original_curation_file': batch.name, 'original_batch_sha256': original_hash,
                      'curation_file': amended_path.name, 'batch_sha256': sha(amended_path),
                      'claim_record_sha256': hashlib.sha256(j(record).encode()).hexdigest(),
                      'figure_review_note': record['figure_review_note'], 'figure_origins': {change['figure_ids_after'][0]: change['figure_origin']},
                      'independent_review_claimed': False, 'semantic_entailment_automatically_proven': False}
            db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)', ('review-' + digest(j(checks)), record['id'], record['reviewer'], now.isoformat(), j(checks), 'reviewed', reason))
        for table in ['documents', 'units', 'pages', 'passages', 'figures', 'concepts', 'claims', 'relations']:
            assert rows(db, table) == before[table], table
        expected_evidence = json.loads(j(before['evidence']))
        for change in changes:
            expected_evidence[change['evidence_id']]['figure_ids'] = j(change['figure_ids_after'])
        assert rows(db, 'evidence') == expected_evidence
        after_reviews = rows(db, 'reviews')
        assert all(after_reviews[k] == v for k, v in before['reviews'].items())
        assert len(after_reviews) == len(before['reviews']) + 5
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        version = refresh_version(db); db.commit()
        counts = {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in before}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    update_manifest(KB, version, counts=counts, updated_at=now.isoformat())
    assert sha(batch) == original_hash
    report = {'stage': 'C-explicit-figure-links-amendment', 'base_graph_version': BASE, 'graph_version': version,
              'reason': reason, 'changes': changes, 'backup_directory': str(backup), 'counts': counts,
              'original_batch_sha256_unchanged': original_hash, 'amended_records_sha256': sha(amended_path),
              'original_claim_rows_and_review_rows_unchanged': True, 'source_text_mapping_geometry_unchanged': True,
              'only_listed_five_evidence_figure_ids_changed': True, 'new_review_rows': 5,
              'full_contract_preflight_against_private_snapshot': 'passed', 'post_checks': 'pending'}
    (AUDIT / 'stage-c-l031-figure-links-amendment.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'graph_version': version, 'amended_evidence': len(changes), 'new_reviews': 5, 'backup_directory': str(backup)}, ensure_ascii=False))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
