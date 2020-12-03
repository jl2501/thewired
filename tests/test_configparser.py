import thewired
import unittest

from thewired.namespace import Namespace
from thewired.namespace import NamespaceNode
from thewired.namespace import NamespaceNodeBase
from thewired.namespace.nsid import get_nsid_ancestry
from thewired import NamespaceConfigParser
from thewired import NamespaceConfigParser2

class test_NamespaceConfigParser1(unittest.TestCase):

    def test_NamespaceConfigParser_instantation(self):
        nscp = NamespaceConfigParser()
        self.assertIsInstance(nscp.new_node(), NamespaceNode)

    def test_NamespaceConfigParser_instantation_with_node_factory_override(self):
        nscp = NamespaceConfigParser(node_factory=NamespaceNodeBase)
        self.assertIsInstance(nscp.new_node(nsid='.test'), NamespaceNodeBase)

    def test_NamespaceConfigParser_instantation_with_node_factory_override_2(self):
        ns = Namespace()
        nscp = NamespaceConfigParser(node_factory=ns.add)
        self.assertIsInstance(nscp.new_node(nsid='.testt')[0], NamespaceNodeBase)

    def test_nscp_instantiation_with_node_factory_override_3(self):
        ns = Namespace()
        nscp = NamespaceConfigParser(node_factory=ns.add_exactly_one)
        self.assertIsInstance(nscp.new_node('.test'), NamespaceNodeBase)



class test_NamespaceConfigParser2(unittest.TestCase):
    def test_NamespaceConfigParser_instantation(self):
        nscp = NamespaceConfigParser2()

    def test_nscp_parse(self):
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

        nscp = NamespaceConfigParser2(prefix='')
        ns = nscp.parse(dictConfig=test_dict)
        for nsid in get_nsid_ancestry('.all.work.no.play.dull_boy'):
            assert isinstance(ns.get(nsid), NamespaceNodeBase)


        for nsid in get_nsid_ancestry('.hackers.on.planet.earth'):
            assert isinstance(ns.get(nsid), NamespaceNodeBase)


    def test_parse_meta(self):
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
