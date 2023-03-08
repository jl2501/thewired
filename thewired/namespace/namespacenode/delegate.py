from .base import NamespaceNodeBase
from logging import getLogger, LoggerAdapter
from ..nsid import Nsid

logger = getLogger(__name__)

class DelegateNode(NamespaceNodeBase):
    """
    delegates all missed attribute lookups to <delegate> object via __getattr__
    """
    def __init__(self, delegate, *, nsid, namespace):
        super().__init__(nsid=nsid, namespace=namespace)
        self.nsid = Nsid(nsid)
        self._delegate = delegate

    def __getattr__(self, attr):
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.__getattr__"))
        #log.debug(f"__getattr__: {attr=}")
        return getattr(self._delegate, attr)

    def __str__(self):
        return str(self._delegate)

    def __repr__(self):
        return repr(self._delegate)

    def __dir__(self):
        return dir(self._delegate)

class CallableDelegateNode(DelegateNode):
    """
    same as delegate node, but dunders must be instantiated into slots (can't be added after construction)
    so, we add the __call__ dunder as part of the definition to make it callable

    requires that the delegate itself is callable
    """
    def __init__(self, delegate, *, nsid, namespace):
        super().__init__(delegate, nsid=nsid, namespace=namespace)

    def __call__(self, *args, **kwargs):
        return self._delegate(*args, **kwargs)
