from __future__ import print_function

__all__ = [
    'MeshSpecifications',
    'RockType',
    'USNT',
]

__displayname__ = 'Specifications'

import numpy as np
import pandas as pd
import properties
import copy
import warnings
import time
import discretize


class MaterialComponent(properties.HasProperties):
    """Defines the extent of a material component in the grid"""

    i =  properties.Array('Range of element indices in the X-direction',
            shape=(2,),
            dtype=int,)

    j =  properties.Array('Range of element indices in the Y-direction',
            shape=(2,),
            dtype=int,)

    k =  properties.Array('Range of element indices in the Z-direction',
            shape=(2,),
            dtype=int,)



class MeshSpecifications(properties.HasProperties):
    """specifies the mesh geometry, element material types and names as well as
    dual permeability parameters and radiation parameters.
    """

    coord = properties.String(
            'specifies the type of mesh that will be generated',
            change_case='lower',
            )

    @properties.validator
    def _validate_mesh_type(self):
        """Check mesh type is one of two valid options: 'rect' or 'cylind'"""
        if self.coord not in ['rect', 'cylind']:
            raise properties.ValidationError("Mesh type ('{}') not a valid mesh type. Only 'rect' and 'cylind' are suppurted".format(self.coord))
        return True

    down = properties.Array(
            'Vector orientation of down direction and in the direction of ' +
            'the gravity vector.',
            dtype=float,
            shape=(3,))

    dx = properties.Array(
            "widths of the mesh in the X-dimension",
            dtype=float,
            shape=("*",))

    dy = properties.Array(
            "widths of the mesh in the Y-dimension",
            dtype=float,
            shape=("*",))

    dz = properties.Array(
            "widths of the mesh in the Z-dimension",
            dtype=float,
            shape=("*",))

    mat = properties.Dictionary(
            'The materials int the model space.',
            key_prop=properties.String('The element name prefix', change_case='lower'),
            value_prop=properties.Dictionary('The material types',
                key_prop=properties.String('The material type. Must have a corresponding entry in the material type the ``rocktab``.'),
                value_prop=properties.List('ther material components', MaterialComponent)
            )
        )

    @property
    def nx(self):
        return len(self.dx)

    @property
    def ny(self):
        return len(self.dy)

    @property
    def nz(self):
        return len(self.dz)

    @property
    def nC(self):
        return (self.nx * self.ny * self.nz)

    @property
    def shape(self):
        return (self.nx, self.ny, self.nz)

    # Optional
    #anistotrpoic
    #wrap_around
    #radcon

    @staticmethod
    def __pasrseCellList(line):
        line_list = []
        for seg in line:
            if '*' in seg:
                sp = seg.split('*')
                seg_arr = np.ones((int(sp[0]),), dtype=float) * float(sp[1])
            else:
                seg_arr = np.array([float(seg)], dtype=float)
            line_list.append(seg_arr)
        return np.concatenate(line_list)

    @classmethod
    def _create(cls, values, validate=False):
        if not isinstance(values, dict):
            raise RuntimeError('Input values must be a dictionary')
        start_time = time.time()
        #print('Creating Mesh Specs...', end='\r')
        props = cls()
        mat = values.pop('mat')
        save = copy.deepcopy(mat)
        for k, v in values.items():
            if k in cls._props:
                # If the value is simple, set it!
                if isinstance(cls._props[k], properties.String):
                    p = props._props.get(k)
                    props._set(k, p.from_json(v))
                else:
                    # anything that isnt a mat is a list of floats
                    # make sure to fix any repetitve values us '*' notations
                    vals = MeshSpecifications.__pasrseCellList(v)
                    props._set(k, vals)
            else:
                #warnings.warn("({}:{}) property is not valid.".format(k, v))
                pass
        # Now handle the material matrix since all other parameters are set
        for pref, comp in mat.items():
            for name, indices in comp.items():
                for idx, ind in enumerate(indices):
                    ind = [i.replace('nx', '%d'%(props.nx+1)) for i in ind]
                    ind = [i.replace('ny', '%d'%(props.ny+1)) for i in ind]
                    ind = [i.replace('nz', '%d'%(props.nz+1)) for i in ind]
                    # Now shift the indices by one because someone chose +1 indexing :(
                    ind = [int(i)-1 for i in ind]
                    indices[idx] = MaterialComponent(i=ind[0:2],j=ind[2:4],k=ind[4:6])
                mat[pref][name] = indices
        props._set('mat', mat)
        # Reutrn the object
        values['mat'] = save
        #print('Created Mesh Specs in {} seconds.'.format(time.time() - start_time))
        if validate:
            start_time = time.time()
            print('Validating Mesh Specs...', end='\r')
            props.validate()
            print('Validated Mesh Specs in {} seconds.'.format(time.time() - start_time))
        return props

    @property
    def definitions(self):
        """Gets the ``mat_type`` definitions as integers to be matched with any
        given rocktab file via the lookup table."""
        mod = np.empty(self.shape, dtype=int)
        lootbl = self.lookup_table.set_index('material')
        for el_pref in self.mat.keys():
            for mat_type in self.mat[el_pref].keys():
                for mc in self.mat[el_pref][mat_type]:
                    mod[mc.i[0]:mc.i[1]+1,mc.j[0]:mc.j[1]+1,mc.k[0]:mc.k[1]+1] = lootbl.loc[mat_type]['id']
        return mod.flatten(order='f')

    @property
    def injector(self):
        mod = np.full(self.shape, False, dtype=bool)
        for mat_type in self.mat['wb1'].keys():
            for mc in self.mat['wb1'][mat_type]:
                mod[mc.i[0]:mc.i[1]+1,mc.j[0]:mc.j[1]+1,mc.k[0]:mc.k[1]+1] = True
        return mod.flatten(order='f')

    @property
    def materials(self):
        mats = []
        for el_pref in self.mat.keys():
            for mat_type in self.mat[el_pref].keys():
                mats.append(mat_type)
        return list(set(mats))

    @property
    def lookup_table(self):
        mats = self.materials
        df = pd.DataFrame(data=mats, columns=['material'])
        df['id'] = pd.factorize(df['material'])[0]
        return df

    def toTensorMesh(self):
        return discretize.TensorMesh(h=[self.dx, self.dy, self.dz])



class Param(properties.HasProperties):
    name = properties.String('The parameter name')
    value = properties.Float('The parameter value')


class EqnParams(properties.HasProperties):
    phase = properties.String('The phase')
    equation = properties.String('Equation to use')
    params = properties.List('The parameters', Param)


class RockType(properties.HasProperties):
    mat_type = properties.String('The rock type name corresponding to ``MaterialComponent.mat_type``.')

    Kd = properties.List('Dimensionless solid sorption coefficient of the component', Param)
    KdFactor = properties.List('Dimensionless solid sorption coefficient of the component', Param)

    tort = properties.List('The Tortuosity parameters per phase.', EqnParams)
    pc = properties.List('The pressure parameters per phase.', EqnParams)
    kr = properties.List('The relative permeability/saturation per phase.', EqnParams)

    K0 = properties.Float('The Kx value')
    K1 = properties.Float('The Kx value')
    K2 = properties.Float('The Kx value')

    porosity = properties.Float('The fractional porosity', min=0., max=1.)
    solid_density = properties.Float('The solid density value.')
    #tcond
    #Cp

    @classmethod
    def _create(cls, mat_type, values, validate=True):
        if not isinstance(values, dict):
            raise RuntimeError('Input values must be a dictionary')
        props = cls()
        props.mat_type = mat_type
        for k, v in values.items():
            if k in cls._props:
                # If the value is simple, set it!
                if not isinstance(cls._props[k], properties.List):
                    p = props._props.get(k)
                    props._set(k, p.from_json(v))
                elif k in ['Kd', 'KdFactor']:
                    # v is a dictionary of name value pairs of params
                    props._set(k, [Param(name=n, value=float(p)) for n,p in v.items()])
                elif k in ['tort', 'pc', 'kr']:
                    phases = []
                    for phase, eqns in v.items():
                        opt = eqns.pop('option')
                        params = [Param(name=n, value=float(p)) for n,p in eqns.items()]
                        phases.append(EqnParams(phase=phase, equation=opt, params=params))
                    props._set(k, phases)
                else:
                    #warnings.warn("({}:{}) property is not valid.".format(k, v))
                    pass
            else:
                print('WARN: {} not a property of this class.'.format(k))
        if validate: props.validate()
        return props


class USNT(MeshSpecifications):
    """The base object to instantiate."""
    rocktab = properties.Dictionary('Porous medium properties', key_prop=properties.String('The material type name'), value_prop=RockType)

    @property
    def attributes(self):
        atts = []
        for k,v in RockType._props.items():
            if isinstance(v, properties.Float):
                atts.append(k)
        return atts

    def model(self, attribute):
        """Gets a rocktab attribute as a NumPy array ready for discretize or PVGeo"""
        mod = np.empty(self.shape)
        mod[:] = np.nan
        for el_pref in self.mat.keys():
            for mat_type in self.mat[el_pref].keys():
                for mc in self.mat[el_pref][mat_type]:
                    mod[mc.i[0]:mc.i[1]+1,mc.j[0]:mc.j[1]+1,mc.k[0]:mc.k[1]+1] = self.rocktab[mat_type]._get(attribute)
        return mod.flatten(order='f')


    def allModels(self, dataframe=True):
        """Returns all attributes in a Pandas DataFrame"""
        df = pd.DataFrame()
        for key in self.attributes:
            df[key] = self.model(key)
        if dataframe:
            return df
        return df.to_dict()


    def saveLithLookupTable(self, filename):
        atts = ['K0', 'K1', 'K2', 'porosity', 'solid_density']
        lootbl = self.lookup_table.set_index('material')
        for at in atts:
            lootbl[at] = np.full(len(lootbl), np.nan)
            for k in lootbl.index:
                lootbl.loc[k,at] = self.rocktab[k]._get(at)
        lootbl = lootbl.reset_index()
        lootbl = lootbl.set_index('id')
        return lootbl.to_csv(filename, index_label='Index')
