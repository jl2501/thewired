from .base import NamespaceNodeBase
from logging import getLogger

log = getLogger(__name__)

class DelegateNode(NamespaceNodeBase):
    """
    delegates all missed attribute lookups to <delegate> object via __getattr__
    """
    def __init__(self, nsid, namespace, delegate):
        super().__init__(nsid, namespace)
        self._delegate = delegate

    def __getattr__(self, attr):
        log.error(f"__getattr__: {attr=}")
        return getattr(self._delegate, attr)