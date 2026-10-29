"""Prepare a small binary transfer, then publish the full already-tested user archive."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[1]
repo = 'foranarchocommunism-crypto/chanlun-rag'
version = '0.4.2'
tag = 'v' + version
transport = root / 'archives/docs-publication-0.4.2'
transport.mkdir(exist_ok=True)
manifest_path = transport / 'documentation-publication.json'
state_file = root / 'source/build/publication-background-state.json'
state = {'version': version, 'status': 'running'}
def save(step, **extra):
    state.update(step=step, updated_at=datetime.now(timezone.utc).isoformat(), **extra)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(state, ensure_ascii=False), flush=True)
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def run(args):
    while True:
        result = subprocess.run(args, cwd=root, capture_output=True)
        if result.returncode == 0: return result.stdout.decode('utf-8').strip()
        detail = result.stderr.decode('utf-8', errors='replace')
        network = any(x in detail.lower() for x in ['timeout','connection','error connecting','eof','rate limit','context deadline','request canceled']) or bool(re.search(r'http 5\d\d', detail.lower()))
        if not network: raise RuntimeError(detail)
        save('waiting_for_network', retry_seconds=60)
        time.sleep(60)
def gh(*args): return run(['gh', *args])
def release():
    return next((r for r in json.loads(gh('api', 'repos/' + repo + '/releases')) if r['tag_name'] == tag), None)

try:
    if sys.argv[1] == 'prepare':
        verified = json.loads((root / '验收记录/0.4.2-全新解压运行验证.json').read_text(encoding='utf-8'))
        onboarding = json.loads((root / '验收记录/0.4.2-本地指南与连接验证.json').read_text(encoding='utf-8'))
        assert verified['passed'] and onboarding['passed']
        work = root / 'source/build/docs-delta'
        for d in ['base', 'target', 'apply']: (work / d).mkdir(parents=True, exist_ok=True)
        old = root / 'archives/chanlun-rag-0.4.1-windows-x64.zip'
        new = root / 'archives/chanlun-rag-0.4.2-windows-x64.zip'
        assert sha(old) == '957abe459d0e227ff93cdfe23c3caf8a2e30c39853796520e4dc17ddd7c300f1'
        shutil.copy2(old, work / 'base/runtime.zip'); shutil.copy2(new, work / 'target/runtime.zip')
        diff = subprocess.run(['git','-c','core.bigFileThreshold=2g','diff','--no-index','--binary','--full-index','--no-ext-diff','--no-textconv','base/runtime.zip','target/runtime.zip'], cwd=work, capture_output=True)
        assert diff.returncode == 1, diff.stderr
        patch = transport / 'documentation-update.patch'; patch.write_bytes(diff.stdout)
        assert patch.stat().st_size < 64 * 1024 * 1024, 'Unexpectedly large delta; do not upload silently'
        shutil.copy2(old, work / 'apply/runtime.zip')
        subprocess.run(['git','apply','--binary','-p2','--directory=source/build/docs-delta/apply',str(patch)], cwd=root, check=True)
        assert sha(work / 'apply/runtime.zip') == sha(new)
        m = {'repository':repo,'tag':tag,'tag_commit':run(['git','rev-parse',tag]),
             'base':{'tag':'v0.4.1','name':old.name,'sha256':sha(old)},
             'target':{'name':new.name,'bytes':new.stat().st_size,'sha256':sha(new)},
             'patch':{'name':patch.name,'bytes':patch.stat().st_size,'sha256':sha(patch)},
             'local_binary_patch_roundtrip_passed':True}
        manifest_path.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'target_bytes':new.stat().st_size,'transfer_bytes':patch.stat().st_size,'exact_roundtrip':True}),flush=True)
    elif sys.argv[1] == 'publish':
        m=json.loads(manifest_path.read_text(encoding='utf-8'))
        save('uploading_documentation_delta', transfer_bytes=m['patch']['bytes'])
        current=release()
        if current is None:
            gh('release','create',tag,'--repo',repo,'--verify-tag','--draft','--title','缠论RAG 0.4.2｜本地AI安装指南版','--notes-file','docs/release-0.4.2.md')
            current=release()
        if current['draft']:
            active=json.loads(gh('run','list','--repo',repo,'--workflow','publish-docs.yml','--limit','1','--json','databaseId,status,url'))
            if not active or active[0]['status']=='completed':
                gh('release','upload',tag,str(transport / m['patch']['name']),str(manifest_path),'--repo',repo,'--clobber')
                save('server_restoring_verified_zip')
                gh('workflow','run','publish-docs.yml','--repo',repo,'--ref','main','-f','tag='+tag,'-f','manifest_sha256='+sha(manifest_path))
                time.sleep(8)
                active=json.loads(gh('run','list','--repo',repo,'--workflow','publish-docs.yml','--limit','1','--json','databaseId,status,url'))
            assert active
            run_id=str(active[0]['databaseId']); save('waiting_for_server_verification',workflow_url=active[0]['url'])
            while True:
                job=json.loads(gh('run','view',run_id,'--repo',repo,'--json','status,conclusion,url'))
                if job['status']=='completed':
                    assert job['conclusion']=='success', job['url']
                    break
                time.sleep(30)
        current=release(); assert not current['draft']
        asset=next(a for a in current['assets'] if a['name']==m['target']['name'])
        assert asset['digest']=='sha256:'+m['target']['sha256'] and asset['size']==m['target']['bytes']
        assert set(a['name'] for a in current['assets'])=={m['target']['name'],m['target']['name']+'.sha256'}
        report={'passed':True,'version':version,'release_url':current['html_url'],'archive_sha256':m['target']['sha256'],'workflow_url':state.get('workflow_url'),'local_guide_in_full_zip':True,'exact_binary_patch_verified':True}
        (root/'验收记录/0.4.2-GitHub发布核对.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        shutil.copy2(manifest_path,root/'验收记录/0.4.2-发布差异清单.json')
        status=json.loads((root/'发布状态.json').read_text(encoding='utf-8'))
        status.update(status='released',version=version,release_tag=tag,archive_sha256=m['target']['sha256'],release_url=current['html_url'],published_at=current['published_at'],publication_receipt='验收记录/0.4.2-GitHub发布核对.json',receipt='验收记录/0.4.2-ZIP与全新解压.json',local_install_guide_included=True)
        (root/'发布状态.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        save('complete',status='complete',release_url=current['html_url'])
    else: raise SystemExit('Use prepare or publish')
except Exception as error:
    save('needs_attention',status='failed',error=type(error).__name__+': '+str(error))
    raise
