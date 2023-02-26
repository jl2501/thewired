import pytest

from thewired.namespace import SecondLifeNode, Namespace
from functools import partial

@pytest.fixture
def mock_attribute_map():
    def mock_provider_callable():
        print("mocked provider called!")
        return "just a value to return"

    return {
        "attribute_1" : "a value for attribute_1",
        "attribute_2" : "a.mock.provider.namespace.nsid",
        "attribute_3" : mock_provider_callable
    }


NS = Namespace()

def test_SecondLife_instantation(mock_attribute_map):
    MapNode = SecondLifeNode(nsid=".test.nsid.string", namespace=NS, secondlife=mock_attribute_map)
    assert str(MapNode.nsid) == '.test.nsid.string'
    assert MapNode._secondlife.keys() == mock_attribute_map.keys()

def test_SecondLife_map1(mock_attribute_map):
    MapNode = SecondLifeNode(nsid=".test.nsid.string", namespace=NS, secondlife=mock_attribute_map)
    assert MapNode.attribute_1 == mock_attribute_map.get('attribute_1')
    assert MapNode.attribute_3 == mock_attribute_map.get('attribute_3').__call__()

def test_lookup_ns():
    ns = Namespace()
    lookup_ns = Namespace()

    sl = {
            "foo" : "nsid://.x.y",
    }

    slnfactory = partial(SecondLifeNode, secondlife_ns=lookup_ns, secondlife=sl)
    ns.add('.a.b.c.d.e', slnfactory)
    lookup_ns.add('.x.y')
    assert str(ns.root.a.b.c.d.e.foo.nsid) == ".x.y"

def test_lookup_ns_callable():

    class SomeCallableClass:
        def __call__(self):
            magic_string = "Tusks' Dissolve is a great album"
            print(magic_string)
            return magic_string

    ns = Namespace()
    lookup_ns = Namespace()

    sl = {
            "foo" : "nsid://.x.y",
    }

    slnfactory = partial(SecondLifeNode, secondlife_ns=lookup_ns, secondlife=sl)
    ns.add('.a.b.c.d.e', slnfactory)

    y_factory = partial(CallableDelegateNode, delegate=SomeCallableClass())
    lookup_ns.add('.x.y', y_factory)
    assert str(ns.root.a.b.c.d.e.foo.nsid) == ".x.y"
    assert ns.root.a.b.c.d.e.foo() == "Tusks' Dissolve is a great album"
