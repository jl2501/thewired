from thewired import Namespace, HandleNode, DelegateNode, NamespaceNodeBase


def test_get():
    ns = Namespace()
    ns.add('.a.b.c.d.e.f.g')
    handle = ns.get_handle('.a.b.c')
    node = handle.get('.d.e.f')
    assert isinstance(node, HandleNode)
    assert str(node.nsid) == '.d.e.f'
