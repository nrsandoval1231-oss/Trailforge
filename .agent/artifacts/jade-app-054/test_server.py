from pathlib import Path
import sys,hashlib,sqlite3,json
root=Path.cwd();sys.path.insert(0,str(root/'src'))
from athena_procurement_arena.operator import Store,blank,Server
path=root/'.agent/artifacts/jade-app-054/synthetic.sqlite3'
store=Store(path)
if not store.listing():
    doc=blank('SYNTHETIC UI validation campus','TEST ONLY','Construction')
    store.save(doc)
    store.save(blank('SYNTHETIC commissioning project','TEST ONLY','Commissioning'))
with Server(store,8770) as server:
    print(server.origin,flush=True)
    server.serve_forever()
