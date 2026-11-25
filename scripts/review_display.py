"""Notebook display helpers; output is compatible with IPython display bundles."""
from pathlib import Path
from html import escape
import base64
R=Path(__file__).resolve().parents[1]
def table(headers,rows):
    cell=lambda x:escape(f'{x:.8g}' if isinstance(x,float) else str(x))
    h='<table><thead><tr>'+''.join('<th>'+cell(x)+'</th>' for x in headers)+'</tr></thead><tbody>'
    h+=''.join('<tr>'+''.join('<td>'+cell(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
    return {'text/html':h}
def figure(name):return {'image/png':base64.b64encode((R/'artifacts/release/figures'/(name+'.png')).read_bytes()).decode()}
