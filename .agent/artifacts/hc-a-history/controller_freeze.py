import hashlib,json,subprocess,tempfile,time,sys
from pathlib import Path
from datetime import datetime,timezone
root=Path.cwd(); art=root/'.agent/artifacts/hc-a-history'; start=datetime.now(timezone.utc).isoformat(); tick=time.monotonic()
paths=subprocess.check_output(['git','diff','--cached','--name-only','-z']).decode().split('\0'); paths=[p for p in paths if p and not p.startswith('.agent/')]
entries=[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'index_blob':subprocess.check_output(['git','rev-parse',':'+p]).decode().strip()} for p in paths]
x={'base_sha':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'branch':subprocess.check_output(['git','branch','--show-current']).decode().strip(),'files':entries,'excluded':'.agent bookkeeping; source, tests, docs and all new research are bound'}
x['candidate_sha256']=hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
(art/'CANDIDATE.json').write_text(json.dumps(x,indent=2)+'\n')
retained=[p for p in subprocess.check_output(['git','ls-files','-z','research/pre-rfp-history']).decode().split('\0') if p]
with tempfile.TemporaryDirectory(prefix='trailforge-byte-proof-') as tmp:
 subprocess.run(['git','-c','core.autocrlf=true','checkout-index','--prefix='+Path(tmp).as_posix()+'/','--stdin','-z'],input=('\0'.join(retained)+'\0').encode(),check=True)
 for p in retained:
  raw=(root/p).read_bytes(); assert raw==(Path(tmp)/p).read_bytes(),p
  blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  assert blob==subprocess.check_output(['git','rev-parse',':'+p]).decode().strip(),p
proof={'status':'PASS','retained_files':len(retained),'working_index_fresh_checkout_bytes':'IDENTICAL','core_autocrlf':True,'candidate_sha256':x['candidate_sha256'],'started_at_utc':start,'finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':round(time.monotonic()-tick,3)}
(art/'CONTROLLER_PORTABILITY.json').write_text(json.dumps(proof,indent=2)+'\n'); print(json.dumps(proof))
