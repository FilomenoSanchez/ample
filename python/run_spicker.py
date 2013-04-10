#!/usr/bin/env python


import glob
import logging
import os
import re
import shutil
import subprocess


class SpickerResult( object ):
    """
    A class to hold the result of running Spicker
    """

    def __init__(self):

        self.cluster_directory = None
        self.cluster_size = None
        self.cluster_centroid = None
        self.pdb = [] # ordered list of the pdbs in their results directory
        self.rosetta_pdb = [] # ordered list of the pdbs in the rosetta directory
        self.r_nat = [] # ordered list of the rnat values for each pdb


class SpickerCluster( object ):

    def __init__(self, amoptd ):
        """Initialise from a dictionary of options"""
        
        self.rundir = amoptd['spicker_rundir']
        self.clusterdir = amoptd['spicker_clusterdir']
        self.spicker_exe =  amoptd['spicker_exe']
        self.models_dir = amoptd['models_dir']
        self.num_clusters = amoptd['num_clusters']
        self.results = None

        self.logger = logging.getLogger()
        
    ###############
    def get_length(self, pdb):
        pdb = open(pdb)
        counter = 0
        for line in pdb:
            pdb_pattern = re.compile('^ATOM')
            pdb_result = pdb_pattern.match(line)
            if pdb_result:
                atom = line[13:16]
                if re.search('CA', atom):
                    counter+=1
    
        # print counter
        return str(counter)

    #################
    def create_input_files(self):
    
        """
        jmht
        Create the input files required to run spicker
    
        path: PATH_TO_MODELS
        outpath: RunDir+'/spicker_run'
    
        (See notes in spicker.f FORTRAN file for a description of the required files)
    
        """

        #os.chdir( self.rundir )
        
        pdbname = ''
        list_string = ''
        counter = 0
    
        # Input file for spicker with coordinates of the CA atoms for each of the PDB structures
        read_out = open( 'rep1.tra1', "w")
    
        #jmht - a list of the full path of all PDBs - used so we can loop through it and copy the selected
        # ones to the relevant directory after we have run spicker
        file_list = open( 'file_list', "w")
    
        for infile in glob.glob( os.path.join(self.models_dir,  '*.pdb') ):
            name = re.split('/', infile)
    
            pdbname = str(name.pop())
            file_list.write(infile + '\n')
            list_string = list_string + pdbname+ '\n'
            counter +=1
            read = open(infile)
    
            length = self.get_length(infile)
    
            read_out.write('\t' + length + '\t926.917       '+str(counter)+'       '+str(counter)+'\n')
            for line in read:
                #print line
                pattern = re.compile('^ATOM\s*(\d*)\s*(\w*)\s*(\w*)\s*(\w)\s*(\d*)\s*(.\d*.\d*)\s*(.\d*.\d*)\s*(.\d*.\d*)\s*(.\d*.\d*)')
                result = re.match(pattern, line)
                if result:
                    split = re.split(pattern, line)
                    #print line
                    #print split
                # print '\t' + split[5] + '\t' + split[6] + '\t' +split[7]
                    if split[2] == 'CA':
                        read_out.write( '     ' + split[6] + '     ' + split[7] + '     ' +split[8] + '\n' )
    
            read.close()
        file_list.close()
        #print list_string
        #make rmsinp
        #length = get_length(path + '/' + pdbname)
    
    
        rmsinp = open('rmsinp', "w")
        rmsinp.write('1  ' + length + '\n\n')
        rmsinp.write(length + '\n')
        rmsinp.close()
        #make tra.in
        tra = open('tra.in', "w")
        tra.write('1 -1 1 \nrep1.tra1')
    
        tra.close()
    
        # Create the file with the sequence of the PDB structures
        seq = open('seq.dat', "w")
        a_pdb = open( os.path.join( self.models_dir, pdbname ), 'r' )
        for line in a_pdb:
            #print line
            pattern = re.compile('^ATOM\s*(\d*)\s*(\w*)\s*(\w*)\s*(\w)\s*(\d*)\s*(\d*)\s')
            result = re.match(pattern, line)
            if result:
                split = re.split(pattern, line)
                #print line
            # print split
                if split[2] == 'CA':
                    seq.write('\t' +split[5] + '\t' + split[3] + '\n')
    ################
    
    
    def run_spicker(self):
        """
        Run spicker to cluster the models
        """
    
    
        if not os.path.isdir( self.rundir ):
            os.mkdir( self.rundir )
        
        os.chdir(self.rundir)
        
        self.logger.debug("Running spicker in directory: {0}".format( self.rundir ) )
            
        self.create_input_files()
        
        p = subprocess.Popen( self.spicker_exe, shell=True, stdin = subprocess.PIPE,
                                       stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
    
        
        # Create directory to hold all clusters
        if not os.path.exists( self.clusterdir ):
            os.mkdir( self.clusterdir )   
        
        # Read the log and generate the results
        results = self.process_log()
        
        # Loop through each cluster copying the files as we go
        # We only process the clusters we will be using
        MAXCLUSTER=200 # max number of pdbs in a cluster
        for cluster in range( self.num_clusters ):
            
            cur_clusterdir = os.path.join( self.clusterdir, "cluster_"+str(cluster+1) )
            if not os.path.exists( cur_clusterdir ):
                os.mkdir( cur_clusterdir )
                
            result = results[ cluster ]
            result.cluster_directory = cur_clusterdir
            for i, pdb in enumerate( result.rosetta_pdb ):
                
                if i > MAXCLUSTER:
                    result.cluster_size = MAXCLUSTER
                    break
                
                fname = os.path.split( pdb )[1]
                shutil.copy( pdb, result.cluster_directory )
                
                result.pdb.append( fname )
                
                if i == 0:
                    result.cluster_centroid = fname
        
        self.results = results
        
        return
                
    def process_log( self, logfile=None ):
        """Read the spicker str.txt file and return a list of SpickerResults for each cluster.
        
        We use the R_nat value to order the files in the cluster
        """
        
        if not logfile:
            logfile = os.path.join(self.rundir, 'str.txt')
            
        clusterCounts = []
        index2rnats = []
        
        # File with the spicker results for each cluster
        self.logger.debug("Processing spicker output file: {0}".format(logfile))
        f = open( logfile, 'r' )
        line = f.readline()
        while line:
            line = line.strip()
            
            if line.startswith("#Cluster"):
                ncluster = int( line.split()[1] )
                
                # skip 2 lines to Nstr
                f.readline()
                f.readline()
                
                line = f.readline().strip()
                if not line.startswith("Nstr="):
                    raise RuntimeError,"Problem reading file: {0}".format( logfile )
                
                ccount = int( line.split()[1] )
                clusterCounts.append( ccount )
                
                # Loop through this cluster
                i2rnat = []
                line = f.readline().strip()
                while not line.startswith("------"):
                    fields = line.split()
                    i2rnat.append( ( int(fields[5]), float( fields[3] ) ) )
                    line = f.readline().strip()
                    
                index2rnats.append( i2rnat )
            
            line = f.readline()
                
        # Sort clusters by the R_nat
        for i,l in enumerate(index2rnats):
            sorted_by_rnat = sorted(l, key=lambda tup: tup[1])
            index2rnats[i] = sorted_by_rnat
    
        # Now map the indices to their files
        
        # Get ordered list of the pdb files
        flist = os.path.join( self.rundir, 'file_list')
        pdb_list = [ line.strip() for  line in open( flist , 'r' ) ]
        
        results = []
        # create results
        for c in range( len( clusterCounts ) ):
            r = SpickerResult()
            r.cluster_size = clusterCounts[ c ]
            for i, rnat in index2rnats[ c ]:
                pdb = pdb_list[i-1]
                r.rosetta_pdb.append( pdb )
                r.r_nat.append( rnat )
            
            results.append( r )
            
        return results
        
    def results_summary(self):
        """Summarise the spicker results"""
        
        if not self.results:
            raise RuntimeError, "Could not find any results!"
        
        
        rstr = "---- Spicker Results ----\n\n"
        
        for i, r in enumerate( self.results ):
            rstr += "Cluster: {0}\n".format(i+1)
            rstr += "* number of models: {0}\n".format( r.cluster_size )
            if i <= self.num_clusters-1:
                rstr += "* files are in directory: {0}\n".format( r.cluster_directory )
                rstr += "* centroid model is: {0}\n".format( r.cluster_centroid )
            rstr += "\n"
            
        return rstr
        
#################
#def check_pid_by_kill(pid):
#    """ Check For the existence of a unix pid. """
#    try:
#        os.kill(pid, 0)
#    except OSError:
#        return False
#    else:
#        return True
###################
#def check_pid(pid):
# if os.path.exists('/proc/'+str(pid)):
#   return True
# else:
#   return False


if __name__ == "__main__":

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)

    root = "/opt/ample-dev1/examples/toxd-example/ROSETTA_MR_0"
    optd = { 'spicker_rundir' : os.path.join( root, 'spicker_run'),
            'spicker_clusterdir' : os.path.join( root, 'S_clusters'),
            'spicker_exe' : '/opt/spicker/spicker',
            'models_dir': os.path.join( root, 'models' ),
            'num_clusters' : 3
            }

    spicker = SpickerCluster( optd )
    spicker.run_spicker()
    print spicker.results_summary()
    #spicker_results = spicker.get_results()

    #run_spicker(models, spicker_run_dir, spickerexe, no_clusters_sampled, overpath)
