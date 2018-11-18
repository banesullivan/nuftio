"""
Helpers to get file names in specific working directory for Bane's datasci
project.

"""
import sys, os
PATH = '/Users/bane/Documents/school/Masters/RESEARCH/LLNL/Kimberlina1.2/prod07-sim0100-sim00199/'

SIM_DIR = r'sim01{:02}'
MESH_NAME = r'sim01{:02}.mesh_k16.prod07.trans.genmsh'
TMESH_NAME = r'sim01{:02}_mesh.json'
TARGET_DIR = 'W31-0.2'
ROCKTAB_NAME = r'sim01{:02}.usnt.rocktab'



def getSimDirName(sim):
     return os.path.join(PATH, SIM_DIR.format(sim))

def getMeshName(sim):
    return os.path.join(getSimDirName(sim), MESH_NAME.format(sim))

def getTMeshName(sim):
    return os.path.join(getSimDirName(sim), TMESH_NAME.format(sim))

def getRockTabName(sim):
    return os.path.join(os.path.join(getSimDirName(sim), TARGET_DIR), ROCKTAB_NAME.format(sim))

def getLookupTableName(sim):
    return os.path.join(getSimDirName(sim), 'lookup_table.csv')

def getLithDefName(sim):
    return os.path.join(getSimDirName(sim), 'lithologies.txt')

def getTargetDirName(sim):
    return os.path.join(getSimDirName(sim), TARGET_DIR)

def getLithMapName(sim):
    return os.path.join(getTargetDirName(sim), 'rocktab_mapper.csv')
