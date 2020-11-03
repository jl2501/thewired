import typing
from typing import Dict
from collections.abc import Mapping

from .namespace import Namespace
from .namespace import nsid

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

class NamespaceConfigParser2(object):
    def __init__(self, prefix: str = None):
        self.prefix = prefix if prefix else ''

    def parse(self, dictConfig: dict, prefix: str = '', namespace=None, namespace_factory=Namespace):
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
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}.parse')

        ns = namespace if namespace else namespace_factory()

        if not dictConfig or len(dictConfig.keys()) <= 0:
            return

        for key in dictConfig.keys():
            new_node_nsid = nsid.make_child_nsid(prefix, key)
            log.debug(f"{new_node_nsid=}")
            new_node = ns.add_exactly_one(new_node_nsid)

            if isinstance(dictConfig[key], Mapping):
               self.parse(dictConfig=dictConfig[key], prefix=new_node_nsid, namespace=ns)

        return ns
