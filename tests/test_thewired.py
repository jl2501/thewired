import thewired
import unittest
from pprint import pprint

class Node2(thewired.NamespaceNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class test_thewired(unittest.TestCase):
    namespace_test_dict = {
            'root' : {
                'child1' : {
                    'c1_attr1': 'value1',
                    'c1_attr2': 'value2',
                },
                'child2' : {
                    'child3' : {
                        'c3_attr1': 'value3',
                        'c3_attr2' : 'value4'
                    },
                    'child4' : {'c4_attr1': 'value5'}
                },
                'child5' : {'c5_attr1': 'value6'}
            }
    }

    def test_build_tree_namespace_ids(self):
        """test thewired.build_tree method"""
        #built_tree = thewired.build_tree(self.namespace_test_dict)
        nscp = thewired.NamespaceConfigParser()
        built_tree = nscp.parse(self.namespace_test_dict)[0]
        #print(f"built_tree: {built_tree}")
        #print(f"dir(built_tree): {dir(built_tree)}")

        root_node = thewired.NamespaceNode('root')

        setattr(root_node, 'child1', thewired.NamespaceNode('root.child1'))
        setattr(root_node, 'child2', thewired.NamespaceNode('root.child2'))
        setattr(root_node, 'child5', thewired.NamespaceNode('root.child5'))

        setattr(root_node.child1, 'c1_attr1', thewired.NamespaceNode('root.child1.c1_attr1'))
        setattr(root_node.child1, 'c2_attr2', thewired.NamespaceNode('root.child1.c2_attr2'))

        setattr(root_node.child2, 'child3', thewired.NamespaceNode('root.child2.child3'))
        setattr(root_node.child2.child3, 'c3_attr1', thewired.NamespaceNode('root.child2.child3.c3_attr1'))
        setattr(root_node.child2.child3, 'c3_attr2', thewired.NamespaceNode('root.child2.child3.c3_attr2'))
        setattr(root_node.child2.child3, 'c3_attr3', thewired.NamespaceNode('root.child2.child3.c3_attr3'))

        setattr(root_node.child2, 'child4', thewired.NamespaceNode('root.child2.child4'))
        setattr(root_node.child2.child4, 'c4_attr1', thewired.NamespaceNode('root.child2.child4.c4_attr1'))
        test_tree = root_node

        self.assertEqual(root_node._namespace_id, built_tree._namespace_id)

        #print(f"type(root_node.child1): {type(root_node.child1)}")
        #print(f"type(built_tree.child_1): {type(built_tree.child1)}")
        self.assertEqual(root_node.child1._namespace_id, built_tree.child1._namespace_id)
        self.assertEqual(root_node.child2._namespace_id, built_tree.child2._namespace_id)
        self.assertEqual(root_node.child5._namespace_id, built_tree.child5._namespace_id)

        self.assertEqual(root_node.child2.child3._namespace_id, built_tree.child2.child3._namespace_id)
        self.assertEqual(root_node.child2.child4._namespace_id, built_tree.child2.child4._namespace_id)



if __name__ == '__main__' :
    unittest.main()
