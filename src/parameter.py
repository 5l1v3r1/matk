class Parameter(object):
    """ pyma parameter class
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self._value = []
        self.min = None
        self.max = None
        self.initial_value = None
        self.mean = None
        self.std = None
        self.trans = 'none'
        self.scale = 1.0
        self.offset = 0.0
        self.parchglim = None
        self.pargrpnm = 'default'
        self.dist = 'uniform'
        self.nvals = 1
        for k,v in kwargs.iteritems():
            if k == 'initial_value':
                self.initial_value = float(v)
                self._value[0] = self.initial_value
            elif k == 'min':
                self.min = float(v)
            elif k == 'max':
                self.max = float(v)
            elif k == 'mean':
                self.mean = float(v)
            elif k == 'std':
                self.std = float(v)
            elif k == 'trans':
                self.trans = v
            elif k == 'scale':
                self.scale = float(v)
            elif k == 'offset':
                self.offset = float(v)
            elif k == 'parchglim':
                self.parchglim = v
            elif k == 'dist':
                self.dist = v
            elif k == 'dist_pars':
                self.dist_pars = v
            elif k == 'nvals':
                self.nvals = v
            else:
                print k + ' is not a valid argument'
        if not self.initial_value is None:
            self.value = self.initial_value
        if self.dist == 'uniform':
            if self.min is None or self.max is None: 
                print "Error: Max and min parameter value must be specified for uniform distribution"
                return
            if self.initial_value is None:
                if self.min <= self.initial_value <= self.max:
                    print "Error: Initial value is not within min and max values:"
                    return
            self.initial_value = (self.max + self.min)/2
            self.value = self.initial_value
            range = self.max - self.min
            self.dist_pars = (self.min, range)
        elif self.dist == 'norm':
            self.dist_pars = (self.mean, self.std)
    @property
    def name(self):
        """ Parameter name
        """
        return self._name
    @name.setter
    def name(self,value):
        self._name = value
    @property
    def min(self):
        """ Parameter lower bound
        """
        return self._min
    @min.setter
    def min(self,value):
        self._min = value
    @property
    def max(self):
        """ Parameter upper bound
        """
        return self._max
    @max.setter
    def max(self,value):
        self._max = value
    @property
    def mean(self):
        """ Parameter mean
        """
        return self._mean
    @mean.setter
    def mean(self,value):
        self._mean = value
    @property
    def std(self):
        """ Parameter st. dev.
        """
        return self._std
    @std.setter
    def std(self,value):
        self._std = value
    @property
    def trans(self):
        return self._trans
    @trans.setter
    def trans(self,value):
        self._trans = value
    @property
    def initial_value(self):
        return self._initial_value
    @initial_value.setter
    def initial_value(self,value):
        self._initial_value = value
    @property
    def value(self):
        """ Parameter value
        """
        return self._value[-1]
    @value.setter
    def value(self,value):
        self._value.append(float(value))
    @property
    def scale(self):
        """ Scale factor to multiply parameter by
        """
        return self._scale
    @scale.setter
    def scale(self,value):
        self._scale = value
    @property
    def offset(self):
        """ Offset to add to parameter
        """
        return self._offset
    @offset.setter
    def offset(self,value):
        self._offset = value
    @property
    def parchglim(self):
        return self._parchglim
    @parchglim.setter
    def parchglim(self,value):
        self._parchglim = value
    @property
    def dist(self):
        """ Probabilistic distribution of parameter belonging to scipy.stats
        module
        """
        return self._dist
    @dist.setter
    def dist(self,value):
        self._dist = value        
    @property
    def dist_pars(self):
        """ Distribution parameters required by self.dist 
        (e.g. if dist == uniform, dist_pars = (min,max-min))
        """
        return self._dist_pars
    @dist_pars.setter
    def dist_pars(self,value):
        self._dist_pars = value              
    @property
    def nvals(self):
        """ Number of values the paramter will take for parameter studies
        """
        return self._nvals
    @nvals.setter
    def nvals(self,value):
        self._nvals = value              
