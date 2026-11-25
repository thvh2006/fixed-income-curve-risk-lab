import sys,tempfile,json,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'src'))
from refresh_market import publish
from curve_lab.data import load_history
from curve_lab.forecast import evaluate
from curve_lab.curves import fit_nelson_siegel
import numpy as np

class OperationalTests(unittest.TestCase):
    def test_failed_refresh_retains_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);publish((R/'data/raw/treasury_par_2025.csv').read_bytes(),2025,p,'official fixture source');before=(p/'latest.json').read_bytes()
            with self.assertRaises(Exception):publish(b'Date,6 Mo\n12/31/2025,not-a-rate\n',2025,p,'broken fixture')
            self.assertEqual(before,(p/'latest.json').read_bytes());self.assertEqual(json.loads((p/'health.json').read_text())['status'],'failed')
    def test_regression_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);publish((R/'data/raw/treasury_par_2025.csv').read_bytes(),2025,p,'fixture');before=(p/'latest.json').read_bytes()
            with self.assertRaises(ValueError):publish((R/'data/raw/treasury_par_2024.csv').read_bytes(),2024,p,'older fixture')
            self.assertEqual(before,(p/'latest.json').read_bytes())
    def test_future_curve_mutation_evaluator(self):
        rows,_=load_history(R);original=evaluate(rows);mutated=[dict(date=r['date'],par=[x+(.01 if r['date']>'2025-08-01' else 0) for x in r['par']]) for r in rows];changed=evaluate(mutated)
        checked=0
        for a,b in zip(original['origins'],changed['origins']):
            if a['target']<='2025-08-01':self.assertEqual(a,b);checked+=1
        self.assertGreater(checked,20)
    def test_ns_challenger_is_finite(self):
        rows,_=load_history(R);curve,fit=fit_nelson_siegel(np.array(rows[-1]['par']))
        self.assertTrue(fit['success']);self.assertLess(fit['rmse_bp'],10);self.assertTrue(np.all(curve.d>0))

if __name__=='__main__':unittest.main()
