"""
Purpose:
    Base Functionality for a NamespaceNode object.

Notes:
    *in progress being factored out from namespacenode module*
"""

from logging import getLogger
from types import SimpleNamespace

from thewired.namespace.nsid import Nsid
from thewired.loginfo import make_log_adapter


logger = getLogger(__name__)


class NamespaceNodeBase(SimpleNamespace):
    """
    Description:
        Base Functionality for a NamespaceNode object.  Attributes are expected to be
        dynamically added and removed from these objects based on configuration and user
        workflow.

    See Also:
        * NamespaceConfigParser
    """
    def __init__(self, nsid, *args, **kwargs):
        """
        Input:
            nsid: namespace id of this node
        """
        super().__init__(*args, **kwargs)
        self.nsid = Nsid(nsid)

    def __repr__(self):
        return f"{self.__class__.__name__}(nsid=\"{self.nsid}\")"
