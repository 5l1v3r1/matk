__all__ = ['forward']
from subprocess import call
from os import name
import pesting
from numpy import array

def run_model(prob, **kwargs):
    """ Run forward model using current value
    
    First argument is a pymads problem
    """
    #for k,v in kwargs:
    #    if k == 'pars':
    #        index = 0
    #        for pargrp in prob.pargrp:
    #            for par in pargrp.parameter:
    #                par.value = v[index]
    #                index += 1
   
    if prob.pest == True:
        pesting.write_model_files(prob)
    if name == 'posix': # If *nix system
        call(prob.sim_command, shell=True, executable='/bin/tcsh')
    else: # If Windows, not sure if this works, maybe get rid of shell=True
        call(prob.sim_command, shell=True)
    if prob.pest == True:
        pesting.read_model_files(prob)
        
  