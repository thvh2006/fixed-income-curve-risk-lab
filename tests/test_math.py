import unittest,sys
from pathlib import Path
from datetime import date
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from curve_lab.bonds import Bond,add_months
from curve_lab.curves import Curve,bootstrap,par_rate,TENORS,KEYS
from curve_lab.risk import bond_risk,carry_bridge,hedge
from curve_lab.forecast import predict

class BondTests(unittest.TestCase):
    def setUp(self):self.s=date(2025,12,31);self.b=Bond(date(2030,12,31),.04)
    def test_par(self):self.assertAlmostEqual(self.b.yield_price(self.s,.04),100,10)
    def test_zero(self):self.assertAlmostEqual(Bond(date(2030,12,31),0).yield_price(self.s,.05),100/1.025**10,10)
    def test_roundtrip(self):
        for y in [-.01,0,.03,.2]:self.assertAlmostEqual(self.b.ytm(self.s,self.b.yield_price(self.s,y)),y,10)
    def test_clean_dirty(self):
        s=date(2026,2,28);ai=self.b.accrued(s);self.assertAlmostEqual(ai,2*59/181);self.assertAlmostEqual((102-ai)+ai,102)
    def test_coupon_day(self):self.assertEqual(self.b.accrued(date(2026,6,30)),0)
    def test_eom_schedule(self):self.assertEqual(self.b.cashflows(self.s)[0]['date'],'2026-06-30')
    def test_maturity_exclusion(self):
        with self.assertRaises(ValueError):self.b.cashflows(self.b.maturity)
    def test_leap(self):self.assertEqual(add_months(date(2024,2,29),12,True),date(2025,2,28))
    def test_analytic_duration(self):
        p=self.b.yield_price(self.s,.04);h=1e-5;r=self.b.yield_risk(self.s,.04)
        self.assertAlmostEqual((self.b.yield_price(self.s,.04-h)-self.b.yield_price(self.s,.04+h))/(2*h*p),r['modified'],7)
    def test_convexity(self):
        p=self.b.yield_price(self.s,.04);h=1e-4;r=self.b.yield_risk(self.s,.04)
        self.assertAlmostEqual((self.b.yield_price(self.s,.04-h)+self.b.yield_price(self.s,.04+h)-2*p)/(h*h*p),r['convexity'],4)
    def test_invalid_yield(self):
        with self.assertRaises(ValueError):self.b.yield_price(self.s,-2)

class CurveTests(unittest.TestCase):
    def setUp(self):self.par=np.array([.04,.04,.039,.039,.04,.042,.043,.046,.045]);self.c=bootstrap(self.par)
    def test_reprice(self):
        for t,p in zip(TENORS,self.par):self.assertAlmostEqual(par_rate(self.c,t),p,12)
    def test_negative_rates(self):
        c=bootstrap(np.full(9,-.005));self.assertGreater(c.df(30),1)
    def test_discount_positive(self):self.assertTrue(np.all(self.c.df(np.arange(0,30,.1))>0))
    def test_no_extrapolation(self):
        with self.assertRaises(ValueError):self.c.df(31)
    def test_missing(self):
        with self.assertRaises(ValueError):bootstrap([np.nan]*9)
    def test_zero_is_not_par(self):self.assertGreater(abs(self.c.zero(30)-self.par[-1]),1e-5)
    def test_key_sum(self):
        r=bond_risk(Bond(date(2030,12,31),.04),date(2025,12,31),self.c)
        self.assertLess(abs(r['key_sum_residual']),1e-7)
    def test_bump_partition(self):
        b=self.c.bumped(np.full(6,.001));self.assertAlmostEqual(float(b.zero(7.3)-self.c.zero(7.3)),.001,12)
    def test_carry_reconciliation(self):
        b=Bond(date(2030,1,2),.04);r=carry_bridge(b,date(2025,1,2),date(2025,7,2),self.c,self.c)
        self.assertEqual(r['coupons'],2);self.assertLess(abs(r['reconciliation']),1e-12)
    def test_hedge_bounds(self):
        h=hedge([100,10],[[1,0],[0,1]],max_units=20)
        self.assertTrue(h['at_bound']);self.assertLessEqual(max(abs(x) for x in h['units']),20)

class TemporalTests(unittest.TestCase):
    def test_future_mutation(self):
        rng=np.random.default_rng(42);y=.04+np.cumsum(rng.normal(0,.0001,(230,9)),axis=0)
        p,_=predict(y[:200]);y[200:]+=10;q,_=predict(y[:200])
        for m in p:np.testing.assert_array_equal(p[m],q[m])
    def test_insufficient_training(self):
        with self.assertRaises(ValueError):predict(np.ones((10,9)))

if __name__=='__main__':unittest.main()
