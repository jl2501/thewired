from thewired import DelegateNode, CallableDelegateNode, Namespace, NamespaceNodeBase
from thewired.testobjects import CallableSomething

def test_delegate_1():

    class Something(object):
        def __init__(self, a):
            self.a = a
        def get_a_x2(self):
            return [self.a, self.a]


    ns = Namespace()
    ns.add_exactly_one('.testing', DelegateNode, Something(15))

    node = ns.get('.testing')

    assert(isinstance(node, NamespaceNodeBase))
    assert(isinstance(node, DelegateNode))
    assert node.a == 15
    assert(node.get_a_x2()[0] == 15)
    assert(node.get_a_x2()[1] == 15)

def test_callabledelegate():

    ns = Namespace()
    ns.add_exactly_one('.testing', CallableDelegateNode, CallableSomething(91))

    node = ns.get('.testing')
    assert(callable(node))
    assert(node("mad crazy string, bro") == "Called with args=('mad crazy string, bro',) kwargs={}")
