from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

from .namespacenode import NamespaceNode

class AliasNode(NamespaceNode):
    """
    Description:
        Node to be used in a namespace that is used as an alias for another node.
    """
    def __init__(self, nsid, alias_nsid, ns_items=None):
        log = LoggerAdapter(logger, {'name_ext': 'AliasNode.__init__'})
        log.debug("Initializing Alias Node: {} --> {}".format(nsid, alias_nsid))

        super().__init__(namespace_id=nsid, provider_map=None, ghost=None,\
            ns_items=ns_items)

        self._alias_nsid = alias_nsid
        self._ns_items = ns_items


    def dereference(self):
        return self.global_ns._lookup(self._alias_nsid)
    

    @property
    def provider_map(self):
        return None

    @provider_map.setter
    def provider_map(self, mapping):
        raise AttributeError("{} does not support having a provider map".format(\
            self.__class__.__name__))

    @property
    def ghost(self):
        return None

    @ghost.setter
    def ghost(self, value):
        raise AttributeError("{} does not support having a ghost".format(\
            self.__class__.__name__))


    def __repr__(self):
        repr = '{}( namespace_id={}, alias_nsid={})'.format(\
            self.__class__.__name__, self._namespace_id, self._alias_nsid)
        return repr


    def __str__(self):
        return '{}({})-->{}'.format(self.__class__.__name__, self._namespace_id,\
            self._alias_nsid)
