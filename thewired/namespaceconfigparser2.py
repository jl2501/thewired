import typing
from typing import Dict
from collections.abc import Mapping

from .namespace import Namespace
from .namespace import nsid

class NamespaceConfigParser2(object):
    def __init__(self, prefix: str = None):
        self.prefix = prefix if prefix else ''

    def parse(self, dictConfig: dict, prefix: str = None, namespace=None, namespace_factory=Namespace):
        """
        Description:
            parse a configDict into a Namespace object
        Input:
            configDict - the configuration file parsed into a dictionary
            prefix - the rolling prefix for this parse, used to collect when recursively
                called
            namespace_factory - what creates the namespace object. Only tested with
                thewired.namespace.Namespace class ATM
        """
        ns = namespace if namespace else namespace_factory()
        rolling_prefix = prefix if prefix else ''

        if not dictConfig or len(dictConfig.keys()) <= 0:
            return

        for key in dictConfig.keys():
            new_node_nsid = nsid.make_child_nsid(rolling_prefix, key)
            new_node = ns.add_exactly_one(new_node_nsid)

            #- check for need to recurse
            if isinstance(dictConfig[key], Mapping):
                self.parse(dictConfig=dictConfig[key], prefix=new_node_nsid, namespace=ns)

        return ns
