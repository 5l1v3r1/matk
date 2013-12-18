import sys, os
from parameter import Parameter
from observation import Observation
from sampleset import SampleSet
import numpy 
from lhs import *
import cPickle as pickle
from shutil import rmtree
import itertools
from multiprocessing import Process, Manager, Pool, freeze_support
from multiprocessing.queues import Queue, JoinableQueue
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

class matk(object):
    """ Class for Model Analysis ToolKit (MATK) module
    """
    def __init__(self, **kwargs):
        '''Initialize MATK object
        :returns: object -- MATK object
        '''
        self.model = ''
        self.model_args = None
        self.model_kwargs = None
        self.ncpus = 1
        self.workdir_base = None
        self.workdir = None
        self.templatedir = None
        self.results_file = None
        self.parameters_file = None
        self.seed = None
        self.sample_size = 10 
        for k,v in kwargs.iteritems():
            if 'sample_size' == k:
                self.sample_size = int(v)
            elif 'ncpus' == k:
                self.ncpus == int(v)
            elif 'workdir_base' == k:
                self.workdir_base = v
            elif 'workdir' == k:
                self.workdir = v
            elif 'templatedir' == k:
                self.templatedir = v
            elif 'model' == k:
                self.model = v
            elif 'model_args' == k:
                self.model_args = v
            elif 'model_kwargs' == k:
                self.model_kwargs = v
            elif 'parameters_file' == k:
                self.parameters_file = v
            elif 'results_file' == k:
                self.results_file = v
            elif 'templatedir' == k:
                self.templatedir = v
            else:
                print k + ' is not a valid argument'
      
        self.pars = OrderedDict()
        self.obs = OrderedDict()
        self.sampleset = OrderedDict()
        self.workdir_index = 0
        self._current = False # Flag indicating if simulated values are associated with current parameters
    @property
    def model(self):
        """ Python function that runs model
        """
        return self._model
    @model.setter
    def model(self,value):
        self._model = value       
    @property
    def model_args(self):
        """ Tuple of extra arguments to MATK model expected to come after parameter dictionary
        """
        return self._model_args
    @model_args.setter
    def model_args(self,value):
        if value is None:
            self._model_args = value
        elif not isinstance( value, (tuple,list,numpy.ndarray) ):
            print "Error: Expected list or array for model keyword arguments"
            return
        else:
            self._model_args = value
    @property
    def model_kwargs(self):
        """ Dictionary of extra keyword arguments to MATK model expected to come after parameter dictionary and model_args
        """
        return self._model_kwargs
    @model_kwargs.setter
    def model_kwargs(self,value):
        if value is None:
            self._model_kwargs = value       
        elif not isinstance( value, dict ):
            print "Error: Expected dictionary for model keyword arguments"
            return
        else:
            self._model_kwargs = value       
    @property
    def ncpus(self):
        """ Set number of cpus to use for concurrent model evaluations
        """
        return self._ncpus
    @ncpus.setter
    def ncpus(self,value):
        self._ncpus = value
    @property
    def workdir_base(self):
        """ Set the base name for parallel working directories
        """
        return self._workdir_base
    @workdir_base.setter
    def workdir_base(self,value):
        self._workdir_base = value    
    @property
    def workdir(self):
        """ Set the base name for parallel working directories
        """
        return self._workdir
    @workdir.setter
    def workdir(self,value):
        self._workdir = value    
    @property
    def workdir_index(self):
        """ Set the working directory index for parallel runs    
        """
        return self._workdir_index
    @workdir_index.setter
    def workdir_index(self,value):
        self._workdir_index = value
    @property
    def templatedir(self):
        """ Set the name of the templatedir for parallel runs   
        """
        return self._templatedir
    @templatedir.setter
    def templatedir(self,value):
        self._templatedir = value
    @property
    def parameters_file(self):
        """ Set the name of the parameters_file for parallel runs   
        """
        return self._parameters_file
    @parameters_file.setter
    def parameters_file(self,value):
        self._parameters_file = value
    @property
    def results_file(self):
        """ Set the name of the results_file for parallel runs   
        """
        return self._results_file
    @results_file.setter
    def results_file(self,value):
        self._results_file = value
    @property
    def seed(self):
        """ Set the seed for random sampling
        """
        return self._seed
    @seed.setter
    def seed(self,value):
        self._seed = value
    @property
    def ssr(self):
        """ Sum of squared residuals
        """
        return sum(numpy.array(self.residuals)**2)
    def add_par(self, name, **kwargs):
        """ Add parameter to problem

            :param name: Name of parameter
            :type name: str
            :param kwargs: keyword arguments passed to parameter class
        """
        if name in self.pars: 
            self.par[name] = Parameter(name,parent=self,**kwargs)
        else:
            self.pars.__setitem__( name, Parameter(name,parent=self,**kwargs))
    def add_obs(self,name,**kwargs):
        """ Add observation to problem
            
            :param name: Name of observation
            :type name: str
            :param kwargs: keyword arguments passed to observation class
        """
        if name in self.obs: 
            self.obs[name] = Observation(name,**kwargs)
        else:
            self.obs.__setitem__( name, Observation(name,**kwargs))
    def add_sampleset(self,name,samples,responses=None,indices=None,index_start=1):
        """ Add sample set to problem
            
            :param name: Name of sample set
            :type name: str
            :param samples: Matrix of parameter samples with npar columns in order of matk.pars.keys()
            :type samples: list(fl64),ndarray(fl64)
            :param responses: Matrix of associated responses with nobs columns in order matk.obs.keys() if observation exists (existence of observations is not required) 
            :type responses: list(fl64),ndarray(fl64)
            :param indices: Sample indices to use when creating working directories and output files
            :type indices: list(int),ndarray(int)
        """
        if not isinstance( samples, (list,numpy.ndarray)):
            print "Error: Parameter samples are not a list or ndarray"
            return 1
        npar = len(self.pars)
        # If list, convert to ndarray
        if isinstance( samples, list ):
            samples = numpy.array(samples)
        if not samples.shape[1] == npar:
            print "Error: The number of columns in sample is not equal to the number of parameters in the problem"
            return 1
        if len(self.pars) > 0:
            parnames = self.par_names
        else:
            parnames = None
        if len(self.obs) > 0:
            obsnames = self.obs_names
        else:
            obsnames = None
        if name in self.sampleset: 
            self.sampleset[name] = SampleSet(name,samples,responses=responses,
                                             indices=indices,index_start=index_start,
                                             parnames=parnames, obsnames=obsnames)
        else:
            self.sampleset.__setitem__( name, SampleSet(name,samples,responses=responses,
                                                indices=indices,index_start=index_start,
                                                parnames=parnames, obsnames=obsnames))
    @property
    def sim_values(self):
        """ Simulated values
            :returns: lst(fl64) -- simulated values in order of matk.obs.keys()
        """
        return [obs.sim for obs in self.obs.values()]
    def _set_sim_values(self, *args, **kwargs):
        """ Set simulated values using a tuple, list, numpy.ndarray, dictionary or keyword arguments
        """
        if len(args) > 0 and len(kwargs) > 0:
            print "Warning: dictionary arg will overide keyword args"
        if len(args) > 0:
            if isinstance( args[0], dict ):
                for k,v in args[0].iteritems():
                    if k in self.obs:
                        self.obs[k].sim = v
                    else:
                        self.add_obs( k, sim=v ) 
            elif isinstance( args[0], (list,tuple,numpy.ndarray) ):
                # If no observations exist, create them
                if len(self.obs) == 0:
                    for i,v in zip(range(len(args[0])),args[0]): 
                        self.add_obs('obs'+str(i),sim=v)
                elif not len(args[0]) == len(self.obs): 
                    print len(args[0]), len(self.obs)
                    print "Error: Number of simulated values in list or tuple does not match created observations"
                    return
                else:
                    for k,v in zip(self.obs.keys(),args[0]):
                        self.obs[k].sim = v
        else:
            for k,v in kwargs.iteritems():
                if k in self.obs:
                    self.obs[k].sim = v
                else:
                    self.add_obs( k, sim=v ) 
    @property
    def par_values(self):
        """ Parameter values
        """
        return [par.value for par in self.pars.values()]
    @par_values.setter
    def par_values(self, value):
        """ Set parameter values using a tuple, list, numpy.ndarray, or dictionary
        """
        if isinstance( value, dict ):
            for k,v in value.iteritems():
                self.pars[k].value = v
        elif isinstance( value, (list,tuple,numpy.ndarray)):
            if not len(value) == len(self.pars): 
                print "Error: Number of parameter values in ndarray does not match created parameters"
                return
            for v,k in zip(value,self.pars.keys()):
                self.pars[k].value = v
        else:
            print "Error: tuple, list, numpy.ndarray, or dictionary expected"
    @property
    def par_names(self):
        """ Get parameter names
        """
        return [par.name for par in self.pars.values()]
    @property
    def par_nvals(self):
        """ Get parameter nvals (number of values for parameter studies)
        """
        return [par.nval for par in self.pars.values()]
    @property
    def obs_values(self):
        """ Observation values
        """
        return [o.value for o in self.obs.values()]
    @obs_values.setter
    def obs_values(self, value):
        """ Set simulated values using a tuple, list, numpy.ndarray, or dictionary
        """
        if isinstance( value, dict ):
            for k,v in value.iteritems():
                if k in self.obs:
                    self.obs[k].value = v
                else:
                    self.add_obs( k, value=v ) 
        elif isinstance( value, (list,tuple,numpy.ndarray) ):
            # If no observations exist, create them
            if len(self.obs) == 0:
                for i,v in enumerate(value): 
                    self.add_obs('obs'+str(i),value=v)
            # else, check if length of value is equal to number created observation
            elif not len(value) == len(self.obs): 
                    print "Error: Number of simulated values does not match created observations"
                    return
            # else, set observation values in order
            else:
                for k,v in zip(self.obs.keys(),value):
                    self.obs[k].value = v
        else:
            print "Error: tuple, list, numpy.ndarray, or dictionary expected"
    @property
    def obs_names(self):
        """ Get observation names
        """
        return [o.name for o in self.obs.values()]
    @property
    def obs_weights(self):
        """ Get observation names
        """
        return [o.weight for o in self.obs.values()]
    @property
    def residuals(self):
        """ Get least squares values
        """
        return [o.residual for o in self.obs.values()]
    @property
    def par_mins(self):
        """ Get parameter lower bounds
        """
        return [par.min for par in self.pars.values()]
    @property
    def par_maxs(self):
        """ Get parameter lower bounds
        """
        return [par.max for par in self.pars.values()]
    @property
    def par_dists(self):
        """ Get parameter probabilistic distributions
        """
        return [par.dist for par in self.pars.values()]
    @property
    def par_dist_pars(self):
        """ Get parameters needed by parameter distributions
        """
        return [par.dist_pars for par in self.pars.values()]
    def __iter__(self):
        return self
    def make_workdir(self, workdir=None, reuse_dirs=False):
        """ Create a working directory

            :param workdir: Name of directory where model will be run. It will be created if it does not exist
            :type workdir: str
            :param reuse_dirs: If True and workdir exists, the model will reuse the directory
            :type reuse_dirs: bool
            :returns: int -- 0: Successful run, 1: workdir exists 
        """
        if not workdir is None: self.workdir = workdir
        if not self.workdir is None:
            # If folder doesn't exist
            if not os.path.isdir( self.workdir ):
                os.makedirs( self.workdir )
                return 0
            # or if reusing directories
            elif reuse_dirs:
                pass
                return 0
            # or throw error
            else:
                print "Error: " + self.workdir + " already exists"
                return 1
    def forward(self, pardict=None, workdir=None, reuse_dirs=False):
        """ Run MATK model using current values

            :param pardict: Dictionary of parameter values keyed by parameter names
            :type pardict: dict
            :param workdir: Name of directory where model will be run. It will be created if it does not exist
            :type workdir: str
            :param reuse_dirs: If True and workdir exists, the model will reuse the directory
            :type reuse_dirs: bool
            :returns: int -- 0: Successful run, 1: workdir exists 
        """
        if not workdir is None: self.workdir = workdir
        if not self.workdir is None:
            curdir = os.getcwd()
            status = self.make_workdir( workdir=self.workdir, reuse_dirs=reuse_dirs)
            os.chdir( self.workdir )
            if status:
                return 1
        else:
            curdir = None
        if hasattr( self.model, '__call__' ):
            if pardict is None:
                pardict = dict([(k,par.value) for k,par in self.pars.items()])
            else: self.par_values = pardict
            if self.model_args is None and self.model_kwargs is None:
                sims = self.model( pardict )
            elif not self.model_args is None and self.model_kwargs is None:
                sims = self.model( pardict, *self.model_args )
            elif self.model_args is None and not self.model_kwargs is None:
                sims = self.model( pardict, **self.model_kwargs )
            elif not self.model_args is None and not self.model_kwargs is None:
                sims = self.model( pardict, *self.model_args, **self.model_kwargs )
            self._set_sim_values(sims)
            self._current = True
        else:
            print "Error: Model is not a Python function"
            return 1
        if not curdir is None:
            os.chdir( curdir )
        return None
    def lmfit(self,workdir=None,reuse_dirs=False,report_fit=True):
        """ Calibrate MATK model using lmfit package

            :param workdir: Name of directory where model will be run. It will be created if it does not exist
            :type workdir: str
            :param reuse_dirs: If True and workdir exists, the model will reuse the directory
            :type reuse_dirs: bool
            :param report_fit: If True, parameter statistics and correlations are printed to the screen
            :type report_fit: bool
            :returns: lmfit minimizer object
        """
           
        try: import lmfit
        except ImportError as exc:
            sys.stderr.write("Warning: failed to import lmfit module. ({})".format(exc))
            return
        def residual(params, prob):
            nm = [params[p.name].name for k,p in prob.pars.items()]
            vs = [params[p.name].value for k,p in prob.pars.items()]
            prob.forward(pardict=dict(zip(nm,vs)),workdir=workdir,reuse_dirs=reuse_dirs)
            return prob.residuals

        # Create lmfit parameter object
        params = lmfit.Parameters()
        for k,p in self.pars.items():
            params.add(k,value=p.value,vary=p.vary,min=p.min,max=p.max,expr=p.expr) 

        out = lmfit.minimize(residual, params, args=(self,))

        # Make sure that self.pars are set to final values of params
        nm = [params[k].name for k in self.pars.keys()]
        vs = [params[k].value for k in self.pars.keys()]
        self.par_values = dict(zip(nm,vs))
        # Run forward model to set simulated values
        self.forward(workdir=workdir, reuse_dirs=reuse_dirs)

        if report_fit:
            print lmfit.report_fit(params)
        return out

    def levmar(self,workdir=None,reuse_dirs=False,max_iter=1000,full_output=True):
        """ Calibrate MATK model using levmar package

            :param workdir: Name of directory where model will be run. It will be created if it does not exist
            :type workdir: str
            :param reuse_dirs: If True and workdir exists, the model will reuse the directory
            :type reuse_dirs: bool
            :param max_iter: Maximum number of iterations
            :type max_iter: int
            :param full_output: If True, additional output displayed during calibration
            :returns: levmar output
        """
        try: import levmar
        except ImportError as exc:
            sys.stderr.write("Warning: failed to import levmar module. ({})".format(exc))
            return
        def _f(pars, prob):
            prob = prob[0]
            nm = [p.name for p in prob.pars.values()]
            vs = [p._func_value(v) for v,p in zip(pars,prob.pars.values())]
            print nm,vs
            prob.forward(pardict=dict(zip(nm,vs)),workdir=workdir,reuse_dirs=reuse_dirs)
            return prob.sim_values
        vs = [p.calib_value for p in self.pars.values()]
        meas = self.obs_values
        if full_output: full_output = 1
        out = levmar.leastsq(_f, vs, meas, args=(self,), Dfun=None, max_iter=max_iter, full_output=full_output)
        #TODO Put levmar results into MATK object
        return out
    def set_lhs_samples(self, name, siz=None, noCorrRestr=False, corrmat=None, seed=None, index_start=1):
        """ Draw lhs samples of parameter values from scipy.stats module distribution
        
            :param name: Name of sample set to be created
            :type name: str
            :param siz: Number of samples to generate, ignored if samples are provided
            :type siz: int
            :param noCorrRestr: If True, correlation structure is not enforced on sample, use if siz is less than number of parameters
            :type noCorrRestr: bool
            :param corrmat: Correlation matrix
            :type corrmat: matrix
            :param seed: Random seed to allow replication of samples
            :type seed: int
            :param index_start: Starting value for sample indices
            :type: int
            :returns: matrix -- Parameter samples
          
        """
        if seed:
            self.seed = seed
        # If siz specified, set sample_size
        if siz:
            self.sample_size = siz
        else:
            siz = self.sample_size
        # Take distribution keyword and convert to scipy.stats distribution object
        dists = []
        for dist in self.par_dists:
            eval( 'dists.append(stats.' + dist + ')' )
        dist_pars = self.par_dist_pars
        x = lhs(dists, dist_pars, siz=siz, noCorrRestr=noCorrRestr, corrmat=corrmat, seed=seed)
        self.add_sampleset( name, x, index_start=index_start )
    def run_samples(self, name=None, ncpus=1, templatedir=None, workdir_base=None,
                    save=True, reuse_dirs=False, outfile=None, verbose=True ):
        """ Run model using values in samples for parameter values
            If samples are not specified, LHS samples are produced
            
            :param name: Name of MATK sample set object
            :type samples: str
            :param ncpus: number of cpus to use to run models concurrently
            :type ncpus: int
            :param templatedir: Name of folder including files needed to run model (e.g. template files, instruction files, executables, etc.)
            :type templatedir: str
            :param workdir_base: Base name for model run folders, run index is appended to workdir_base
            :type workdir_base: str
            :param save: If True, model files and folders will not be deleted during parallel model execution
            :type save: bool
            :param reuse_dirs: Will use existing directories if True, will return an error if False and directory exists
            :type reuse_dirs: bool
            :param outfile: File to write results to
            :type outfile: str
            :returns: tuple(ndarray(fl64),ndarray(fl64)) - (Matrix of responses from sampled model runs siz rows by npar columns, Parameter samples, same as input samples if provided)
            
        """
        # If name is None, run last created sampleset 
        if name is None:
            name = next(reversed(self.sampleset)).name
        elif len(self.sampleset) == 0:
            print "Error: There is not a sampleset to run"
            return
        if templatedir:
            self.templatedir = templatedir
        if workdir_base:
            self.workdir_base = workdir_base
                
        if verbose: 
            print "%-8s" % 'index',
            for nm in self.par_names:
                print ' ',
                print "%14s" % nm,
            header = True
        if ncpus == 1:
            out = []
            for sample, index in zip(self.sampleset[name].samples,self.sampleset[name].indices):
                self.par_values = sample
                if not self.workdir_base is None:
                    workdir = self.workdir_base + '.' + str(index)
                else:
                    workdir = None
                self.forward(workdir=workdir,reuse_dirs=reuse_dirs)
                if not save:
                    rmtree( workdir )
                responses = self.sim_values
                if verbose:
                    if header:
                        for nm in self.obs_names:
                            print " ",
                            print "%14s" % nm,
                        header = False
                        print ''
                    print "%-8d" % index,
                    for v in sample:
                        print "%16lf" % v,
                    for v in responses:
                        print "%16lf" % v,
                    print ''

                out.append( responses )
            out = numpy.array(out)
        elif ncpus > 1:
            out, samples = self.parallel_mp(ncpus, self.sampleset[name].samples, indices=self.sampleset[name].indices,
                                         templatedir=templatedir, workdir_base=workdir_base, 
                                         save=save, reuse_dirs=reuse_dirs, verbose=verbose)
        else:
            print 'Error: number of cpus (ncpus) must be greater than zero'
            return
        self.sampleset[name].responses = out 
        if not outfile is None:
            self.save_sampleset( outfile, name )

        return out
    def parallel(self, ncpus, par_sets, templatedir=None, workdir_base=None, save=True,
                reuse_dirs=False, indices=None):
 
        def child( prob ):
            if hasattr( prob.model, '__call__' ):
                status = prob.forward(reuse_dirs=reuse_dirs)
                if status:
                    print "Error running forward model for parallel job " + str(prob.workdir_index)
                    os._exit( 0 )
                out = dict( zip(prob.obs_names,prob.sim_values) )
                if self.workdir is None:
                    pickle.dump( out, open(self.results_file, "wb"))
                else:
                    pickle.dump( out, open(os.path.join(self.workdir,self.results_file), "wb"))
            os._exit( 0 )

        def set_child( prob ):
            if prob.workdir_base is not None:
                prob.workdir = prob.workdir_base + '.' + str(prob.workdir_index)
            prob.results_file = 'output' + '.' + str(prob.workdir_index)

        # Determine if using working directories or not
        saved_workdir = self.workdir # Save workdir to reset after parallel run
        if not workdir_base is None: self.workdir_base = workdir_base
        if self.workdir_base is None: self.workdir = None

        # Determine number of samples and adjust ncpus if samples < ncpus requested
        if isinstance( par_sets, numpy.ndarray ): n = par_sets.shape[0]
        elif isinstance( par_sets, list ): n = len(par_sets)
        if n < ncpus: ncpus = n

        # Start ncpus model runs
        jobs = []
        pids = []
        workdirs = []
        ps_index = [] # Parset index used for reordering
        results_files = []
        for i in range(ncpus):
            self.workdir_index = indices[i]
            set_child( self )
            pardict = dict(zip(self.par_names(), par_sets[i] ) )
            self.par_values = pardict
            pid = os.fork()
            if pid:
                parent = True
                pids.append(pid)
                workdirs.append( self.workdir )
                ps_index.append( i )
                results_files.append(self.results_file)
            else:
                parent = False
                child( self )
                os._exit( 0 )

        
        # Wait for jobs and start new ones
        if parent:
            # Create dictionaries of results_file names and working directories for reference below
            resfl_dict = dict(zip(pids,results_files)) 
            wkdir_dict = dict(zip(pids,workdirs))
            ps_index_dict = dict(zip(pids,ps_index))
            res_index = []
            responses = []
            njobs_started = ncpus
            njobs_finished = 0
            while njobs_finished < n and parent:
                    rpid,status = os.wait() # Wait for jobs
                    if status:
                        print os.strerror( status )
                        return 1
                    # Update dictionaries to include any new jobs
                    resfl_dict = dict(zip(pids,results_files))
                    wkdir_dict = dict(zip(pids,workdirs))
                    ps_index_dict = dict(zip(pids,ps_index))
                    # Load results from completed job
                    if not wkdir_dict[rpid] is None:
                        out = pickle.load( open( os.path.join(wkdir_dict[rpid],resfl_dict[rpid]), "rb" ) )
                        if save is False:
                            rmtree( wkdir_dict[rpid] )
                    else:
                        out = pickle.load( open( resfl_dict[rpid], "rb" ))
                        if save is False:
                            os.remove( resfl_dict[rpid] )
                    self._set_sim_values( out )
                    responses.append( self.sim_values )
                    res_index.append( ps_index_dict[rpid] )
                    njobs_finished += 1
                    # Start new jobs
                    if njobs_started < n:
                        njobs_started += 1
                        self.workdir_index = indices[njobs_started-1]
                        set_child( self )
                        pardict = dict(zip(self.par_names(), par_sets[njobs_started-1] ) )
                        self.par_values = pardict
                        pid = os.fork()
                        if pid:
                            parent = True
                            pids.append(pid)
                            workdirs.append( self.workdir)
                            results_files.append(self.results_file)
                            ps_index.append( njobs_started-1 )
                        else:
                            parent = False
                            child( self )
                            os._exit( 0 )
        
        # Rearrange responses to correspond with par_sets
        res = []
        for i in range(n):
            res.append( responses[res_index[i]] ) 
        responses = numpy.array(res)

        # Clean parent
        self.workdir = saved_workdir

        return responses, par_sets   
    def child( self, in_queue, out_list, reuse_dirs, save):
        for pars,smp_ind,lst_ind in iter(in_queue.get, (None,None,None)):
            self.workdir_index = smp_ind
            if self.workdir_base is not None:
                self.workdir = self.workdir_base + '.' + str(self.workdir_index)
            self.par_values = pars
            status = self.forward(reuse_dirs=reuse_dirs)
            if status:
                print "Error running forward model for parallel job " + str(self.workdir_index)
            else:
                out_list.put([lst_ind, self.sim_values])
            if not save and not self.workdir is None:
                rmtree( self.workdir )
            in_queue.task_done()
        in_queue.task_done()
    def parallel_mp(self, ncpus, par_sets, templatedir=None, workdir_base=None, save=True,
                reuse_dirs=False, indices=None, verbose=True):

        if not os.name is "posix":
            # Use freeze_support for PCs
            freeze_support()

        # Determine if using working directories or not
        saved_workdir = self.workdir # Save workdir to reset after parallel run
        if not workdir_base is None: self.workdir_base = workdir_base
        if self.workdir_base is None: self.workdir = None

        # Determine number of samples and adjust ncpus if samples < ncpus requested
        if isinstance( par_sets, numpy.ndarray ): n = par_sets.shape[0]
        elif isinstance( par_sets, list ): n = len(par_sets)
        if n < ncpus: ncpus = n

        # Start ncpus model runs
        resultsq = Queue()
        work = JoinableQueue()
        pool = []
        for i in range(ncpus):
            p = Process(target=self.child, args=(work, resultsq, reuse_dirs, save))
            p.daemon = True
            p.start()
            pool.append(p)

        iter_args = itertools.chain( par_sets, (None,)*ncpus )
        iter_smpind = itertools.chain( indices, (None,)*ncpus )
        iter_lstind = itertools.chain( range(len(par_sets)), (None,)*ncpus )
        for item in zip(iter_args,iter_smpind,iter_lstind):
            work.put(item)
        
        results = [None]*len(par_sets)
        header = True
        for i in range(len(par_sets)):
            ind, resp = resultsq.get()
            results[ind] = resp
            if verbose:
                if header:
                    if len(self.obs_names) == 0:
                        for i in range(len(results[ind])):
                            print "%15s" % 'obs'+str(i+1),
                    else:
                        for nm in self.obs_names:
                            print " ",
                            print "%14s" % nm,
                    header = False
                    print ''
                print "%-8d" % indices[ind],
                for v in par_sets[ind]:
                    print "%16lf" % v,
                for v in resp:
                    print "%16lf" % v,
                print ''
            
        for p in pool:
            p.join()

        # Clean parent
        self.workdir = saved_workdir
        results = numpy.array(results)

        return results, par_sets   
    def set_parstudy_samples(self, name, *args, **kwargs):
        ''' Generate parameter study samples
        
        :param name: Name of sample set to be created
        :type name: str
        :param outfile: Name of file where samples will be written. If outfile=None, no file is written.
        :type outfile: str
        :param args: Number of values for each parameter. The order is expected to match order of matk.pars.keys()
        :type args: tuple(fl64), list(fl64), or ndarray(fl64)
        :param kwargs: keyword arguments where keyword is the parameter name and argument is the number of desired values
        :type kwargs: dict(fl64)
        :returns: ndarray(fl64) -- Array of samples
        '''
        outfile = None
        for k,v in kwargs.iteritems():
            if k == 'outfile':
                outfile = v

        if len(args) > 0 and len(kwargs) > 0:
            print "Warning: dictionary arg will overide keyword args"
        if len(args) > 0:
            if isinstance( args[0], dict ):
                for k,v in args[0].iteritems():
                    self.pars[k].nvals = v
            elif isinstance( args[0], (list,tuple,numpy.ndarray)):
                if isinstance( args[0], (list,tuple)):
                    if not len(args[0]) == len(self.pars): 
                        print "Error: Number of values in list or tuple does not match created parameters"
                        return
                elif isinstance( args[0], numpy.ndarray ):
                    if not args[0].shape[0] == len(self.pars): 
                        print "Error: Number of values in ndarray does not match created parameters"
                        return
                i = 0
                for v,k in zip(args[0],self.pars.keys()):
                    self.pars[k].nvals = v
                    i += 1
        else:
            for k,v in kwargs.iteritems():
                if not k == 'outfile':
                    self.pars[k].nvals = v


        x = []
        for k,p in self.pars.items():
            if p.nvals == 1 or not p.vary:
                x.append(numpy.linspace(p.value, p.max, p.nvals))
            elif p.nvals > 1:
                x.append(numpy.linspace(p.min, p.max, p.nvals))

        x = list(itertools.product(*x))
        x = numpy.array(x)

        self.add_sampleset( name, x )

    def save_sampleset( self, outfile, sampleset ):
        ''' Save sampleset to file

            :param outfile: Name of file where sampleset will be written
            :type outfile: str
            :param sampleset: Sampleset name
            :type sampleset: str
        '''

        if isinstance( sampleset, str ):
            x = numpy.column_stack([self.sampleset[sampleset].indices,self.sampleset[sampleset].samples])
            if not self.sampleset[sampleset].responses is None:
                x = numpy.column_stack([x,self.sampleset[sampleset].responses])
        else:
            print 'Error: sampleset is not a string'
            return

        if outfile:
            f = open(outfile, 'w')
            f.write("%-8s" % 'index' )
            # Print par names
            for nm in self.par_names:
                f.write(" ")
                f.write("%15s" % nm )
            # Print obs names if responses exist
            if not self.sampleset[sampleset].responses is None:
                if len(self.obs_names) == 0:
                    for i in range(self.sampleset[sampleset].responses.shape[1]):
                        #f.write(" ")
                        f.write("%15s" % 'obs'+str(i+1) )
                else:
                    for nm in self.obs_names:
                        #f.write(" ")
                        f.write("%15s" % nm )
            f.write('\n')
            for row in x:
                f.write("%-8d" % row[0] )
                for i in range(1,len(row)):
                    f.write("%16lf" % row[i] )
                f.write('\n')
            #numpy.savetxt(f, x, fmt='%16lf')
            f.close()
    def Jac( self, h=1.e-3, ncpus=1, templatedir=None, workdir_base=None,
                    save=True, reuse_dirs=False ):
        ''' Numerical Jacobian calculation

            :param h: Parameter increment, single value or array with npar values
            :type h: fl64 or ndarray(fl64)
            :returns: ndarray(fl64) -- Jacobian matrix
        '''
        # Collect parameter sets
        a = numpy.copy(numpy.array(self.par_values))
        # If current simulated values are associated with current parameter values...
        if self._current:
            sims = self.sim_values
        if isinstance(h, (tuple,list)):
            h = numpy.array(h)
        elif not isinstance(h, numpy.ndarray):
            h = numpy.ones(len(a))*h
        hlmat = numpy.identity(len(self.pars))*-h
        humat = numpy.identity(len(self.pars))*h
        hmat = numpy.concatenate([hlmat,humat])
        parset = []
        for hs in hmat:
            parset.append(hs+a)
        parset = numpy.array(parset)
        self.add_sampleset('_jac_',parset)

        self.run_samples(name='_jac_', ncpus=ncpus, templatedir=templatedir, verbose=False,
                         workdir_base=workdir_base, save=save, reuse_dirs=reuse_dirs )
        # Perform simulations on parameter sets
        obs = self.sampleset['_jac_'].responses
        a_ls = obs[0:len(a)]
        a_us = obs[len(a):]
        J = []
        for a_l,a_u,hs in zip(a_ls,a_us,h):
            J.append((a_l-a_u)/(2*hs))
        self.par_values = a
        # If current simulated values are associated with current parameter values...
        if self._current:
            self._set_sim_values(sims)

        return numpy.array(J).T
    def calibrate( self, maxiter=100, lambdax=0.001, minchange=1.0e-1, minlambdax=1.0e-6, verbose=False,
                  workdir=None, reuse_dirs=False):
        from minimizer import Minimizer
        fitter = Minimizer(self)
        fitter.calibrate(maxiter=maxiter, lambdax=lambdax, minchange=minchange,
                         minlambdax=minlambdax, verbose=verbose, workdir=workdir, reuse_dirs=reuse_dirs)


