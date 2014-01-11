#!/usr/bin/env python
'''
Created on 19 Jul 2013

@author: jmht

Data we will be collecting:

Target:
length in AA
resolution in A
secondary structure (% and per AA)
?radius of gyration

Rosetta Models:
Score
maxsub cf target

Cluster:

Ensemble:
number of models (and their scores)
truncation level
number residues
side_chain_treatment

Solution
number (and identity? of residues)

shelxe rebuild:
* CC
* av. fragment length
* RMSD to native
* Maxsub to native
* TM to native

remac refined result
* reforigin score to native
* rmsd to native
* maxsub to native
* TM to native

TO THINK ABOUT
* multiple models/chains in native
* multiple chains in solution (e.g. 3PCV)

Strategy:
for each PDB structure
Extract Data (e.g. resolution,length) from native PDB.
Extract DSSP data from native DSSP file.
Extract secondary structure prediction (SSP) from fragment prediction.
Compare DSSP and SSP data.
Extract Maxsub and RMSD data from ROSETTA score file for all models.
For each result:
Determine the ensemble that generated the result.
Extract data on ensemble from serialised file for run.
Extract data on MRBUMP MR job from logfiles

Calculate RMSD:
Standardise native PDB (most probable conformation, HETATM etc.).
Loop over each chain in the native extracting chain to file:
Loop over each chain in refined PDB extracting to file
Calculate map between native and model - NEED FULL FILE?
strip native PDB to C-alpha atoms
create a PDB containing only those ATOMS from native that are in refined PDB
and renaming the chain and renumbering the atoms to match the refined PDB.
Use reforigin to compare.


'''

import cPickle
import csv
import glob
import os
import re
import shutil
import sys
import traceback
import types
import unittest

#sys.path.append("/Users/jmht/Documents/AMPLE/ample-dev1/python")
sys.path.append("/opt/ample-dev1/python")

import ample_util
import contacts
import csymmatch
import dssp
import maxcluster
import mrbump_results
import pdb_edit
import pdb_model
import phaser_parser
import reforigin
import residue_map
import shelxe_log

class AmpleResult(object):
    """Results for an ample solution"""
    
    def __init__(self):



        # The attributes we will be holding
        self.orderedAttrs = [ 
                              'pdbCode',
                              'title',
                              'fastaLength',
                              'numChains',
                              'estChainsASU',
                              'spaceGroup',
                              'resolution',
                              'solventContent',
                              'matthewsCoefficient',
                              'spaceGroup',
                              'ss_pred',
                              'ss_pred_str',
                              'ss_dssp',
                              'ss_dssp_str',
                              'resultDir',
                              'spickerClusterSize',
                              'spickerClusterCentroid',
                              'ensembleName',
                              'ensembleNumModels',
                              'ensembleNumResidues',
                              'ensemblePercentModel',
                              'ensembleSideChainTreatment',
                              'ensembleRadiusThreshold',
                              'ensembleTruncationThreshold',
                              'ensembleNativeRMSD',
                              'ensembleNativeTM',
                              'mrProgram',
                              'phaserLLG',
                              'phaserTFZ',
                              'phaserTime',
                              'phaserKilled',
                              'molrepScore',
                              'molrepTime',
                              'reforiginRMSD',
                              'floatingOrigin',
                              'csymmatchOriginOk',
                              'contactData',
                              'contactOrigin',
                              'numContacts',
                              'inregisterContacts',
                              'ooregisterContacts',
                              'backwardsContacts',
                              'goodContacts',
                              'nocatContacts',
                              'helixSequence',
                              'lenHelix',
                              'rfact',
                              'rfree',
                              'solution',
                              'shelxeCC',
                              'shelxeAvgChainLength',
                              'shelxeMaxChainLength',
                              'shelxeNumChains',
                              'shelxeCsymmatchShelxeScore',
                              'shelxeTM',
                              'shelxeTMPairs',
                              'shelxeRMSD',
                              ]
        
        # The matching titles
        self.orderedTitles = [  
                                "PDB Code",
                                "Title",
                                "Fasta Length",
                                "Number of Chains",
                                "Est. Chains in ASU",
                                "Space Group",
                                "Resolution",
                                "Solvent Content",
                                "Matthews Coefficient",
                                "Space Group",
                                "SS_Prediction Data",
                                "SS Prediction",
                                "DSSP Data",
                                "DSSP Assignment",
                                "Result Dir",
                                'Spicker cluster size',
                                'Spicker Centroid',
                                "Ensemble name",
                                "Ensemble num models",
                                "Ensemble num residues",
                                "Ensemble % of Model",
                                "Ensemble side chain",
                                "Ensemble radius thresh",
                                "Ensemble truncation thresh",
                                'Ensemble Native RMSD',
                                'Ensemble Native TM',
                                "MR program",
                                "Phaser LLG",
                                "Phaser TFZ",
                                "Phaser Time",
                                "Phaser Killed",
                                "Molrep Score",
                                "Molrep Time",
                                "Reforigin RMSD",
                                "Floating Origin",
                                "Csymmatch Origin OK",
                                "Contact Data",
                                "Contact origin",
                                "Number of contacts",
                                "In register contacts",
                                "Out of register contacts",
                                "Backwards contacts",
                                "Good contacts",
                                "Uncategorised contacts",
                                "Helix sequence",
                                "Helix length",
                                "Rfact",
                                "Rfree",
                                "Solution",
                                "Shelxe CC",
                                "Shelxe avg. chain length",
                                "Shelxe max. chain length",
                                "Shelxe num. chains",
                                "Shelxe Csymmatch Score",
                                "Shelxe TM Score",
                                "Shelxe TM Pairs",
                                "Shelxe RMSD",
                                 ]

        # Things not to output
        self.skip = [ "resultDir", "ss_pred", "ss_dssp", "contactData" ]
        
        # Set initial values
        for a in self.orderedAttrs:
            setattr( self, a, None )
        
        return
    
    def valuesAsList(self):
        return [ getattr(self, a) for a in self.orderedAttrs if a not in self.skip ]
    
    def titlesAsList(self):
#         l = []
#         for i, t in enumerate( self.orderedTitles ):
#             if self.orderedAttrs[i] not in self.skip:
#                 l.append( t )
#         return l
        return [ t for i, t in enumerate( self.orderedTitles ) if self.orderedAttrs[i] not in self.skip ]
    
    def asDict(self):
        """Return ourselves as a dict"""
        d = {}
        for a in self.orderedAttrs:
            d[ a ] = getattr(self, a)
        return d
    
    def __str__(self):
        
        s = ""
        for i, t in enumerate( self.orderedTitles ):
            if self.orderedAttrs[i] in self.skip:
                continue
            s += "{0:<26} : {1}\n".format( t, getattr( self, self.orderedAttrs[i] ) )
        return s
    
# End AmpleResult

class CompareModels(object):
    """Class to compare two models - currently with maxcluster"""
    
    def __init__(self, refModel, targetModel, workdir=None ):
        
        self.workdir = workdir
        
        self.refModel = refModel
        self.targetModel = targetModel
        
        self.grmsd = None
        self.maxsub = None
        self.pairs = None
        self.rmsd = None
        self.tm = None
        
        pdbedit = pdb_edit.PDBEdit()
        
        #print "CompareModels refModel: {0}  targetModel: {1}".format( refModel, targetModel )
        
        # If the rebuilt models is in multiple chains, we need to create a single chain
        nativePdbInfo = pdbedit.get_info( self.targetModel )
        if len( nativePdbInfo.models[0].chains ) > 1:
            #print "Coallescing targetModel into a single chain"
            n = os.path.splitext( os.path.basename( self.targetModel ) )[0]
            targetModel1chain = os.path.join( workdir, n+"_1chain.pdb" )
            pdbedit.to_single_chain( self.targetModel, targetModel1chain )
            self.targetModel = targetModel1chain
            
        # If the reference model is in multiple chains, we need to create a single chain
        nativePdbInfo = pdbedit.get_info( self.refModel )
        if len( nativePdbInfo.models[0].chains ) > 1:
            #print "Coallescing refModel into a single chain"
            n = os.path.splitext( os.path.basename( self.refModel ) )[0]
            refModel1chain = os.path.join( workdir, n+"_1chain.pdb" )
            pdbedit.to_single_chain( self.refModel, refModel1chain )
            self.refModel = refModel1chain
        
        self.run()
    
        return
    
    def run(self):
        
        n = os.path.splitext( os.path.basename( self.targetModel ) )[0]
        logfile = os.path.join( self.workdir, n+"_maxcluster.log" )
        
        # Run maxcluster in sequence independant mode
        cmd="/opt/maxcluster/maxcluster -in -e {0} -p {1}".format( self.targetModel, self.refModel ).split()
        retcode = ample_util.run_command(cmd=cmd, logfile=logfile, directory=os.getcwd(), dolog=False)
        
        if retcode != 0:
            raise RuntimeError,"Error running maxcluster!"
        
        self.parse_maxcluster_log( logfile )
        
        alignrsm = os.path.join( self.workdir, "align.rsm")
        
        n = os.path.splitext( os.path.basename( self.targetModel ) )[0]
        rootname = os.path.join( self.workdir, n )
        self.split_alignrsm( alignrsm=alignrsm, rootname=rootname )
        
        return
    
    def parse_maxcluster_log( self, logfile ):
        """Extract nativePdbInfo - assumes it completers in 1 iteration"""
        
        
        def _get_float( istr ):
            # Needed as we sometimes get spurious characters after the last digit
            nums = [ str(i) for i in range(10 ) ]
            if istr[-1] not in nums:
                istr = istr[:-1]
            return float(istr)
        
        for line in open( logfile , 'r' ):
            if line.startswith("Iter"):
                # colon after int
                iternum = int( line.split()[1][:-1] )
                if iternum > 1:
                    raise RuntimeError,"More than one iteration - no idea what that means..."
                
                if line.find( " Pairs=") != -1:
                    # e.g.: Iter 1: Pairs= 144, RMSD= 0.259, MAXSUB=0.997. Len= 144. gRMSD= 0.262, TM=0.997
                    # Need to remove spaces after = sign as the output is flakey - do it twice for safety
                    tmp = line.replace("= ","=")
                    tmp = tmp.replace("= ","=")
                    for f in tmp.split():
#                         if f.startswith("Pairs"):
#                             self.pairs = int( f.split("=")[1] )
                        if f.startswith("RMSD"):
                            self.rmsd = _get_float( f.split("=")[1] )
                        if f.startswith("MAXSUB"):
                            self.maxsub = _get_float( f.split("=")[1] )
                        if f.startswith("gRMSD"):
                            self.grmsd = _get_float( f.split("=")[1] )
                        if f.startswith("TM"):
                            self.tm = _get_float( f.split("=")[1] )
                            
                    # Bail out as we should be done
                    break
            
        return
    
    def split_alignrsm(self, alignrsm=None, rootname=None):
         
        # Order is experiment then assignment
 
        
        efile = rootname+"_experiment.pdb"
        pfile = rootname+"_prediction.pdb"
                 
        f = open( alignrsm, 'r' )
        line = f.readline()
         
        reading = False
        gotExp = False
        lines = []
        for line in open( alignrsm, 'r' ):
            
            # End of one of the files
            if line.startswith("TER"):
                lines.append( line )
                if not gotExp:
                    gotExp=True
                    f = open( efile, 'w' )
                else:
                    f = open( pfile, 'w' )
                    
                f.writelines( lines )
                f.close()
                lines = []
                reading=False
            
            if line.startswith("REMARK"):
                if not reading:
                    reading = True
                    
            if reading:
                lines.append( line )
        
        return
# End CompareModels



class EnsemblePdbParser(object):
    """
    Class to mine information from an ensemble pdb
    """

    def __init__(self,pdbfile):

        self.pdbfile = pdbfile
        
        self.centroidModelName = None
        self.modelNames = []
        self.models = []

        self.parse()

        return

    def parse(self):
        """parse"""

        # print os.path.join(os.getcwd(), logfile)

        capture=False
        for line in open(self.pdbfile, 'r'):
            
            if line.startswith( "REMARK   MODEL" ) and not capture:
                capture=True
                
            if capture and not line.startswith( "REMARK   MODEL" ):
                break
            
            if capture:
                fields = line.split()
                self.models.append( fields[3] )
                
        
        if not len( self.models ):
            raise RuntimeError,"Failed to get any models from ensemble!"
        
        for m in self.models:
            self.modelNames.append( os.path.splitext( os.path.basename( m ) )[0] )
            
        self.centroidModelName = self.modelNames[0]

        return

class MolrepLogParser(object):
    """
    Class to mine information from a 
    """

    def __init__(self,logfile):

        self.logfile = logfile

        self.score=None
        self.tfScore=None
        self.wrfac=None
        self.time = None

        self.parse()

        return

    def parse(self):
        """This just drops through reading each summary and so we are left with the last one"""

        fh=open(self.logfile)

        line=fh.readline()
        while line:
            
            if "--- Summary ---" in line:
                # really scrappy - just skip 3 and take whatever comes next
                fh.readline()
                fh.readline()
                fh.readline()
                line=fh.readline()
                fields = line.split()
                if len(fields) != 14:
                    raise RuntimeError,"Error reading summary for line: {0}".format( line )
                
                self.tfScore = float( fields[10] )
                self.wrfac = float( fields[11] )
                self.score= float( fields[12] )
                
            if line.startswith( "Times: User:" ):
                fields = line.split()
                time = fields[6]
                m,s = time.split(":")
                self.time = int(m)*60 + int(s)

            line=fh.readline()
        fh.close()

        return

class MrbumpLogParser(object):
    """
    Class to mine information from a 
    """

    def __init__(self,logfile):

        self.logfile = logfile

        self.noResTarget=0
        self.noChainsTarget=0
        self.resolution=0.0

        self.parse()

        return

    def parse(self):
        """parse"""

        fh=open(self.logfile)

        line=fh.readline()
        while line:
            if "Number of residues:" in line:
                self.noResTarget=int( line.split()[-1] )
            if "Estimated number of molecules to search for in a.s.u.:" in line:
                self.noChainsTarget=int( line.split()[-1] )
            if "Resolution of collected data (angstroms):" in line:
                self.resolution=float( line.split()[-1] )
            line=fh.readline()
        fh.close()

        return

class PsipredParser(object):
    """
    Class to mine information from a psipred format file
    """

    def __init__(self,pfile):

        self.psipredfile = pfile
        
        self.residues = []
        self.assignment = []
        self.percentH = None
        self.percentC = None
        self.percentE = None

        self.parse()

        return

    def parse(self):
        """parse"""

        # print os.path.join(os.getcwd(), logfile)

        self.residues = []
        self.assignment = []
        for i, line in enumerate( open(self.psipredfile, 'r') ):
            # Assume first 2 lines are not important
            if i < 2:
                continue
            
            if not line:
                break
            
            fields = line.split()
            if len(fields) != 6:
                raise RuntimeError,"Wrong number of fields in line: ",line
            
            idx, resid, pred = int(fields[0]), fields[1], fields[2]
            if 1 == 3 and idx != 1:
                raise RuntimeError,"Got wrong index for first data: ",line
            
            self.residues.append( resid )
            self.assignment.append( pred )
            
        
        if not len(self.residues) or not len( self.assignment):
            raise RuntimeError,"Got no assignment!"
        
        nH = 0
        nC = 0
        nE = 0
        for p in self.assignment:
            if p == "H":
                nH += 1
            elif p == "C":
                nC += 1
            elif p == "E":
                nE += 1
            else:
                raise RuntimeError,"Unrecognised assignment: {0}".format( p )
            
        self.percentC = float(nC) / len(self.assignment) * 100
        self.percentH = float(nH) / len(self.assignment) * 100
        self.percentE = float(nE) / len(self.assignment) * 100
            
            
        return

    def asDict(self):
        d = {}
        d['assignment'] = self.assignment
        d['residues'] = self.residues
        d['percentC'] = self.percentC
        d['percentE'] = self.percentE
        d['percentH'] = self.percentH
        
        return d
    
class RefmacLogParser(object):
    """
    Class to mine information from a phaser log
    """

    def __init__(self,logfile):

        self.logfile = logfile

        self.initRfree=1.0
        self.finalRfree=1.0
        self.initRfactor=1.0
        self.finalRfactor=1.0
        self.noResModel=0
        self.noChainsModel=0

        self.parse()

        return

    def parse(self):
        """parse"""

        # print os.path.join(os.getcwd(), logfile)
        fh = open(self.logfile, 'r')

        CAPTURE=False

        line=fh.readline()
        while line:
            if "Number of residues :" in line:
                self.noResModel=int( line.split()[-1] )
            if "Number of chains   :" in line:
                self.noChainsModel=int( line.split()[-1] )
            if CAPTURE:
                if "R free" in line:
                    self.initRfree=float( line.split()[-2] )
                    self.finalRfree=float( line.split()[-1] )
                    CAPTURE=False
                if "R factor" in line:
                    self.initRfactor=float( line.split()[-2] )
                    self.finalRfactor=float( line.split()[-1] )
            if " $TEXT:Result: $$ Final results $$" in line:
                CAPTURE=True
            line=fh.readline()
        fh.close()

        return

class RosettaScoreData(object):
    
    def __init__(self):
        self.score = None
        self.rms = None
        self.maxsub = None
        self.description = None
        self.model = None
        return

class RosettaScoreParser(object):
    
    def __init__(self, directory ):
        
        self.directory = directory
        
        self.avgScore = None
        self.topScore = None
        self.avgRms = None
        self.topRms = None
        self.avgMaxsub = None
        self.topMaxsub = None
        
        self.data = []
        
        score_file = os.path.join( directory, "score.fsc")
        self.parseFile( score_file )
        
    def parseFile(self, score_file ):
        for i, line in enumerate( open(score_file, 'r') ):
            
            if i == 0:
                continue
    
            line = line.strip()
            if not line: # ignore blank lines - not sure why they are there...
                continue
            
            d = RosettaScoreData()
            
            fields = line.split()
            d.score = float(fields[1])
            d.rms = float(fields[26])
            d.maxsub = float(fields[27])
            d.description = fields[ 31 ]
            #pdb = fields[31]
            
            d.model = os.path.join( self.directory, d.description+".pdb" )
            
            self.data.append( d )
        
        avg = 0
        self.topScore = self.data[0].score
        for d in self.data:
            avg += d.score
            if d.score < self.topScore:
                self.topScore = d.score
        self.avgScore  = avg / len(self.data)
        
        avg = 0
        self.topRms = self.data[0].rms
        for d in self.data:
            avg += d.rms
            if d.rms < self.topRms:
                self.topRms = d.rms
        self.avgRms  = avg / len(self.data)
        
        avg = 0
        self.topMaxsub = self.data[0].maxsub
        for d in self.data:
            avg += d.maxsub
            if d.maxsub > self.topMaxsub:
                self.topMaxsub = d.maxsub
        self.avgMaxsub  = avg / len(self.data)
        
        return
        
    def maxsubSorted(self, reverse=True ):
        return sorted( self.data, key=lambda data: data.maxsub, reverse=reverse )
     
    def rmsSorted(self, reverse=True ):
        return sorted( self.data, key=lambda data: data.rms, reverse=reverse )
    
    def rms(self, name):
        for d in self.data:
            if d.description == name:
                return d.rms
            
    def maxsub(self, name):
        for d in self.data:
            if d.description == name:
                return d.maxsub
    
    def __str__(self):
        s = "Results for: {0}\n".format(self.name)
        s += "Top score : {0}\n".format( self.topScore )
        s += "Avg score : {0}\n".format( self.avgScore )
        s += "Top rms   : {0}\n".format( self.topRms )
        s += "Avg rms   : {0}\n".format( self.avgRms )
        s += "Top maxsub: {0}\n".format( self.topMaxsub )
        s += "Avg maxsub: {0}\n".format( self.avgMaxsub )
        return s

class Test(unittest.TestCase):


    def testShelxeLogParser(self):
        logfile = "/media/data/shared/TM/2BHW/ROSETTA_MR_0/MRBUMP/cluster_1/search_poly_ala_trunc_9.355791_rad_3_molrep_mrbump/" + \
        "data/loc0_ALL_poly_ala_trunc_9.355791_rad_3/unmod/mr/molrep/build/shelxe/shelxe_run.log"
        
        p = shelxe_log.ShelxeLogParser( logfile )
        self.assertEqual(37.26, p.CC)
        self.assertEqual(7, p.avgChainLength)
        self.assertEqual(9, p.maxChainLength)
        self.assertEqual(1, p.cycle)
        self.assertEqual(14, p.numChains)
    


def processMrbump( mrbumpResult ):
    
    # Add attributes to object
    mrbumpResult.phaserLLG = None
    mrbumpResult.phaserTFZ = None
    mrbumpResult.phaserPdb = None
    mrbumpResult.phaserLog = None
    mrbumpResult.phaserTime = None
    mrbumpResult.molrepLog = None
    mrbumpResult.molrepScore = None
    mrbumpResult.molrepTime = None
    mrbumpResult.molrepPdb = None
    mrbumpResult.shelxePdb = None
    mrbumpResult.shelxeLog = None
    mrbumpResult.shelxeCC = None
    mrbumpResult.shelxeAvgChainLength = None
    mrbumpResult.shelxeMaxChainLength = None
    mrbumpResult.shelxeNumChains = None
    mrbumpResult.estChainsASU = None

    # Need to remove last component as we recored the refmac directory
    mrDir = os.sep.join( mrbumpResult.resultDir.split(os.sep)[:-1] )
    # HACK - we run the processing on cytosine so differnt place
    #/data2/jmht/coiled-coils/single_ensemble
    mrDir = mrDir.replace( "/data2/jmht/coiled-coils/single_ensemble","/media/data/shared/coiled-coils/single_model" )
    mrbumpResult.mrDir = mrDir
    
    mrbumpResult.ensembleName = mrbumpResult.name[9:-6]
    
    # Process log
    mrbumpP = MrbumpLogParser( mrbumpResult.mrbumpLog )
    mrbumpResult.estChainsASU = mrbumpP.noChainsTarget
    
    if mrbumpResult.program == "phaser":
        
        phaserPdb = os.path.join( mrDir,"refine","{0}_loc0_ALL_{1}_UNMOD.1.pdb".format(mrbumpResult.program, mrbumpResult.ensembleName) )
        if os.path.isfile( phaserPdb ):
            phaserP = phaser_parser.PhaserPdbParser( phaserPdb )
            mrbumpResult.phaserLLG = phaserP.LLG
            mrbumpResult.phaserTFZ = phaserP.TFZ
            mrbumpResult.phaserPdb = phaserPdb
            
            phaserLog = os.path.join( mrDir, "{0}_loc0_ALL_{1}_UNMOD.log".format(mrbumpResult.program, mrbumpResult.ensembleName) )
            mrbumpResult.phaserLog = phaserLog
            phaserP = phaser_parser.PhaserLogParser( phaserLog )
            mrbumpResult.phaserTime = phaserP.time
        
    elif mrbumpResult.program == "molrep":
        molrepLog = os.path.join( mrDir, "molrep.log" )
        mrbumpResult.molrepLog = molrepLog
        molrepP = MolrepLogParser( molrepLog )
        mrbumpResult.molrepScore = molrepP.score
        mrbumpResult.molrepTime = molrepP.time
        
        molrepPdb = os.path.join( mrDir,"refine","{0}_loc0_ALL_{1}_UNMOD.1.pdb".format(mrbumpResult.program, mrbumpResult.ensembleName) )
        if os.path.isfile( molrepPdb ):
            mrbumpResult.molrepPdb = molrepPdb
    else:
        assert False
        
    #
    # SHELXE PROCESSING
    #
    # Now read the shelxe log to see how we did
    shelxePdb = os.path.join( mrDir, "build/shelxe", "shelxe_{0}_loc0_ALL_{1}_UNMOD.pdb".format( mrbumpResult.program, mrbumpResult.ensembleName ) )
    if os.path.isfile( shelxePdb):
        mrbumpResult.shelxePdb = shelxePdb
        
    shelxeLog = os.path.join( mrDir, "build/shelxe/shelxe_run.log" )
    if os.path.isfile( shelxeLog ):
        mrbumpResult.shelxeLog = shelxeLog
        shelxeP = shelxe_log.ShelxeLogParser( shelxeLog )
        mrbumpResult.shelxeCC = shelxeP.CC
        mrbumpResult.shelxeAvgChainLength = shelxeP.avgChainLength
        mrbumpResult.shelxeMaxChainLength = shelxeP.maxChainLength
        mrbumpResult.shelxeNumChains= shelxeP.numChains
    
    return

def analyseSolution( ampleResult=None,
                     nativePdbInfo=None,
                     nativeAs1Chain=None,
                     refModelPdbInfo=None,
                     resSeqMap=None,
                     originInfo=None,
                     dsspLog=None,
                     workdir=None ):


    if ampleResult.mrProgram == "phaser":
        placedPdb = ampleResult.phaserPdb
    elif ampleResult.mrProgram == "molrep":
        placedPdb = ampleResult.molrepPdb
    else:
        assert False

    if placedPdb is None:
     #print "NO PDB FOR ",ampleResult
     return
    #else:
    # print "GOT PDB FOR ",ampleResult

    # debug - copy into work directory as reforigin struggles with long pathnames
    shutil.copy(placedPdb, os.path.join( workdir, os.path.basename( placedPdb ) ) )
    
    placedPdbInfo = pdbedit.get_info( placedPdb )
    
    # Get reforigin info
    if True:
    #try:
        rmsder = reforigin.ReforiginRmsd()
        rmsder.getRmsd(  nativePdbInfo=nativePdbInfo,
                         placedPdbInfo=placedPdbInfo,
                         refModelPdbInfo=refModelPdbInfo,
                         cAlphaOnly=True )
        ampleResult.reforiginRMSD = rmsder.rmsd
    #except Exception, e:
    #    print "ERROR: ReforiginRmsd with: {0} {1}".format( nativePdbInfo.pdb, placedPdbInfo.pdb )
    #    print "{0}".format( e )
    #    ampleResult.reforiginRMSD = 9999
         
    #
    # SHELXE PROCESSING
    #
    if not ampleResult.shelxePdb is None and os.path.isfile( ampleResult.shelxePdb ):
        # Need to copy to avoid problems with long path names
        shelxePdb = os.path.join(workdir, os.path.basename( ampleResult.shelxePdb ) )
        shutil.copy( ampleResult.shelxePdb, shelxePdb )
        
        csym                           = csymmatch.Csymmatch()
        shelxeCsymmatchPdb             = ample_util.filename_append( 
                                                                    filename=shelxePdb, 
                                                                    astr="csymmatch", 
                                                                    directory=workdir )
        
        # Had problem with shelx losing origin information
        csym.run( refPdb=nativePdbInfo.pdb, inPdb=shelxePdb, outPdb=shelxeCsymmatchPdb )
        shelxeCsymmatchOrigin = csym.origin()
        
        # See if this origin is valid
        ampleResult.floatingOrigin = originInfo.isFloating()
        ampleResult.csymmatchOriginOk = True
        if not shelxeCsymmatchOrigin or \
        ( shelxeCsymmatchOrigin not in originInfo.redundantAlternateOrigins() and not ampleResult.floatingOrigin ):
            ampleResult.csymmatchOriginOk   = False
            shelxeCsymmatchOrigin  = None
        
        ampleResult.shelxeCsymmatchShelxeScore  = csym.averageScore()
        shelxeCsymmatchPdbSingle       = ample_util.filename_append( filename=shelxeCsymmatchPdb, 
                                                                     astr="1chain", 
                                                                     directory=workdir )
        pdbedit.to_single_chain(shelxeCsymmatchPdb, shelxeCsymmatchPdbSingle)
        
        # Compare the traced model to the native with maxcluster
        # We can only compare one chain so we extracted this earlier
        maxComp = maxcluster.Maxcluster()
        d = maxComp.compareSingle( nativePdb=nativeAs1Chain,
                                   modelPdb=shelxeCsymmatchPdbSingle,
                                   sequenceIndependant=True,
                                   rmsd=False
                                 )
        ampleResult.shelxeTM = d.tm
        ampleResult.shelxeTMPairs = d.pairs
        
        d = maxComp.compareSingle( nativePdb=nativeAs1Chain,
                                   modelPdb=shelxeCsymmatchPdbSingle,
                                   sequenceIndependant=True,
                                   rmsd=True )
        ampleResult.shelxeRMSD = d.rmsd

        # Now calculate contacts
    
        # Only bother when we have a floating origin if the csymmatch origin is ok
        if not ampleResult.floatingOrigin or ( ampleResult.floatingOrigin and ampleResult.csymmatchOriginOk ):
            ccalc = contacts.Contacts()
            #try:
            if True:
                ccalc.getContacts( placedPdbInfo=placedPdbInfo,
                                   nativePdbInfo=nativePdbInfo,
                                   resSeqMap=resSeqMap,
                                   originInfo=originInfo,
                                   shelxeCsymmatchOrigin=shelxeCsymmatchOrigin,
                                   workdir=workdir,
                                   dsspLog=dsspLog
                                )
            #except Exception, e:
            #    print "ERROR WITH CONTACTS: {0}".format( e )
       
            if ccalc.best:
                ampleResult.contactData        = ccalc.best
                ampleResult.numContacts        = ccalc.best.numContacts
                ampleResult.inregisterContacts = ccalc.best.inregister
                ampleResult.ooregisterContacts = ccalc.best.ooregister
                ampleResult.backwardsContacts  = ccalc.best.backwards
                ampleResult.contactOrigin      = ccalc.best.origin
                ampleResult.goodContacts       = ampleResult.inregisterContacts + ampleResult.ooregisterContacts
                ampleResult.nocatContacts      = ampleResult.numContacts - ampleResult.goodContacts
                ampleResult.helixSequence      = ccalc.best.helix
                if ccalc.best.helix:
                    ampleResult.lenHelix = len( ccalc.best.helix )
                
                gotHelix=False
                hfile = os.path.join( workdir, "{0}.helix".format( ampleResult.ensembleName ) )
                gotHelix =  ccalc.writeHelixFile( hfile )
                        
                # Just for debugging
                if ampleResult.shelxeCC >= 25 and ampleResult.shelxeAvgChainLength >= 10 and not gotHelix:
                    print "NO HELIX FILE"

    return

if __name__ == "__main__":
    
    pickledResults=False
    CLUSTERNUM=0
    #dataRoot = "/Users/jmht/Documents/AMPLE/data"
    dataRoot = "/media/data/shared/coiled-coils/ensemble"
    
    rundir = "/home/jmht/Documents/test/CC/run2"
    rundir = os.getcwd()
    os.chdir( rundir )
    
    if pickledResults:
        pfile = os.path.join( dataRoot,"results.pkl" )
        with open( pfile ) as f:
            resultsDict = cPickle.load( f  )
    
    allResults = []
    
    for pdbCode in [ l.strip() for l in open( os.path.join( dataRoot, "dirs.list") ) if not l.startswith("#") ]:
    #for pdbCode in sorted( resultsDict.keys() ):
    #for pdbCode in [ "1BYZ" ]:
        
        workdir = os.path.join( rundir, pdbCode )
        if not os.path.isdir( workdir ):
            os.mkdir( workdir )
        os.chdir( workdir )
            
        print "\nResults for ",pdbCode
        
        # Directory where all the data for this run live
        dataDir = os.path.join( dataRoot, pdbCode )
        
        # Get the path to the original pickle file
        pfile = os.path.join( dataDir, "ROSETTA_MR_0/resultsd.pkl")
        with open( pfile ) as f:
            ampleDict = cPickle.load( f  )
    
        # First process all stuff that's the same for each structure
        
        # Get path to native Extract all the nativePdbInfo from it
        nativePdb = os.path.join( dataDir, "{0}.pdb".format( pdbCode ) )
        pdbedit = pdb_edit.PDBEdit()
        nativePdbInfo = pdbedit.get_info( nativePdb )
        
        # First check if the native has > 1 model and extract the first if so
        if len( nativePdbInfo.models ) > 1:
            print "nativePdb has > 1 model - using first"
            nativePdb1 = ample_util.filename_append( filename=nativePdb, astr="model1", directory=workdir )
            pdbedit.extract_model( nativePdb, nativePdb1, modelID=nativePdbInfo.models[0].serial )
            nativePdb = nativePdb1
            
        # Standardise the PDB to rename any non-standard AA, remove solvent etc
        nativePdbStd = ample_util.filename_append( filename=nativePdb, astr="std", directory=workdir )
        pdbedit.standardise( nativePdb, nativePdbStd )
        nativePdb = nativePdbStd
        
        # Get the new Info about the native
        nativePdbInfo = pdbedit.get_info( nativePdb )
        
        # Get information on the origins for this spaceGroup
        originInfo = pdb_model.OriginInfo( spaceGroupLabel=nativePdbInfo.crystalInfo.spaceGroup )

        # For maxcluster comparsion of shelxe model we need a single chain from the native so we get this here
        if len( nativePdbInfo.models[0].chains ) > 1:
            chainID = nativePdbInfo.models[0].chains[0]
            nativeAs1Chain  = ample_util.filename_append( filename=nativePdbInfo.pdb,
                                                           astr="1chain".format( chainID ), 
                                                           directory=workdir )
            pdbedit.to_single_chain( nativePdbInfo.pdb, nativeAs1Chain )
        else:
            nativeAs1Chain = nativePdbInfo.pdb
        
        
        # Get hold of a full model so we can do the mapping of residues
        refModelPdb = os.path.join( dataDir, "models/S_00000001.pdb".format( pdbCode ) )
        resSeqMap = residue_map.residueSequenceMap()
        refModelPdbInfo = pdbedit.get_info( refModelPdb )
        resSeqMap.fromInfo( refInfo=refModelPdbInfo,
                            refChainID=refModelPdbInfo.models[0].chains[0], # Only 1 chain in model
                            targetInfo=nativePdbInfo,
                            targetChainID=nativePdbInfo.models[0].chains[0]
                          )
        
        # Get the scores for the models - we use both the rosetta and maxcluster methods as maxcluster
        # requires a separate run to generate total RMSD
        modelsDirectory = os.path.join( dataDir, "models")
        scoreP = RosettaScoreParser( modelsDirectory )
        maxComp = maxcluster.Maxcluster()
        maxComp.compareDirectory( nativePdbInfo=nativePdbInfo,
                                  resSeqMap=resSeqMap,
                                  modelsDirectory=modelsDirectory,
                                  workdir=workdir )
        
        # Secondary Structure assignments
        #sam_file = os.path.join( dataDir, "fragments/t001_.rdb_ss2"  )
        psipred_file = os.path.join( dataDir, "fragments/t001_.psipred_ss2"  )
        psipredP = PsipredParser( psipred_file )
        dsspLog = os.path.join( dataDir, "{0}.dssp".format( pdbCode  )  )
        dsspP = dssp.DsspParser( dsspLog )
        
        # Loop over each result
        if pickledResults:
            results = resultsDict[ pdbCode ]
        else:
            r = mrbump_results.ResultsSummary( os.path.join( dataDir, "ROSETTA_MR_0/MRBUMP/cluster_1") )
            r.extractResults()
            results = r.results
        
        #jtest=0
        for mrbumpResult in results:
            
            #jtest += 1
            #if jtest > 1:
            #    break
            
            print "processing result ",mrbumpResult.name
            
            ar = AmpleResult()
            allResults.append( ar )
            
            ar.pdbCode = pdbCode
            ar.title = nativePdbInfo.title
            ar.fastaLength = ampleDict['fasta_length']
            ar.spickerClusterSize = ampleDict['spicker_results'][ CLUSTERNUM ].cluster_size
            ar.spickerClusterCentroid = os.path.splitext( os.path.basename( ampleDict['spicker_results'][ CLUSTERNUM ].cluster_centroid ) )[0]
            ar.numChains = len( nativePdbInfo.models[0].chains )
            ar.resolution = nativePdbInfo.resolution
            ar.solventContent = nativePdbInfo.solventContent
            ar.matthewsCoefficient = nativePdbInfo.matthewsCoefficient
            ar.spaceGroup = originInfo.spaceGroup()
            
            ar.ss_pred = psipredP.asDict()
            ar.ss_pred_str = "C:{0:d} | E:{1:d} | H:{2:d}".format( int(psipredP.percentC),  int(psipredP.percentE), int(psipredP.percentH) )
            ar.ss_dssp = dsspP.asDict()
            ar.ss_dssp_str = "C:{0:d} | E:{1:d} | H:{2:d}".format( int(dsspP.percentC[0]),  int(dsspP.percentE[0]), int(dsspP.percentH[0]) )
            
            # yuck...
            if mrbumpResult.solution == 'unfinished':
                s = mrbumpResult.name.split("_")
                # Different for CC and TM cases
                #ensembleName = "_".join( s[2:-2] )
                ensembleName = "_".join( s[2:-1] )
            else:
                # MRBUMP Results have loc0_ALL_ prepended and  _UNMOD appended
                ensembleName = mrbumpResult.name[9:-6]
            ar.ensembleName = ensembleName
            
            #if ensembleName != "SCWRL_reliable_sidechains_trunc_0.005734_rad_1":
            #   continue
            
            # Extract information on the models and ensembles
            eresults = ampleDict['ensemble_results']
            got=False
            for e in ampleDict[ 'ensemble_results' ][ CLUSTERNUM ]:
                if e.name == ensembleName:
                    got=True
                    break 
        
            if not got:
                raise RuntimeError,"Failed to get ensemble results"
        
            ar.ensembleNumModels =  e.num_models
            ar.ensembleNumResidues =  e.num_residues
            ar.ensembleSideChainTreatment = e.side_chain_treatment
            ar.ensembleRadiusThreshold = e.radius_threshold
            ar.ensembleTruncationThreshold =  e.truncation_threshold
            ar.ensemblePercentModel = int( ( float( ar.ensembleNumResidues ) / float( ar.fastaLength ) ) * 100 )
            
            # Get the data on the models in the ensemble
            ensembleFile = os.path.join( dataDir, "ROSETTA_MR_0/ensembles_1", ensembleName+".pdb" )
            eP = EnsemblePdbParser( ensembleFile )
            
            ar.ensembleNativeRMSD = scoreP.rms( eP.centroidModelName )
            ar.ensembleNativeTM = maxComp.tm( eP.centroidModelName )
    
            ar.solution =  mrbumpResult.solution
            
            # No results so move on
            if mrbumpResult.solution == 'unfinished':
                ar.solution = mrbumpResult.solution
                continue
            
            # process MRBUMP solution here
            #mrbumpLog = os.path.join( dataDir, "ROSETTA_MR_0/MRBUMP/cluster_1/", "{0}_{1}.sub.log".format( ensembleName, mrbumpResult.program )  )
            mrbumpLog = os.path.join( dataDir, "ROSETTA_MR_0/MRBUMP/cluster_1/", "{0}.sub.log".format( ensembleName ) )
            mrbumpResult.mrbumpLog = mrbumpLog
            
           # Update the Mrbump result object and set all values in the Ample Result
            processMrbump( mrbumpResult )
    
            # Now set result attributes from what we've got
            ar.solution =  mrbumpResult.solution
            ar.resultDir = mrbumpResult.mrDir
            ar.rfact =  mrbumpResult.rfact
            ar.rfree =  mrbumpResult.rfree
            ar.mrProgram =  mrbumpResult.program
        
            if mrbumpResult.program == "phaser":
                #ar.phaserLog = mrbumpResult.phaserLog
                ar.phaserLLG = mrbumpResult.phaserLLG
                ar.phaserTFZ = mrbumpResult.phaserTFZ
                ar.phaserPdb = mrbumpResult.phaserPdb
                ar.phaserTime = mrbumpResult.phaserTime
            elif mrbumpResult.program == "molrep":
                #ar.molrepLog = mrbumpResult.molrepLog
                ar.molrepScore = mrbumpResult.molrepScore
                ar.molrepTime = mrbumpResult.molrepTime
                ar.molrepPdb = mrbumpResult.molrepPdb
            else:
                raise RuntimeError,"Unrecognised program!"
            
            #ar.shelxeLog = mrbumpResult.shelxeLog
            ar.shelxePdb = mrbumpResult.shelxePdb
            ar.shelxeCC = mrbumpResult.shelxeCC
            ar.shelxeAvgChainLength = mrbumpResult.shelxeAvgChainLength
            ar.shelxeMaxChainLength = mrbumpResult.shelxeMaxChainLength
            ar.shelxeNumChains = mrbumpResult.shelxeNumChains
            ar.estChainsASU = mrbumpResult.estChainsASU
            
            # Now process the result
            try:
                analyseSolution( ampleResult=ar,
                                 nativePdbInfo=nativePdbInfo,
                                 nativeAs1Chain=nativeAs1Chain,
                                 refModelPdbInfo=refModelPdbInfo,
                                 resSeqMap=resSeqMap,
                                 originInfo=originInfo,
                                 dsspLog=dsspLog,
                                 workdir=workdir )
            except Exception,e:
                print "ERROR ANALYSING SOLUTION: {0} {1}".format( pdbCode, mrbumpResult.ensembleName )
                print traceback.format_exc()
            
            
            #print ar

    # End loop over results
    #sys.exit(1)
    
    pfile = os.path.join( rundir, "ar_results.pkl")
    f = open( pfile, 'w' )
    ampleDict = cPickle.dump( allResults, f  )
    
    cpath = os.path.join( rundir, 'results.csv' )
    csvfile =  open( cpath, 'wb')
    csvwriter = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    header=False
    for r in allResults:
        if not header:
            csvwriter.writerow( r.titlesAsList() )
            header=True
        csvwriter.writerow( r.valuesAsList() )
        
    csvfile.close()
