"""
python dunder / magic methods can't be added dynamically
but I don't want to include things that aren't used as it clutters
the logical namespace navigation xp.

a CallableNode is a namespace node that defines __call__ and thus can be invoked / called
"""

from .base import NamespaceNodeBase

class CallableNode(NamespaceNodeBase):
    """
    A Namespace Node with a __call__ method registered in the native slots
    """
    def __init__(self, nsid, __call__=None):
        """
        Description:
            create a callable object that calls the passed in callable, __call__, when called. %-D
        Input:
            nsid: namespace id
            __call__: the callable to invoke in response to us being invoked
        """
        super().__init__(nsid)
        self.target_callable = __call__
        
    def __call__(self, *args, **kwargs):
        return self.target_callable(*args, **kwargs)
