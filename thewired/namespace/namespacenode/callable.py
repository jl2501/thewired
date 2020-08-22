"""
python dunder / magic methods can't be added dynamically
but I don't want to include things that aren't used as it clutters
the logical namespace navigation xp.

a CallableNodeMixin is a namespace node Mixin that defines __call__ and thus can be invoked / called
"""

class CallableNodeMixin(object):
    """
    A Namespace Node with a __call__ method registered in the native slots
    """
    def __call__(self, *args, **kwargs):
        return self.invoke(*args, **kwargs)
