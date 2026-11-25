"""Hash immutable public release files. Mutable market/health receipts excluded."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
SKIP={'release_manifest.json','data/latest.json','data/health.json','artifacts/release/release_review.json'}
def main():
    files=[]
    for p in sorted(R.rglob('*')):
        rel=p.relative_to(R).as_posix()
        if not p.is_file() or any(x in p.relative_to(R).parts for x in ['.git','node_modules','__pycache__','outputs']) or rel in SKIP or p.suffix=='.pyc' or rel.endswith('.inspect.ndjson'):continue
        files.append(dict(path=rel,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size))
    (R/'release_manifest.json').write_text(json.dumps(dict(version='1.0.0',policy='Immutable public files; market/health receipts and mutable publication review excluded',files=files),indent=2)+'\n')
    print('Manifest:',len(files),'files')
if __name__=='__main__':main()
