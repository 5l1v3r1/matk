__all__ = ['read_dakota', 'read_dakota_files', 'write_dakota_files']

import pymads
import re
from numpy import array, where, zeros

def read_dakota(filename):
    """ Read a DAKOTA control file and populate objects
    
    First argument must be a DAKOTA input file
    Optional second argument is a pymads dakota_prob (pymads.dakota_prob)
    """
    f = open(filename, 'r')
    lines = array(f.readlines())
    f.close()
    i = 0
    while i < lines.size:
        values = lines[i].split('#') # Remove any comment section of line
        values = values[0].split()
        if values:
            if 'interface,' in values[0]:
                i+=1
                values = lines[i].split('#') # Remove any comment section of line
                values = values[0].split()
                if values:
                    if 'fork' or 'system' in values[0]:
                        i+=1
                        while lines[i].strip(): # Check if line is blank
                            values = lines[i].split('#') # Remove any comment section of line
                            if 'asynchronous evaluation_concurrency' in values[0]:
                                values = values[0].split('=')
                                ncpus = values[1].strip() 
                            elif 'analysis_driver' in values[0]:
                                values = values[0].split('=')
                                analysis_driver = re.sub("'","", values[1].strip() ) 
                            elif 'parameters_file' in values[0]:
                                values = values[0].split('=')
                                parameters_file = re.sub("'","", values[1].strip() )
                            elif 'results_file' in values[0]:
                                values = values[0].split('=')
                                results_file = re.sub("'","", values[1].strip() )
                            elif 'template_directory' in values[0]:
                                values = values[0].split('=')
                                template_directory = re.sub("'","", values[1].strip() )
                            elif 'named' in values[0]:
                                value = values[0].split()
                                workdir_base = re.sub("'","", value[1].strip() )
                                if 'file_save' in values[0]:
                                    file_save = True
                                if ' directory_save' in values[0]:
                                    file_save = True
                            #elif 'aprepro' in values[0]:
                            #    aprepro = True
                            i+=1
            if 'variables,' in values[0]:
                i+=1
                values = lines[i].split('#') # Remove any comment section of line
                npar = 0
                if values:
                    if 'uniform_uncertain' in values[0]:
                        value = values[0].split('=')
                        npar += int(value[1].strip()) 
                        i+=1
                        while lines[i].strip(): # Check if line is blank
                            values = lines[i].split('#') # Remove any comment section of line
                            if 'lower_bounds' in values[0]:
                                values = values[0].split('=')
                                min = values[1].split()
                            elif 'upper_bounds' in values[0]:
                                values = values[0].split('=')
                                max = values[1].split()
                            elif 'descriptors' in values[0]:
                                values = values[0].split('=')
                                par_names = re.sub("'","", values[1])
                                par_names = par_names.split()
                            i+=1
            #if 'method,' in values[0]:
            if 'responses,' in values[0]:
               i+=1
               values = lines[i].split('#') # Remove any comment section of line
               if 'num_response_functions' in values[0]:
                   value = values[0].split('=')
                   nobs = int(value[1].strip()) 
        i+=1
    # Create dakota pymads problem
    dakota_prob = pymads.PyMadsProblem(npar,nobs,analysis_driver=analysis_driver,parameters_file=parameters_file,results_file=results_file,templatedir=template_directory,file_save=file_save,dakota=True)
    # Create parameters
    for i in range(len(par_names)):
        initial_value = ( float(max[i]) + float(min[i]) ) / 2 # Set initial value to midpoint of range
        dakota_prob.add_parameter( par_names[i], min=min[i], max=max[i], initial_value=initial_value )
    for i in range(nobs):
        obs_name = 'response_' + str(i+1)
        dakota_prob.add_observation( obs_name )

    return dakota_prob

def read_dakota_files(prob, workdir=None):
    """ Read responses from simulation files

            Parameter
            ---------
            workdir : string
                name of directory where model output files exist            
    """
    results = []
    with open( prob.results_file, 'r' ) as f:
        results.append( f.readline().strip() )

    results = array(results)
    prob.set_sim_values( results )

def write_dakota_files(prob, workdir=None):
    """ Write parameter file in aprepro format (dprepro utility provided free with DAKOTA)

            Parameter
            ---------
            workdir : string
                name of directory to write model files to           
    """

    if workdir:
        filename = workdir + '/' + prob.parameters_file
    else:
        filename = prob.parameters_file
    
    f = open( filename, 'w')
    
    for par in prob.get_parameters():
        f.write( " { " + par.name + ' = ' + str(par.value) + ' }\n'  ) 
    
    f.close()
    
#def obj_fun(prob):
#    of = 0.0
#    for obsgrp in prob.obsgrp:
#        for obs in obsgrp.observation:
#            of += ( float(obs.value) - float(obs.sim_value) )**2
#    return of
#            
 
def main(argv=None):
    import sys
    if argv is None:
        argv = sys.argv
    dakota_prob = read_dakota(argv[1])
    print dakota_prob

if __name__ == "__main__":
    main()
 
