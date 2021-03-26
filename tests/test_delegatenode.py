from thewired import DelegateNode, Namespace, NamespaceNodeBase

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
    assert(node.get_a_x2()[0] == 15)
    assert(node.get_a_x2()[1] == 15)
