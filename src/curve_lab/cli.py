import argparse,runpy
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description='Rebuild the frozen educational curve research');p.add_argument('command',choices=['build']);p.parse_args()
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/build.py'),run_name='__main__')
