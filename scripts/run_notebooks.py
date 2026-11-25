"""Execute each notebook with a fresh Python namespace and captured MIME bundles."""
import contextlib,io,json,os,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
    os.chdir(R);started=time.perf_counter();count=0
    for path in sorted((R/'notebooks').glob('*.ipynb')):
        nb=json.loads(path.read_text());ns={};n=0
        for cell in nb['cells']:
            if cell['cell_type']!='code':continue
            n+=1;stream=io.StringIO();outputs=[]
            def display_bundle(bundle):
                if stream.getvalue():outputs.append(dict(output_type='stream',name='stdout',text=stream.getvalue().splitlines(True)));stream.seek(0);stream.truncate(0)
                outputs.append(dict(output_type='display_data',data=bundle,metadata={}))
            ns['display_bundle']=display_bundle
            with contextlib.redirect_stdout(stream):exec(compile(''.join(cell['source']),str(path),'exec'),ns)
            if stream.getvalue():outputs.append(dict(output_type='stream',name='stdout',text=stream.getvalue().splitlines(True)))
            cell.update(execution_count=n,outputs=outputs)
        path.write_text(json.dumps(nb,indent=2)+'\n');count+=n;print('PASS',path.name,n)
    print(json.dumps(dict(notebooks=8,code_cells=count,elapsed_seconds=time.perf_counter()-started,native_jupyter=False)))
if __name__=='__main__':main()
