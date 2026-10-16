#!/usr/bin/env python3
"""Small algebra/holdout gates; no solvers and no fabricated measurements."""
import unittest
import numpy as np
import analyze_models as m


def rows(function, sizes=m.SIZES):
    return [dict(n=n, N=n*33, mean_ns=function(n*33)) for n in sizes for _ in range(3)]


class Models(unittest.TestCase):
    def test_origin_closed_form(self):
        sample=rows(lambda N: 25*N + 1300)
        for model in m.GOOGLE:
            fit=m.fit(sample,model)
            N=np.array([r['N'] for r in sample],dtype=float)
            y=np.array([r['mean_ns'] for r in sample])
            x=m.feature(model,N)
            expected=x * np.dot(x,y)/np.dot(x,x)
            np.testing.assert_allclose(m.predict(fit,sample),expected,rtol=1e-13)

    def test_affine_recovers_intercept_and_slope(self):
        for intercept in (-2000,2000):
            sample=rows(lambda N: intercept+3*N)
            fitted=m.fit(sample,'affine_N')
            self.assertAlmostEqual(m.parameters(fitted)['intercept_ns'],intercept,places=6)
            self.assertAlmostEqual(m.parameters(fitted)['linear_slope_ns_per_N'],3,places=10)
            np.testing.assert_allclose(m.predict(fitted,sample),[r['mean_ns'] for r in sample],rtol=1e-12)

    def test_hinge_and_unidentified_window(self):
        knot=65536*33
        sample=rows(lambda N: 9 + 2*N + 5*max(N-knot,0))
        fitted=m.fit(sample,'hinge_65536')
        self.assertAlmostEqual(m.parameters(fitted)['hinge_delta_ns_per_N'],5,places=10)
        np.testing.assert_allclose(m.predict(fitted,sample),[r['mean_ns'] for r in sample],rtol=1e-10)
        self.assertIsNone(m.fit(sample[:18],'hinge_65536'))
        self.assertIsNone(m.fit(sample[-9:],'hinge_65536'))

    def test_relative_objective_closed_form_and_negatives_retained(self):
        sample=rows(lambda N: N**1.2)
        fitted=m.fit(sample,'N',True)
        xs=np.array([r['N']/r['mean_ns'] for r in sample])
        c=np.sum(xs)/np.dot(xs,xs)
        np.testing.assert_allclose(m.predict(fitted,sample),[c*r['N'] for r in sample],rtol=1e-13)
        stats=m.metrics(sample,-np.ones(len(sample)))
        self.assertEqual(stats['nonpositive_predictions'],len(sample))

    def test_blocked_fold_is_size_blocked_not_repetition_split(self):
        for train,test in m.FOLDS.values():
            self.assertFalse(set(train)&set(test))
            self.assertLess(max(train),min(test))
            self.assertEqual(tuple(train),m.SIZES[:len(train)])


if __name__=='__main__': unittest.main()
