import sys,os
try:
    import matk
except:
    try:
        sys.path.append('..'+os.sep+'src')
        import matk
    except ImportError as err:
        print 'Unable to load MATK module: '+str(err)
import numpy
from scipy import arange, randn, exp
try:
    from collections import OrderedDict as dict
except:
    print "Warning: collections module is not installed"
    print "Ordering of observations will not be maintained in output"
from multiprocessing import freeze_support

# Model function
def dbexpl(p):
    t=arange(0,100,20.)
    if p['par1']<0.5:
        asdf
    y =  (p['par1']*exp(-p['par2']*t) + p['par3']*exp(-p['par4']*t))
    nm =  ['o1','o2','o3','o4','o5']
    return dict(zip(nm,y))

def run():
    # Setup MATK model with parameters
    p = matk.matk(model=dbexpl)
    p.add_par('par1',min=0,max=1)
    p.add_par('par2',min=0,max=0.2)
    p.add_par('par3',min=0,max=1)
    p.add_par('par4',min=0,max=0.2)
    
    # Create LHS sample
    s = p.lhs(siz=500, seed=1000)
    
    # Look at sample parameter histograms, correlations, and panels
    s.samples.hist(ncols=2,title='Parameter Histograms',tight=False)
    parcor = s.samples.corr(plot=True, title='Parameter Correlations')
    s.samples.panels(title='Parameter Panels')
    
    # Run model with parameter samples
    s.run( ncpus=2, outfile='results.dat', logfile='log.dat',verbose=False)
    
    # Look at sample response histograms, correlations, and panels
    s.responses.hist(ncols=3,title='Model Response Histograms',tight=False)
    
    # Copy sampleset and subset to only samples with nan responses
    snan = s.copy()
    snan.subset(numpy.isnan, obs='o1')
    
    # Evaluate parameter combination resulting in nans
    # Note that it is easy to identify that the culprit is par1 with values less than 0.5
    snan.samples.hist(ncols=2,title='NAN Parameter Histograms',tight=False)
    parcor = snan.samples.corr(plot=True, title='NAN Parameter Correlations')
    snan.samples.panels(title='NAN Parameter Panels')
    
# Freeze support is necessary for multiprocessing on windows
if __name__== "__main__":
    freeze_support()
    run()
