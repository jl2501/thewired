###
#pytest tests
###

from thewired.namespace import CallableNode

def test_instantation():
    cn = CallableNode('a.b.c.d.e.f', lambda: print("invoked!"))
    cn()

def test_invocation():
    cn = CallableNode('a.b.c.d.e.f', lambda: 777)
    assert cn() == 777

