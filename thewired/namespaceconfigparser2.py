import sys
import typing
from typing import Dict, Union
from collections.abc import Mapping
from importlib import import_module
from functools import partial

from .namespace import Namespace
from .namespace import NamespaceNodeBase
from .namespace import nsid

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

class NamespaceConfigParser2(object):
    def __init__(self, prefix: str = None, node_factory=NamespaceNodeBase):
        self.prefix = prefix if prefix else ''
        self.default_node_factory=node_factory

        #- special YAML keys that can be used to let this parser know
        #- what type should be used for the node factory and what params to pass it
        self.meta_keys = ['__type__', '__init__']


            

    def _get_node_factory(self, key: str, dictConfig: dict) -> partial:
        """
        Description:
            return a context manager that sets the node factory based on any meta keys that
            may exist under this key
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._parse_meta_key'))

        #- check the subkeys of this key to see if they have any meta info about how to create the node
        if any(x in self.meta_keys for x in dictConfig[key].keys()):
            #- we need to change the node factory from the default
            try:
                nf_module_name = '.'.join(dictConfig[key]["__type__"].split('.')[0:-1])
                nf_symbol_name = dictConfig[key]["__type__"].split('.')[-1]
                nf_module = import_module(nf_module_name)

            except KeyError:
                #- no "__type__" key
                #- leave node_factory set to the default
                log.debug("key error when trying to access '__type__'")
                nf_module = None

            except ValueError:
                #- we have a name, but it might not have a dot at all,
                #- which would then try to import the empty string and 
                #- fail with a ValueError

                #- try to use the current module as the module containing the node factory
                log.debug("value error importing namespace factory module: \"{nf_module_name}\"")
                nf_module = sys.modules[__name__]

            finally:
                if nf_module:
                    node_factory = getattr(nf_module, nf_symbol_name)
                else:
                    node_factory = self.default_node_factory

            #- set the parameters for the node factory
            try:
                _init_params = dictConfig[key]["__init__"]
            except KeyError:
                #- no __init__ key
                _init_params = dict()


            log.debug(f"returning custom {node_factory=} {_init_params=}")
            return partial(node_factory, **_init_params)

        else:
            log.debug("returning default node factory")
            return self.default_node_factory
            

                

    def parse(self, dictConfig: dict, prefix:str='', namespace:Union[None, Namespace]=None, namespace_factory:type=Namespace) -> Union[Namespace, None]:
        """
        Description:
            parse a configDict into a Namespace object
        Input:
            configDict - the configuration file parsed into a dictionary
            prefix - the rolling prefix for this parse, used to collect when recursively
                called
            namespace - what namespace to add the new nodes parsed to 
                        (if not specified, will use namespace_factory to create a new one)
            namespace_factory - creates a new namespace object when an existing one is not passed in via `namespace`
                                Only tested with thewired.namespace.Namespace class ATM
        Output:
            a namespace object representing the nodes specifed in the dictConfig object
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}.parse'))

        log.debug(f"enter: {prefix=} {namespace=} {namespace_factory=} {dictConfig=}")
        ns = namespace if namespace else namespace_factory()

        if not dictConfig or len(dictConfig.keys()) <= 0:
            return None

        #- create a namespace of objects described by dictConfig Mapping
        for key in dictConfig.keys():
            log.debug(f"starting {key=}")
            if key not in self.meta_keys:
                node_factory = self._get_node_factory(key, dictConfig)

                #- every key gets turned into a node in the namespace
                new_node_nsid = nsid.make_child_nsid(prefix, key)
                log.debug(f"{new_node_nsid=}")
                log.debug(f"{node_factory=}")

                new_node = ns.add_exactly_one(new_node_nsid, node_factory)

                if isinstance(dictConfig[key], Mapping):
                   log.debug(f"recursing on {key=} {dictConfig[key]}")
                   self.parse(dictConfig=dictConfig[key], prefix=new_node_nsid, namespace=ns)
                else:
                    log.debug(f"setting {new_node.nsid}.{key} to {dictConfig[key]}")
                    setattr(new_node, key, dictConfig[key])
        return ns
