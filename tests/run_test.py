import unittest
from pesting import *
from pymads import *
import exp_model
from numpy import array
import pymc
import mcmc 
from glob import glob
from shutil import rmtree


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.prob = read_pest('exp_model.pst')

    def test_forward(self):
        self.prob.forward()
        SSE =  sum( array(self.prob.get_residuals())**2 )
        self.assertEqual(SSE,0.0, 'SSE should be zero!')

    def test_calibrate(self):
        self.calib_prob = read_pest('exp_model_calib.pst')
        x,cov_x,infodic,mesg,ier = self.calib_prob.calibrate()
        SSE = sum( array(infodic['fvec'])**2)
        self.assertEqual(SSE, 0.0, 'Calibration should result in SSE = 0.0!')

    def test_sample(self):
        s = self.prob.get_samples(siz=1, noCorrRestr=True)
        lb = self.prob.get_lower_bounds()
        ub = self.prob.get_upper_bounds()
        self.assertTrue( (s >= lb).any() and (s <= ub).any(), 'Sample outside parameter bounds!' )

    def test_parallel(self):
        par_out, par_in = self.prob.run_samples(siz=10, seed=1000, templatedir='templatedir', workdir_base='workdir', parallel=True, save_dirs=False)
        ser_out, ser_in = self.prob.run_samples(siz=10, seed=1000)
        for dir in glob('workdir.*'):
            rmtree(dir)
        self.assertTrue( (par_in == ser_in).any(), 'Parallel and serial samples not the same!' )
        self.assertTrue( (par_out == ser_out).any(), 'Parallel and serial samples outputs not the same!' )

    def test_mcmc(self):
        mcmc.create_pymc_model(self.prob)
        M = mcmc.mcmc(self.prob, nsample=10)
        #TODO: add test criteria

    def test_dakoting(self):
        self.prob = dakoting.read_dakota('exp_model.dkt')
        data,samples = self.prob.run_samples(siz=10,parallel=True,ncpus=4)
        for dir in glob('workdir.*'):
            rmtree(dir)
        self.assertEqual(self.prob.nobs,4, 'nobs should be 4!')
        self.assertEqual(self.prob.npar,4, 'npar should be 4!')


if __name__ == '__main__':
    unittest.main()

