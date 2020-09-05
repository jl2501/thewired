"""
the point of separating out the namespace node types is to keep them small and modular and thus (hopefully) easier to reason about the expected
behavior of.

But, in the end, we want to be able to combine the available features from each type as needed to support the desired dynamics.

experimenting with a Mixin pattern to be able to have pythons magic methods included dynamically.
this allows a namespacenode object to be created dynamically that will be instantated with dunder methods that allow standard
python internals to operate as normal. (those methods can't be added dynamically)
"""

from thewired.namespace import CallableMixin, SecondLifeNode
import pytest

class CallableSecondLifeNode(CallableMixin, SecondLifeNode):
    def __init__(self, nsid, secondlife=None):
        super().__init__(nsid, secondlife=secondlife)

    def _call(self, *args, **kwargs):
        print("invoked!")
        return 777

def test_mixin():
    csln = CallableSecondLifeNode(nsid='.a.b.c', secondlife=dict(a="AAA", b=lambda: 888))
    assert callable(csln)
    assert csln() == 777
    assert csln.a == 'AAA'
    assert csln.b == 888
