"""
the point of separating out the namespace node types is to keep them small and modular and thus (hopefully) easier to reason about the expected
behavior of.

But, in the end, we want to be able to combine the available features from each type as needed to support the desired dynamics.

For now, I'm doing that by mapping methods orthogonally (no overlap) into multiple subclasses of NamespaceNodeBase and then
using multiple inheritance from this level of classes to specify which features get added to the namespace node newly being created.

it may be better to actually make that in to an interface rather than (ab)using inheritance this way, but that's code for another day
"""

from thewired.namespace import CallableNodeMixin, SecondLifeNode

def test_mixin():
    class CallableSecondLifeNode(CallableNodeMixin, SecondLifeNode):
        def __init__(self, nsid, secondlife=None):
            super().__init__(nsid, secondlife=secondlife)

        def invoke(self, *args, **kwargs):
            print("invoked!")
            return 777

    csln = CallableSecondLifeNode(nsid='.a.b.c', secondlife=dict(a="AAA", b=lambda: 888))
    assert csln() == 777
    assert csln.a == 'AAA'
    assert csln.b == 888
