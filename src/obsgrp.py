from observation import Observation

class ObservationGroup(object):
    def __init__(self, name):
        self.name = name
        self.observation = []
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self,value):
        self._name = value
    def add_observation(self, name, value, **kwargs):
        """Add a parameter to the problem
        
            [-] - optional parameters
            problem.add_parameter( name, value, weight, obsgrpnm)
        """
        #mypar = parameter(name,value, **kwargs)
        self.observation.append(Observation(name,value,**kwargs))
    def __iter__(self):
        return iter(self.observation)
        