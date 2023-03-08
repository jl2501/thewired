import logging
import unittest

import thewired.namespace 
from thewired.namespace.nsid import make_child_nsid
from thewired.exceptions import InvalidNsidError, NamespaceLookupError
from thewired.exceptions import NamespaceCollisionError
from thewired.namespace import Namespace, NamespaceNodeBase, HandleNode

class TestNamespace(unittest.TestCase):
    def test_default_instantiation(self):
        ns = thewired.namespace.Namespace()

    def test_get_root_node(self):
        ns = Namespace()
        root = ns.get('.')
        self.assertEqual(ns.root, root)

    def test_add_node_return1(self):
        ns = Namespace()
        new_nsid = '.a'
        new_nodes = ns.add(new_nsid)
        #- add returns all the new nodes created in order of creation
        #- so the last one in the list will be the deepest child
        new_node = new_nodes[-1]
        self.assertEqual(str(new_nodes[-1].nsid), new_nsid)

    def test_add_node_return2(self):
        ns = Namespace()
        new_nsid = '.a.b'
        new_nodes = ns.add(new_nsid)
        #- add returns all the new nodes created in order of creation
        #- so the last one in the list will be the deepest child
        new_node = new_nodes[-1]
        self.assertEqual(str(new_nodes[-1].nsid), new_nsid)


    def test_add_bad_node1(self):
        ns = Namespace()
        # nsids must start with a dot
        new_nsid = 'a'
        with self.assertRaises(InvalidNsidError):
            new_nodes = ns.add(new_nsid)

    def test_add_bad_node2(self):
        ns = Namespace()
        # nsids must start with a dot
        new_nsid = 'a.b'
        with self.assertRaises(InvalidNsidError):
            new_nodes = ns.add(new_nsid)

    def test_add_then_get_new_node(self):
        ns = Namespace()
        new_nsid = '.a.b.c.d.e'
        ns.add(new_nsid)
        node = ns.get(new_nsid)
        self.assertEqual(new_nsid, str(node.nsid))

    def test_add_then_get_ancestor(self):
        ns = Namespace()
        parent_nsid = '.a.b.c.d.e'
        child_nsid = make_child_nsid(parent_nsid, 'f')
        ns.add(child_nsid)
        node = ns.get(parent_nsid)
        self.assertEqual(parent_nsid, str(node.nsid))

    def test_add_then_get_bad(self):
        ns = Namespace()
        new_nsid = '.a.b.c.d.e'
        bad_new_nsid = '.a.b.c.d.e.f'
        ns.add(new_nsid)
        with self.assertRaises(NamespaceLookupError):
            node = ns.get(bad_new_nsid)

    def test_delete_node(self):
        ns = Namespace()
        new_nsid = '.a.b.c.d'
        ns.add(new_nsid)
        node = ns.remove(new_nsid)
        self.assertEqual(str(node.nsid), new_nsid)
        with self.assertRaises(NamespaceLookupError):
            ns.get(new_nsid)

    def test_add_exactly_one_happy_path(self):
        ns = Namespace()
        nsid = '.one_new_node'
        new_node = ns.add_exactly_one(nsid)
        self.assertEqual(str(new_node.nsid), nsid)

    def test_add_exactly_one_bad_input(self):
        ns = Namespace()
        nsid = '.two.nodes'
        with self.assertRaises(ValueError):
            new_node = ns.add_exactly_one(nsid)

        nsid = '.now.three.nodes'
        with self.assertRaises(ValueError):
            new_node = ns.add_exactly_one(nsid)
    
    def test_add_root_node(self):
        ns = Namespace()
        with self.assertRaises(NamespaceCollisionError):
            ns.add_exactly_one('.')

    def test_default_node_factory_bad_input(self):
        def bad_factory(x=None):
            pass
        with self.assertRaises(ValueError):
            ns = Namespace(default_node_factory=bad_factory)
        with self.assertRaises(ValueError):
          ns = Namespace(default_node_factory=['a','list','?'])

    def test_default_node_factory(self):
        class NewNamespaceNodeBase(NamespaceNodeBase):
            def __init__(self, nsid=None, namespace=None):
                super().__init__(nsid=nsid, namespace=namespace)

        ns = Namespace(default_node_factory=NewNamespaceNodeBase)
        new_nodes = ns.add('.this.is.all.new')

        for node in new_nodes:
            self.assertIsInstance(node, NewNamespaceNodeBase)

    def test_basic_walk(self):
        ns = Namespace()
        self.assertEqual({"." : {}}, ns.walk())

    def test_walk(self):
        ns = Namespace()
        ns.add('.all.work.no_play.dull_boy')
        ns.add('.hackers.on.planet.earth')
        test_dict = {
            "." : {
                "all" : {
                    "work" : {
                        "no_play" :  {
                            "dull_boy" : {}
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
        }
        self.assertEqual(ns.walk(), test_dict)


    def test_bad_get(self):
        ns = Namespace()
        with self.assertRaises(NamespaceLookupError):
            ns.get(".something.that.does.not.exist.and.is.long")

    def test_bad_get2(self):
        ns = Namespace()
        ns.add('.something.that')

        with self.assertRaises(NamespaceLookupError):
            ns.get(".something.that.does.not.exist.and.is.long")

    def test_root_delegate(self):
        ns = Namespace()
        ns.add('.a.few.nodes')

        #make sure it exists with this name
        ns.a.few.nodes.attr = "val"
        assert ns.a.few.nodes.attr == "val"

    def test_get_handle(self):
        ns = Namespace()
        ns.add(".add.some.stuff.here")
        ns.add(".other.stuff.added.here.now")

        handle = ns.get_handle(".other.stuff")
        assert isinstance(handle.added.here, NamespaceNodeBase)

    def test_get_nonexisting_handle(self):
        ns = Namespace()
        handle = ns.get_handle(".something.totally.new", create_nodes=True)
        assert str(handle.get('.')._delegate.nsid) == ".something.totally.new"

    def test_get_nonexisting_handle_fail(self):
        ns = Namespace()
        with self.assertRaises(NamespaceLookupError):
            handle = ns.get_handle(".something.totally.new")

    def test_handle_get(self):
        ns = Namespace()
        ns.add(".add.some.stuff.here")
        ns.add(".other.stuff.added.here.now")

        handle = ns.get_handle(".other.stuff")
        #assert isinstance(handle.get('.added.here'), NamespaceNodeBase)
        assert isinstance(handle.get('.added.here'), HandleNode)

    def test_handle_add(self):
        ns = Namespace()
        ns.add(".more.stuff.here.too")

        handle = ns.get_handle(".more.stuff.here.too")
        new_node = handle.add(".subtree")[0]
        assert isinstance(handle.subtree, NamespaceNodeBase)

    def test_handle_remove(self):
        ns = Namespace()
        ns.add(".more.stuff.here.too")

        handle = ns.get_handle(".more.stuff.here")
        node = handle.remove(".too")

        assert node.nsid.nsid == ".more.stuff.here.too"

def test_get_subnodes():
    ns = Namespace()
    ns.add(".a.few.nodes.here.and.there.and.everywhere")

    subnodes = ns.get_subnodes('.a.few')
    nsids = [str(x.nsid) for x in subnodes]

    assert nsids == ['.a.few.nodes', '.a.few.nodes.here', '.a.few.nodes.here.and', '.a.few.nodes.here.and.there', '.a.few.nodes.here.and.there.and', '.a.few.nodes.here.and.there.and.everywhere']


def test_get_subnodes_root():
    ns = Namespace()
    ns.add(".a.b.c")
    subnodes = ns.get_subnodes('.')
    nsids = [str(x.nsid) for x in subnodes]

    assert nsids == ['.a', '.a.b', '.a.b.c']


def test_get_subnodes_from_handle():
    ns = Namespace()
    ns.add(".a.few.nodes.here.and.there.and.everywhere")
    handle = ns.get_handle(".a.few")

    subnodes = handle.get_subnodes('.nodes.here.and.there')
    nsids = [str(x.nsid) for x in subnodes]

    assert nsids == ['.nodes.here.and.there.and', '.nodes.here.and.there.and.everywhere']

def test_get_subnodes_from_handle_root():
    ns = Namespace()
    ns.add(".a.b.c.d")
    handle = ns.get_handle(".a.b")

    subnodes = handle.get_subnodes('.')
    nsids = [str(x.nsid) for x in subnodes]

    assert nsids == ['.c', '.c.d']



def test_get_subnodes_from_nested_handles(caplog):
    ns = Namespace()
    #caplog.set_level(logging.DEBUG)
    ns.add(".a.few.nodes.here.and.there.and.everywhere")
    handle1 = ns.get_handle(".a.few")
    handle2 = handle1.get_handle(".nodes")

    subnodes = handle2.get_subnodes('.here.and.there')
    nsids = [str(x.nsid) for x in subnodes]

    assert nsids == ['.a.few.nodes.here.and.there.and', '.a.few.nodes.here.and.there.and.everywhere']
