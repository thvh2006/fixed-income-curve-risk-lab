from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'artifacts/release/research.json').read_text())
h=(R/'dashboard/template.html').read_text().replace('/*STYLE*/',(R/'dashboard/style.css').read_text()).replace('/*DATA*/',json.dumps(d,separators=(',',':')).replace('</','<\\/')).replace('/*APP*/',(R/'dashboard/app.js').read_text())
(R/'index.html').write_text(h)
print('Built self-contained dashboard',len(h),'characters')
