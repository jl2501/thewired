from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import copy
import collections
from thewired.util import is_nsid_ref

class ParametizedCall(object):
    """
    Description: 
        Provider Primitive type. Builds up a string to be used as an addendum
        for calling a named method with a set of parameters that exists in the params
        namespace
    """
    _param_dict_mark_key = '__params__'



    @classmethod
    def is_param_call_map(cls, map):
        """
        Description:
            check if a given mapping is formatted in a way that makes it identifiable as a
            ParametizedCall mapping
        """
        return len(map.keys()) == 1 and cls._param_dict_mark_key in map.keys()



    @classmethod
    def get_params(cls, map, *args, **kwargs):
        """
        Description:
            get the raw parameters from a formatted params map
        Input:
            map:
                the params map
            *args: ignored
            **kwargs: overlay parameters
        Ouput: a 2-tuple of (method_name, params dict)
        """

        log = LoggerAdapter(logger, {'name_ext' : 'ParametizedCall.get_params'})
        log.debug("Entered")
        log.debug("kwargs: {}".format(str(kwargs)))

        params_marker = cls._param_dict_mark_key

        params = copy.deepcopy(map[params_marker])
        log.debug("raw params: {}".format(params))
        method_name = params['defaults'].pop('method_name')
        param_chain = collections.ChainMap(kwargs, params['defaults'])
        param_set_name = kwargs.pop('_params', None)
        if param_set_name:
            param_chain.maps.insert(1, params[param_set_name])

        log.debug("Exiting")
        return (method_name, param_chain)


    def __init__(self, nsroot, method_name, param_map):
        """
        Input:
            nsroot: namespace root to resolve symbolic inter-NS references
            param_map: the dict-like object to use as the parameter map
        """
        self.nsroot = nsroot
        self.method_name = method_name
        self.params = param_map


    def make_addendum(self, nsid=None, implementor=None, key=None, need_key=True):
        """
        Description:
            create the addendum dynamically from the parameter map
            Inter-namespace symbolic references are all deferenced

        Input:
            nsid: ignored;
            implementor: ignored;
            key: sub key to use in the parameterized dict
                generally per-implementor object specific

            need_key: boolean to control raising KeyError if provided key does not exist
                in the addendum param map

        Output:
            a string suitable for use in an Addendum provider
        """

        log = LoggerAdapter(logger, {'name_ext' : 'ParametizedCall.make_addendum'})
        unpack_str = ''
        for k,v in self.params.items():

            #- dereference symbolic ref values
            if is_nsid_ref(v):
                log.debug("Dereferencing symbolic ref: {}".format(v))
                v = self.nsroot._lookup_symbolic_ref(v, follow_symrefs=True)
                log.debug("deref: {}".format(v))

            #- dereference sequence items
            if isinstance(v, collections.Sequence) and not isinstance(v, str):
                v = self.stringify_sequence(v, key=key)
                unpack_str += '{} = {}, '.format(k,v)
                continue

            if isinstance(v, collections.Mapping) and key is not None:
                try:
                    v = v[key]
                    #unpack_str += '{} = {}, '.format(k,v[key])
                except KeyError as err:
                    #- subkey not present
                    msg = "Subkey '{}' not present; not using".format(key)
                    log.debug(msg)
                    if need_key:
                        raise

            if isinstance(v, str):
                unpack_str += '{} = \'{}\', '.format(k,v)
            else:
                #- immediate non-string value
                unpack_str += '{} = {}, '.format(k,v)


        #- chop off last ", "
        unpack_str = unpack_str[0:-2]

        addendum = '.' + self.method_name + '(' + unpack_str + ')'
        log.debug("returning addendum: {}".format(addendum))
        return addendum



    def stringify_sequence(self, seq, key=None):
        """
        Description:
            make a sequence into a string version. we can't use the default python
            formatter here b/c that would enclose the whole thing in quotes, but we want
            to pass back a string that can be used as an eval-able string, thus the list
            braces themselves should be literals, but every item inside should be a string
        """
        seq_str = '['
        dref_seq = self.deref_sequence_items(seq)

        for item in dref_seq:
            if isinstance(item, collections.Mapping) and key is not None:
                try:
                    seq_str += "'{}'".format(item[key])
                except KeyError as err:
                    msg = "Subkey '{}' not present!".format(key)
                    log.error(msg)
                    raise ValueError(msg) from err
            else:
                seq_str += "'{}'".format(item)
        seq_str += ']'

        return seq_str
        

    def deref_sequence_items(self, seq):
        """
        Description:
            dereference everything in a sequence
        """
        dref_seq = list()
        for item in seq:
            if is_nsid_ref(item):
                item = self.nsroot._lookup_symbolic_ref(item, follow_symrefs=True)
            dref_seq.append(item)

        return dref_seq


    def __call__(self, nsid=None, implementor=None, key=None):
        return self.make_addendum(nsid=nsid, implementor=implementor, key=key)


    def __str__(self):
        return 'ParametizedCall: {}'.format(self.make_addendum())
