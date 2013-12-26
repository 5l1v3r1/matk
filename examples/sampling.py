import matk
import numpy
from scipy import arange, randn, exp
try:
    from collections import OrderedDict as dict
except:
    print "Warning: collections module is not installed"
    print "Ordering of observations will not be maintained in output"


# Model function
def dbexpl(p):
    t=arange(0,100,20.)
    y =  (p['par1']*exp(-p['par2']*t) + p['par3']*exp(-p['par4']*t))
    nm =  ['o1','o2','o3','o4','o5']
    return dict(zip(nm,y))


# Setup MATK model with parameters
p = matk.matk(model=dbexpl)
p.add_par('par1',min=0,max=1)
p.add_par('par2',min=0,max=0.2)
p.add_par('par3',min=0,max=1)
p.add_par('par4',min=0,max=0.2)

# Create LHS sample
p.set_lhs_samples('lhs', siz=20, seed=1000)

# Look at sample parameter histograms and correlations
p.sampleset['lhs'].samples.hist(ncols=2,title='Parameter Histograms',tight=True)
parcor = p.sampleset['lhs'].samples.corr(plot=True, title='Parameter Correlations')

# Run model with parameter samples
p.sampleset['lhs'].run( ncpus=2, outfile='results.dat', logfile='log.dat',verbose=False)

# Look at sample response histograms
p.sampleset['lhs'].responses.hist(ncols=3,title='Model Response Histograms',tight=True)
rescor = p.sampleset['lhs'].responses.corr(plot=True, title='Model Response Correlations')

# Print and plot parameter/response correlations
print "\nPearson Correlation Coefficients:"
pcorr = p.sampleset['lhs'].corr(plot=True,title='Pearson Correlation Coefficients') 
print "\nSpearman Correlation Coefficients:"
scorr = p.sampleset['lhs'].corr(plot=True,type='spearman',title='Spearman Rank Correlation Coefficients') 

