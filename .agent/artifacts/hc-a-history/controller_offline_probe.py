"""Controller offline proof for the frozen HC-A-HISTORY candidate."""
import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
spec = importlib.util.spec_from_file_location('history_cli', ROOT / 'scripts/run_pre_rfp_history.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)
started = datetime.now(timezone.utc).isoformat()
tick = time.monotonic()
with tempfile.TemporaryDirectory(prefix='trailforge-history-controller-') as tmp:
    one, two = Path(tmp)/'one', Path(tmp)/'two'
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')) as blocked:
        first = cli.run(one)
        second = cli.run(two)
    assert first == second
    files = sorted(p.relative_to(one).as_posix() for p in one.rglob('*') if p.is_file())
    assert files == sorted(p.relative_to(two).as_posix() for p in two.rglob('*') if p.is_file())
    for p in files:
        assert (one/p).read_bytes() == (two/p).read_bytes(), p
    assert len(first['cases']) == 3
    assert all(c['historical_lead_seconds'] is None and c['lead_status'] == 'UNKNOWN' and not c['discovery_credit'] for c in first['cases'])
    surfaced = [c for c in first['cases'] if c['first_policy_surface_at'] != 'UNKNOWN']
    assert len(surfaced) == 1 and surfaced[0]['case_id'] == 'montauk-2021'
    assert datetime.fromisoformat(surfaced[0]['first_policy_surface_at']) == datetime.fromisoformat('2021-05-07T16:48:02+00:00')
    final = ROOT/'research/pre-rfp-history/results-controller-final'
    assert (one/'cohort.json').read_bytes() == (final/'cohort.json').read_bytes()
    assert (one/'report.md').read_bytes() == (final/'report.md').read_bytes()
    proof = {'status':'PASS','started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-tick,3),'case_count':3,'byte_identical_generated_files':len(files),'cohort_hash':first['cohort_hash'],'network_connect_attempts':blocked.call_count,'first_policy_surface_count':1,'buyer_actionable_count':0,'supported_lead_count':0,'files':[{'path':p,'sha256':hashlib.sha256((one/p).read_bytes()).hexdigest()} for p in files]}
artifacts = ROOT/'.agent/artifacts/hc-a-history'
imported = json.loads((artifacts/'PR7_IMPORT.json').read_text())
assert all(hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest() == x['sha256'] for x in imported['files'])
dirty = json.loads((artifacts/'DIRTY_WORK_PROTECTION.json').read_text())
assert all(hashlib.sha256((Path(dirty['root'])/x['path']).read_bytes()).hexdigest() == x['sha256'] for x in dirty['files'])
proof.update(imported_blobs_unchanged=len(imported['files']),original_dirty_files_unchanged=len(dirty['files']))
(artifacts/'CONTROLLER_RUNTIME.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k!='files'}))

