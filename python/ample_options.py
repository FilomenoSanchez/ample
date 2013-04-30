'''
Class to hold the options for ample
'''

# Our imports
import printTable

class AmpleOptions(object):
    
    def __init__(self):
        
        # The dictionary with all the options
        self.d = {}
        pass
    
    def final_summary(self, cluster=None):
        """Return a string summarising the results of the run.
        
        Args:
        cluster -- the number of the cluster to summarise (COUNTING FROM 0)
                   otherwise all clusters are summarised
        """
        
        if not cluster:
            # Get number of clusters from the length of the mrbump results lists
            clusters = [ i for i in range( len( self.d['mrbump_results'] ) ) ]
        else:
            if cluster >= len( self.d['mrbump_results'] ):
                raise RuntimeError, "Cluster number is not in results list"
            clusters = [ cluster ]
            
        # String to hold the results summary
        summary = ""
        for cluster in clusters:
            
            summary+="\n\nResults for cluster: {0}\n\n".format( cluster+1 )
            
            
            # Table for results with header
            results_table = []
            results_table.append( ("Name", "MR_program", "Solution", "final_Rfact", "final_Rfree", "SHELXE_CC", "#Models", "#Residues") )

            # Assume mrbump_results are already sorted
            mrbump_results = self.d['mrbump_results'][ cluster ]
            ensemble_results = self.d['ensemble_results'][ cluster ]
            
            name2e = {}
            # Get map of name -> ensemble result
            for i, e in enumerate( ensemble_results ):
                if name2e.has_key( e.name ):
                    raise RuntimeError, "Duplicate key: {0}".format( e.name )
                name2e[ e.name ] = ensemble_results[ i ]
            
            best=None
            for i, result in enumerate( mrbump_results ):
                
                # MRBUMP Results have loc0_ALL_ prepended and  _UNMOD appended
                name = result.name[9:-6]
                
                # Remember best result
                if i == 0:
                    best = mrbump_results[i]
                
                result_summary = [ result.name,
                                   result.program,
                                   result.solution,
                                   result.rfact,
                                   result.rfree,
                                   result.shelxCC,
                                   name2e[ name ].num_models,
                                   name2e[ name ].num_residues
                                ]
            
                results_table.append( result_summary )
                
            # Get nicely formatted string summarising the results
            table = printTable.Table()
            summary += table.pprint_table( results_table )
            
            # Show where it happened
            summary += '\nBest results so far are in :\n\n'
            summary +=  best.resultDir
        
        return summary
        
        
    def populate( self, parser_args ):
        """
        Fill ourselves with the options from the parser
        """
        
        tmpv = None
        for k, v in vars(parser_args).iteritems():
            #print "{} | {}".format( k, v )   
            if isinstance(v,list):
                # All values are in a list
                tmpv  = v[0]
            else:
                tmpv = v
                
            # Bit of a hack for true/false
            if isinstance( tmpv, str ):
                if tmpv.lower() == "true":
                    tmpv = True
                elif tmpv.lower() == "false":
                    tmpv = False
                
            self.d[k] = tmpv
            
            #if v == False:
            #    self.d[k] = False
        
        # end of loop
        
        #for k, v in self.d.iteritems():
        #    print "{} | {}".format( k, v )
        
    def prettify_parameters(self):
        """
        Return the parameters nicely formated as a list of strings suitable for writing out to a file
        """
        pstr = ""
        pstr +='Params Used in this Run\n\n'
        
        keys1 = ['fasta','work_dir','mtz','pdb_code']
        pstr += '---input---\n'
        for k in keys1:
            pstr += "{0}: {1}\n".format(k, self.d[k])

        keys2 = ['make_frags','rosetta_fragments_exe','frags3mers','frags9mers']
        pstr+= '\n---fragments---\n'
        for k in keys2:
            pstr += "{0}: {1}\n".format(k, self.d[k])
            
        keys3 = ['make_models','rosetta_path','rosetta_db']
        pstr+= '\n---modelling---\n'
        for k in keys3:
            pstr += "{0}: {1}\n".format(k, self.d[k])
        
        if self.d['use_scwrl']:
            pstr+= '\n---3rd party---\nSCWRL {0}\n'.format( self.d['scwrl'] )

        keys4 = ['missing_domain','domain_all_chains_pdb']
        if keys4[0]:
            pstr+= '\n---Missing Domain---\n'
            for k in keys4:
                pstr += "{0}: {1}\n".format(k, self.d[k])
        
        # This only used for printing
        INSERT_DOMAIN = False
        if self.d['domain_termini_distance'] > 0:
            INSERT_DOMAIN = True
        pstr += '\nIs an Insert Domain {0} termini distance {1}\n'.format( INSERT_DOMAIN, self.d['domain_termini_distance'] )
        
        # Now print out everything else
        pstr += "\n---Other parameters---\n"
        
        done_keys = keys1 + keys2 + keys3 + keys4 + [ 'use_scwrl', 'domain_termini_distance'  ]
        for k, v in sorted(self.d.items()):
            if k not in done_keys:
                pstr += "{0} : {1}\n".format( k, v )
                
        return pstr
    

if __name__ == "__main__":
    
    import sys
    import cPickle
    
    if len(sys.argv) == 2:
        pfile = sys.argv[1]
    else:
        pfile = "/opt/ample-dev1/examples/toxd-example/ROSETTA_MR_15/ample_results.pkl"
    
    f = open(pfile)
    d = cPickle.load(f)
    
    AD = AmpleOptions()
    for k,v in d.iteritems():
        AD.d[k] = v
        
    print AD.final_summary()