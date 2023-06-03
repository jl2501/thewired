"""
Purpose:
    Base Functionality for a NamespaceNode object.

Notes:
    *in progress being factored out from namespacenode module*
"""

from logging import getLogger
from types import SimpleNamespace
from typing import Union

from thewired.namespace.nsid import Nsid

from thewired.loginfo import make_log_adapter

###
# type aliases
###
#NSID = Union[str, Nsid]


logger = getLogger(__name__)


class NamespaceNodeBase(SimpleNamespace):
    """
    Description:
        Base Functionality for a NamespaceNode object.  Attributes are expected to be
        dynamically added and removed from these objects based on configuration and user
        workflow.

    Input:
        namespace: the namespace object that this node will belong to. (Used for the Node to call Namespace API operations)
        nsid: the NameSpace ID of this node

    See Also:
        * NamespaceConfigParser
    """
    #def __init__(self, namespace:Namespace, nsid:NSID, *args, **kwargs): #circular imports needed for type annotations
    def __init__(self, nsid, namespace,  *args, **kwargs):
        """
        Input:
            nsid: namespace id of this node
        """
        log = make_log_adapter(logger, self.__class__, "__init__")
        log.debug(f"calling super().__init__: {nsid=} | {namespace=} | {args=} | {kwargs=}")
        super().__init__(*args, **kwargs)
        self.nsid = Nsid(nsid)
        self._ns = namespace
        log.debug("exiting")

    def __repr__(self):
        return f"{self.__class__.__name__}(nsid=\"{self.nsid}\")"
