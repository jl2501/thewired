import thewired
import unittest

from functools import partial

from thewired.namespace import Namespace
from thewired.namespace import NamespaceNode
from thewired.namespace import NamespaceNodeBase
from thewired.namespace.nsid import get_nsid_ancestry
from thewired import NamespaceConfigParser
from thewired import NamespaceConfigParser2

class NamespaceNodeSubclass(NamespaceNode):
    pass

class NamespaceNodeBaseSubclass(NamespaceNodeBase):
    pass


class test_NamespaceConfigParser1(unittest.TestCase):

    def test_NamespaceConfigParser_instantation(self):
        nscp = NamespaceConfigParser()
        self.assertIsInstance(nscp.new_node(), NamespaceNode)

    def test_NamespaceConfigParser_instantiation_with_node_factory_override_1(self):
        nscp = NamespaceConfigParser(node_factory=NamespaceNodeSubclass)
        self.assertIsInstance(nscp.new_node(nsid='.test'), NamespaceNodeSubclass)

    def test_NamespaceConfigParser_instantiation_with_node_factory_override_2(self):
        ns = Namespace(default_node_factory=NamespaceNodeBaseSubclass)
        nscp = NamespaceConfigParser(node_factory=ns.add)
        new_node = nscp.new_node(nsid='.test')[0]
        self.assertIsInstance(new_node, NamespaceNodeBaseSubclass)

    def test_NamespaceConfigParser_instantiation_with_node_factory_override_3(self):
        ns = Namespace(default_node_factory=NamespaceNodeBaseSubclass)
        nfactory = partial(ns.add_exactly_one, node_factory=NamespaceNodeBaseSubclass)
        nscp = NamespaceConfigParser(node_factory=nfactory)
        new_node = nscp.new_node('.test')
        self.assertIsInstance(new_node, NamespaceNodeBaseSubclass)



def test_NamespaceConfigParser_instantation():
    nscp = NamespaceConfigParser2()

def test_parse_no_meta():
    test_dict = {
        "all" : {
            "work" : {
                "no" : {
                  "play" : {
                      "dull_boy" : {}
                  }
                }
            }
        },
        "hackers" : {
            "on" : {
                "planet" : {
                    "earth" : {}
                }
            }
        }
    }

    nscp = NamespaceConfigParser2()
    ns = nscp.parse(dictConfig=test_dict)

    print(ns.walk())
    for nsid in get_nsid_ancestry('.all.work.no.play.dull_boy'):
        assert isinstance(ns.get(nsid), NamespaceNodeBase)


    for nsid in get_nsid_ancestry('.hackers.on.planet.earth'):
        assert isinstance(ns.get(nsid), NamespaceNodeBase)


def test_parse_meta_1():
    test_dict = {
        "topkey" : {
            "user1" : {
                "__type__": "thewired.SecondLifeNode"
            }
        }
    }
    nscp = NamespaceConfigParser2()
    ns = nscp.parse(dictConfig=test_dict)
    print(ns.walk())

    assert isinstance(ns.root, NamespaceNodeBase)
    from thewired import SecondLifeNode
    assert isinstance(ns.get(".topkey.user1"), SecondLifeNode)



def test_parse_meta_2():
    test_dict = {
        "topkey" : {
            "user1" : {
                "__type__": "thewired.SecondLifeNode",
                "__init__": {
                    "a": "a value for param1",
                    "b" : "param2's value"
                }
            }
        }
    }

    nscp = NamespaceConfigParser2()
    ns = nscp.parse(dictConfig=test_dict)
    print(ns.walk())

    assert isinstance(ns.root, NamespaceNodeBase)

    from thewired import SecondLifeNode
    assert isinstance(ns.get(".topkey.user1"), SecondLifeNode)
    assert ns.get('.topkey.user1').a == "a value for param1"
    assert ns.get('.topkey.user1').b == "param2's value"
    assert ns.root.topkey.user1.a == "a value for param1"
    assert ns.root.topkey.user1.b == "param2's value"

def test_parse_meta_nested():
    test_dict = {
        "topkey" : {
            "subkey1" : {
                "__type__" : "thewired.testobjects.SomeNodeType",
                "__init__" : {
                    "something" : {
                        "__type__" : "thewired.testobjects.Something",
                        "__init__" : {
                            "arg1" : "some value"
                        }
                    }
                }
            }
        }
    }

    nscp = NamespaceConfigParser2()
    ns = nscp.parse(dictConfig=test_dict)
    print(ns.walk())

    assert isinstance(ns.root, NamespaceNodeBase)

    from thewired.testobjects import SomeNodeType
    assert isinstance(ns.get(".topkey.subkey1"), SomeNodeType)
