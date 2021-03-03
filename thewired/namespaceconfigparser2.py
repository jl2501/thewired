import sys
import typing
from typing import Dict, Union, Callable, List
from collections.abc import Mapping
from importlib import import_module
from functools import partial

from .namespace import Namespace
from .namespace import NamespaceNodeBase
from .namespace import nsid

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

class NamespaceConfigParser2(object):
    def __init__(self, 
            node_factory:type=NamespaceNodeBase,
            callback_target_keys:Union[List[str],None]=None,
            input_mutator_callback:Union[Callable, None]=None):

        self.default_node_factory=node_factory

        #- special YAML keys that can be used to let this parser know
        #- what type should be used for the node factory and what params to pass it
        self.meta_keys = set(['__class__', '__init__', '__type__'])
        self._input_mutator_targets = callback_target_keys if callback_target_keys else list()
        self._input_mutator = input_mutator_callback if input_mutator_callback else lambda x,y: (x,y)



    def parse(self, dictConfig: dict, prefix:str='', namespace:Namespace=None, namespace_factory:type=Namespace) -> Union[Namespace, None]:
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


        try:
            dictConfig.keys()
        except (AttributeError, TypeError):
            return None


        #- create namespace as dictConfig describes
        for key in dictConfig.copy().keys():

            if key in self._input_mutator_targets:
                dictConfig, key = self._input_mutator(dictConfig, key)

            #- NB: meta keys can not be top level keys with this current pattern
            if key not in self.meta_keys:
                log.debug(f"parsing {key=}")
                node_factory = self._create_factory(dictConfig[key], self.default_node_factory)

                if node_factory:
                    new_node_nsid = nsid.make_child_nsid(prefix, key)
                    log.debug(f"{new_node_nsid=}")
                    new_node = ns.add_exactly_one(new_node_nsid, node_factory)

                    if isinstance(dictConfig[key], Mapping):
                       self.parse(dictConfig=dictConfig[key], prefix=new_node_nsid, namespace=ns)
                    else:
                        log.debug(f"setting {new_node.nsid}.{key} to {dictConfig[key]}")
                        setattr(new_node, key, dictConfig[key])

        return ns



    def _create_factory(self, dictConfig: dict, default_factory: Union[None, callable]=None) -> Union[partial, None]:
        """
        Description:
            Create and return the factory function + params as a partial based on any meta keys that
            may exist under this key

            There's some extra logic for nodes that define an object that must first be instantiated and passed in
            as a parameter to the nodes __init__ method

        Input:
            dictConfig: mapping to parse

        Output:
            a partial made from the parsed factory function with the parsed factory function params
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._create_node_factory'))

        try:
            keys = dictConfig.keys()
        except AttributeError:
            #- the dictConfig isn't a dict anymore
            log.debug("No factory: not a dict")
            return None

        node_factory_function = self._parse_meta_factory_function(dictConfig, self.default_node_factory)
        init_params = self._parse_meta_factory_function_params(dictConfig)

        log.debug(f"returning custom {node_factory_function=} {init_params=}")
        return partial(node_factory_function, **init_params)




    def _parse_meta_factory_function(self, dictConfig: dict, default_factory_function: Union[None, callable]=None) -> callable:
        """
        Description:
            create the node factory function from the config, but this part does not deal with
            parsing the parameters specified for the factory function. Only the callable w/out any params

        Input:
          dictConfig: the config we are parsing

        Output:
            callable that should first be combined with the parameters before being called

        Notes:
            called by:
                * _create_node_factory
                * _create_node_factory_param_object
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._create_node_factory_bare_function'))

        factory_func = self._parse_meta_factory_function_dynamic(dictConfig)
        if not factory_func:
            factory_func = self._parse_meta_factory_function_static(dictConfig, default_factory_function)

        #TODO: when static parser retuns None like dynamic
        # if not factory_func:
        # factory_func = default_factory_func

        return factory_func




    def _parse_meta_factory_function_dynamic(self, dictConfig: dict) -> Union[callable, None]:
        #- dyty == "dynamic type"
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._parse_meta_factory_function_dynamic'))
        try:
            dyty_name = dictConfig["__type__"]["name"]
            dyty_bases = dictConfig["__type__"]["bases"]
            dyty_dict = dictConfig["__type__"]["dict"]

            dyty_bases = self._parse_meta_factory_function_dynamic_bases(dyty_bases)
            
            log.debug(f"{dyty_name=}")
            log.debug(f"{dyty_bases=}")
            log.debug(f"{dyty_dict=}")
            dyty = type(dyty_name, dyty_bases, dyty_dict)
            return dyty

        except KeyError:
           return None




    def _parse_meta_factory_function_dynamic_bases(self, base_names: list) -> tuple:
        """
        Description:
            takes the list of strings of class names and turns it into a tuple of type objects
            required before passing the bases to `type` builtin
        Input:
            bases: a list of strings of base class names
        Output:
            tuple of types created from the names

        TODO: this was straight copied from _parse_meta_factory_function_static. Refactor into a shared method call
            that can capture the similar logic for importing the module and getting the symbol as an object
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._parse_meta_factory_function_dynamic_bases'))

        bases = list()  # will be returned value

        for basename in base_names:
            module = None    #- the python module that has the class 
            try:
                module_name = '.'.join(basename.split('.')[0:-1])
                symbol_name = basename.split('.')[-1]
                module = import_module(module_name)


            except ValueError:
                #- the import_module call failed
                #- we have a name, but it might not have a dot at all,
                #- which would then try to import the empty string and 
                #- fail with a ValueError

                #- try to use thewired as the base import lib name
                log.debug("value error importing: \"{module_name}\". Defaulting to 'thewired'.")
                module = import_module("thewired")

            finally:
                if module:
                    try:
                        cls = getattr(module, symbol_name)

                    except AttributeError as err:
                        log.debug(f"specified class ({symbol_name}) does not exist in specified module ({module_name})!")
                        raise ValueError(f"\"{symbol_name} does not exist in {module_name}!") from err

                    else:
                        bases.append(cls)

        return tuple(bases)



    def _parse_meta_factory_function_static(self, dictConfig: dict, default_factory_function: callable) -> callable:
        """
        Description:
            parses a staticly typed node object config ("__class__", "__init__" keys)

        Input:
            dictConfig: config dict (deserialized yaml) we are parsing
            default_factory_function: what to return if we don't find a static type definition

        Output:
            always returns a callable. Either what was parsed or the default if it failed to parse
            TODO: unify semanitcs btw this and dynamci parser. return None instead of passing default
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._parse_meta_factory_function_static'))
        #- pick back up here in case of KeyError
        nf_module = None    #- "node factory module" - the python module that has the node factory function defined
        try:
            nf_module_name = '.'.join(dictConfig["__class__"].split('.')[0:-1])
            nf_symbol_name = dictConfig["__class__"].split('.')[-1]
            nf_module = import_module(nf_module_name)

        except KeyError:
            #- no "__class__" key
            #- leave node_factory set to the default
            log.debug("key error when trying to access '__class__'")
            return default_factory_function

        except ValueError:
            #- the import_module call failed
            #- we have a name, but it might not have a dot at all,
            #- which would then try to import the empty string and 
            #- fail with a ValueError

            #- try to use the current module as the module containing the node factory
            log.debug("value error importing namespace factory module: \"{nf_module_name}\"")
            nf_module = sys.modules[__name__]

        finally:
            if nf_module:
                try:
                    node_factory = getattr(nf_module, nf_symbol_name)
                except AttributeError as err:
                    log.debug("specified factory function does not exist in specified module!")
                    raise ValueError("parsed factory function does not exist in specified module!") from err

                if not callable(node_factory):
                    log.debug(f"specified node factory is not callable! {dictConfig=}")
                    raise ValueError(f"parsed node factory {dictConfig['__class__']} is not callable!")

            else:
                return default_factory_function

        return node_factory



    def _parse_meta_factory_function_params(self, dictConfig: dict) -> dict:
        """
        Description:
            Figure out the parameters that are to be passed into the node factory bare function to complete the node factory function
            by parsing the '__init__' subkey if it exists

            If the '__init__' block has parameters that themselves have a '__class__' key, then this will descend and instantiate those
            objects

        Input:
            dictConfig: the config we are parsing

        Output:
            A dict with all the parameters needed for the node factory to be called

        Notes:
            Only called by _create_node_factory as a helper method (at same dict key level)

            Only works with dict /kwarg params ATM
            TODO: make this work with serialized positional args as well
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._create_node_factory_bare_params'))
        init_params = dict()

        if not dictConfig:
            return dict()
        try:
            init_params_config = dictConfig["__init__"]
        except KeyError:
            #- no __init__ key, leave it as an empty dict
            return dict()

        else:
            #- there is an "__init__" subkey for this node factory parameter
            try:
                init_param_names = init_params_config.keys()
            except AttributeError:
                log.debug(f"dictConfig[__init__] is not a mapping: {dictConfig['__init__']}")
                pass

            else:
                #- check the init params config for more nested meta keys
                #- that case is when there are objects that first must be instantiated in order
                #- to be passed as parameters into the node factory bare function to complete
                #- the node factory function partial
                for init_param_name in init_param_names:
                    try:
                        init_params_config[init_param_name].keys()
                    except AttributeError:
                        init_params[init_param_name] = dictConfig["__init__"][init_param_name]

                    else:
                        if set(init_params_config[init_param_name].keys()).intersection(set(self.meta_keys)):
                            log.debug(f"found recursive parameter definition: {init_param_name=}")
                            log.debug(f"recursive parameter config: {dictConfig['__init__'][init_param_name]=}")

                            #init_params[init_param_name] = self._create_node_factory_param_object(dictConfig["__init__"][init_param_name])
                            init_params[init_param_name] = self._create_factory(dictConfig["__init__"][init_param_name], object)()

                            log.debug(f"created new object: {init_params[init_param_name]=}")
        return init_params



    def _create_node_factory_param_object(self, dictConfig:dict) -> Union[object, None]:
        """
        Description:
            instantiates objects defined inside of node factory init function parameters
            these objects are needed in order to pass in as params to the node factory function
        Input:
            dictConfig: the config we are parsing
        Output:
            a parameter object instantiated as specified in the config via the meta keys
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}._create_node_factory_param_objects'))
        log.debug(f"create_node_factory_param_object: {dictConfig=}")

        if not dictConfig:
            return None
        try:
            keys = dictConfig.keys()
        except AttributeError:
            #- no .keys(), dictConfig is no longer a mapping type
            return None

        #- parse out the function from __class__
        factory_function = self._parse_meta_factory_function(dictConfig)

        #- parse the parameters and instantiate the objects
        init_params = dict()
        try:
            init_param_names = dictConfig['__init__'].keys()
            for init_param_name in init_param_names:
                try:
                    init_param_keys = dictConfig['__init__'][init_param_name].keys()
                    #- this init param itself requires an init param
                    #- TODO
                    pass

                except AttributeError:
                    #- this init param is not a mapping type
                    init_params = dictConfig['__init__'][init_param_name]

        except KeyError:
            #- no '__init__' key
            return dict()

