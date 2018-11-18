"""This modules holds all of the neccesarry functions and classes for reading
NUFT input data into the classes described in  :mod:`~nuftio.spec`.
"""
from __future__ import print_function

__displayname__ = 'File I/O'

__all__ = [
    'NuftMesh',
    'Parser',
    'read_genmsh',
    'read_rocktab',
    'read_usnt',
    'read_tab',

]

import properties
import discretize
import pandas as pd
import numpy as np
import cPyparsing as pyparsing
import time
import re
import sys
if sys.version_info < (3,):
    from StringIO import StringIO
else:
    from io import StringIO


from .spec import MeshSpecifications, RockType, USNT



class Parser(properties.HasProperties):
    """Parses NUFT data files"""
    COMMENTS = ";"

    @staticmethod
    def __toDict(lst, no=False):
        """An internal helper to handle parsing the ridiculously cumbersome
        NUFT data format into nested dictionaries."""
        if isinstance(lst[0], list):
            return Parser.__toDict(lst[0])
        key = lst[0]
        key = key.replace('-','_')
        values = lst[1::]
        # Check if there is an option
        if len(values) > 1 and not isinstance(values[0], list) and isinstance(values[1], list):
            #print('made an option:', values[0])
            values[0] = ['option', values[0]]
        # clean the values into a nested dict if needed
        #print(key, values)
        if len(values) < 1:
            tmp = key
            key ='option'
            values = tmp
        if isinstance(values[0], list) and len(values[0]) > 1:
            clean = {}
            for vs in values:
                k,v = Parser.__toDict(vs, no=True)
                if key == 'mat':
                    tmp = clean.get(k, {})
                    nk, nv = Parser.__toDict(v, no=True)
                    tmp2 = tmp.get(nk, [])
                    tmp2.append(nv)
                    tmp[nk] = tmp2
                    clean[k] = tmp
                else:
                    clean[k] = v
            values = clean
        if all(not isinstance(x, list) for x in values) and len(values) > 1:
            #print('passing', key, values)
            pass
        elif isinstance(values, list) and len(values) == 1:
            #print('did not pass', key, values)
            values = values[0]
        # return
        if no:
            return key, values
        return {key:values}


    @staticmethod
    def _createSpecs(dic):
        """Creates the proper specs for the input nested dictionary. The top
        level of values will be transformed to ``spec`` objects
        """
        pass

    @staticmethod
    def _readFileContents(filename, comments=';', skiprows=0):
        """Reads the contents of a file to a giant text string"""
        # Load in all the file lines
        text = np.genfromtxt(filename,
                            dtype=str,
                            delimiter='\n',
                            comments=comments)[skiprows::]
        return '\n'.join(text)


    @staticmethod
    def parseFile(filename, comments=';', skiprows=0, opener='(', closer=')'):
        """Parses general NUFT data file into a disctionary. If it is a table
        then use the ``parseTabFile`` method.
        """
        text = Parser._readFileContents(filename, comments=comments, skiprows=skiprows)
        # Run the parsing and get a nest list of the results
        return Parser.parseString(text, opener=opener, closer=closer)

    @staticmethod
    def parseString(text, opener='(', closer=')'):
        """Perses a string of text in NUFT data format to nested dictionaries"""
        start_time = time.time()
        print('Parsing...', end='\r')
        # Create the data block parser
        r = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'*+,-./:;<=>?@[\]^_`{|}~'
        se = pyparsing.nestedExpr(opener=opener, closer=closer, content=pyparsing.Word(r))
        # Run the parsing and get a nest list of the results
        results = se.parseString(text)
        results = results.asList()
        print('Parsed text in {} seconds'.format(time.time() - start_time))
        # Now turn that nested dictionary into data objects!
        data = Parser.__toDict(results)
        return data

    @staticmethod
    def parseTabFile(filename, comments=';', skiprows=0, opener='(', closer=')'):
        """Reads the NUFT table data format (``.tab`` files)."""
        # reade the file lines
        text = Parser._readFileContents(filename, comments=comments, skiprows=skiprows)
        # now find all tables
        TABLE = re.compile(r'\(table(.+?)\)', re.MULTILINE|re.DOTALL)
        tables = TABLE.findall(text)
        if len(tables) < 1:
            raise RuntimeError('No tables found in the iput file.')
        dfs = []
        # Now create pandas data frames of all the tables in that file
        for tab in tables:
            dfs.append(pd.read_table(StringIO(tables[0]), delim_whitespace=True, header=None))
        if len(dfs) == 1:
            # Id only one dataframe, return it
            return dfs[0]
        return dfs


# Now define the functions that we want to use

def read_genmsh(filename, comments=';', skiprows=0, opener='(', closer=')', usnt=False):
    """Reads genmsh specifiation files"""
    datadict = Parser.parseFile(filename, comments=comments, skiprows=skiprows, opener=opener, closer=closer)
    keys = list(datadict.keys())
    if len(keys) != 1:
        raise RuntimeError('This file is specifies too many/few data structures: {}'.format(keys))
    if keys[0] != 'genmsh':
        raise RuntimeError('The data type ({}) is not (genmsh).'.format(key[0]))
    # Okay we got a genmsh
    if usnt:
        return USNT._create(datadict[keys[0]])
    return MeshSpecifications._create(datadict[keys[0]])


def read_rocktab(filename, comments=';', skiprows=0, opener='(', closer=')'):
    """Reads rocktab material specification files"""
    datadict = Parser.parseFile(filename, comments=comments, skiprows=skiprows, opener=opener, closer=closer)
    keys = list(datadict.keys())
    if len(keys) != 1:
        raise RuntimeError('This file is specifies too many/few data structures: {}'.format(keys))
    if keys[0] != 'rocktab':
        raise RuntimeError('The data type ({}) is not (rocktab).'.format(key[0]))
    # Okay we got a rocktab
    tabs = {}
    for k, v in datadict[keys[0]].items():
        tabs[k] = RockType._create(k, v)
    return tabs


def read_usnt(fname_mesh, fname_rtab,  comments=';', skiprows=0, opener='(', closer=')'):
    """Reads mesh specifications and rock property table into one data object"""
    usnt = read_genmsh(fname_mesh, comments=comments, skiprows=skiprows, opener=opener, closer=closer, usnt=True)
    rocktab = read_rocktab(fname_rtab, comments=comments, skiprows=skiprows, opener=opener, closer=closer)
    usnt.rocktab = rocktab
    return usnt

def read_tab(filename, comments=';', skiprows=0, opener='(', closer=')'):
    """Reads the NUFT table data format (``.tab`` files)."""
    return Parser.parseTabFile(filename, comments=comments, skiprows=skiprows, opener=opener, closer=closer)



class NuftMesh(discretize.TensorMesh):
    """This is an extension of ``discretize``s ``TensorMesh`` to provide
    file IO for NUFT simulation results"""


    @classmethod
    def readNuft(TensorMesh, filename, fix_indices=True):
        """Run the Foo algorithm on an input number ``nub``.

        Args:
            filename (str): the relative or absolute file name
            fix_indices (bool): If True, decrease the indexing arrays by one
                because someone chose to use +1 indexing in the NUFT format.

        """
        # read the NUFT results using pandas because its a big ol table
        try:
            data = pd.read_table(filename, delim_whitespace=True)
        except (FileNotFoundError, IOError, OSError):
            raise RuntimeError('File ("{}") not found.'.format(filename))
        # Now use spatial refernce data to reconstruct the TensorMesh
        #- The array titles that should always be present and that we will use
        refs = ['index', 'i', 'j', 'k', 'x', 'dx', 'y', 'dy', 'z', 'dz', 'element_ref', 'nuft_ind']
        #- subtract one from indexing arrays because someone chose +1 indexing :(
        if fix_indices:
            data['index'] -= 1
            data['i'] -= 1
            data['j'] -= 1
            data['k'] -= 1
            data['element_ref'] -= 1
            data['nuft_ind'] -= 1
        #- Get the tensors on each axis
        xedge = data[data['j'] == 0]
        xedge = xedge[xedge['k'] == 0]
        yedge = data[data['i'] == 0]
        yedge = yedge[yedge['k'] == 0]
        zedge = data[data['i'] == 0]
        zedge = zedge[zedge['j'] == 0]
        xt = xedge['dx'].values
        yt = yedge['dy'].values
        zt = zedge['dz'].values
        # Find the origin
        odx = xedge[xedge['j'] == 0]
        ox = (odx['x'] - odx['dx']/2.).values[0]
        ody = yedge[yedge['i'] == 0]
        oy = (odx['y'] - odx['dy']/2.).values[0]
        odz = xedge[xedge['j'] == 0]
        oz = (odx['z'] - odx['dz']/2.).values[0]
        # Construct the TensorMesh
        mesh = TensorMesh([xt, yt, zt], x0=(ox, oy, oz))
        # Make a model dictionary
        data = data[[k for k in data.keys() if k not in refs]]
        models = dict()
        # Validate the mesh and models
        #TODO: mesh.validate()
        for name in data.keys():
            mod = data[name].values
            if mod.size != mesh.nC:
                raise RuntimeError('Number of elements ({}) in data array does not match number of cells ({}) in the mesh.'.format(mod.size, mesh.nC))
            models[name] = mod
        # Return the constructed mesh and models
        return mesh, models
