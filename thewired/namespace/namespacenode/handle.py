"""
Purpose:
    Namespace Handles return these nodes
    This is so that a node that is returned from a handle can be referenced with the same handle
    If we use the canonical NSID in the node returned, the Handle can never refer to that node
    as the node would have a canonical NSID and the Handle will always add its prefix

    So, instead, we have NamespaceHandles return HandleNodes
"""

from logging import getLogger
from .base import NamespaceNodeBase
from .delegate import DelegateNode

from thewired.namespace.nsid import strip_common_prefix, Nsid

from thewired.loginfo import make_log_adapter



logger = getLogger(__name__)


class HandleNode(DelegateNode):
    """
    delegates all missed attribute lookups to <delegate> object via __getattr__
    overrides NSID as a property to strip the Handle prefix in the nsid
    """
    def __init__(self, real_node, ns_handle):
        self._delegate = real_node
        self._ns = ns_handle

    def __getattr__(self, attr):
        return getattr(self._delegate, attr)

    def __str__(self):
        return str(self._delegate)

    def __repr__(self):
        return "HandleNode(" + repr(self._delegate) + ")"

    def __dir__(self):
        return dir(self._delegate)

    @property
    def nsid(self):
        hnsid = strip_common_prefix(self._delegate.nsid, self._ns.prefix)[0]
        return Nsid(hnsid) if hnsid and hnsid[0] == '.' else Nsid('.' + hnsid)

    @nsid.setter
    def nsid(self, new_nsid):
        self._delegate.nsid = new_nsid



class CallableHandleNode(HandleNode):
    """
    same as HandleNode, but dunders must be instantiated into slots (can't be added after construction)
    so, we add the __call__ dunder as part of the definition to make it callable

    requires that the delegate itself is callable
    """
    def __init__(self, real_node, ns_handle):
        super().__init__(real_node, ns_handle)

    def __call__(self, *args, **kwargs):
        return self._delegate(*args, **kwargs)

    def __repr__(self):
        return "CallableHandleNode(" + repr(self._delegate) + ")"
