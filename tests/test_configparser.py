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



def test_NamespaceConfigParser_instantation():
    nscp = NamespaceConfigParser()
    assert(isinstance(nscp.new_node(), NamespaceNode))

def test_NamespaceConfigParser_instantiation_with_node_factory_override_1():
    nscp = NamespaceConfigParser(node_factory=NamespaceNodeSubclass)
    assert(isinstance(nscp.new_node(nsid='.test'), NamespaceNodeSubclass))

def test_NamespaceConfigParser_instantiation_with_node_factory_override_2():
    ns = Namespace(default_node_factory=NamespaceNodeBaseSubclass)
    nscp = NamespaceConfigParser(node_factory=ns.add)
    new_node = nscp.new_node(nsid='.test')[0]
    assert(isinstance(new_node, NamespaceNodeBaseSubclass))

def test_NamespaceConfigParser_instantiation_with_node_factory_override_3():
    ns = Namespace(default_node_factory=NamespaceNodeBaseSubclass)
    nfactory = partial(ns.add_exactly_one, node_factory=NamespaceNodeBaseSubclass)
    nscp = NamespaceConfigParser(node_factory=nfactory)
    new_node = nscp.new_node('.test')
    assert(isinstance(new_node, NamespaceNodeBaseSubclass))



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


def test_parse_existing_namespace():
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

    ns = Namespace()
    nscp = NamespaceConfigParser2(namespace=ns)
    nscp.parse(dictConfig=test_dict)

    for nsid in get_nsid_ancestry('.all.work.no.play.dull_boy'):
        assert isinstance(ns.get(nsid), NamespaceNodeBase)


    for nsid in get_nsid_ancestry('.hackers.on.planet.earth'):
        assert isinstance(ns.get(nsid), NamespaceNodeBase)


def test_parse_meta_1():
    test_dict = {
        "topkey" : {
            "user1" : {
                "__class__": "thewired.SecondLifeNode"
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
                "__class__": "thewired.SecondLifeNode",
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

def test_parse_meta_nested_1():
    test_dict = {
        "topkey" : {
            "subkey1" : {
                "__class__" : "thewired.testobjects.SomeNodeType",
                "__init__" : {
                    "something" : {
                        "__class__" : "thewired.testobjects.Something",
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

def test_parse_meta_nested_2():
    test_dict = {
        "topkey" : {
            "subkey1" : {
                "__class__" : "thewired.testobjects.SomeOtherNodeType",
                "__init__" : {
                    "somethingelse" : {
                        "__class__" : "thewired.testobjects.SomethingElse",
                        "__init__" : {
                            "something" : {
                                "__class__" : "thewired.testobjects.Something",
                                "__init__" : {
                                    "arg1" : "some value"
                                }
                            }
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

    from thewired.testobjects import SomeOtherNodeType
    assert isinstance(ns.get(".topkey.subkey1"), SomeOtherNodeType)
    assert ns.root.topkey.subkey1.something_elses_thing == "some value"


def test_parse_dynamic_type_1():
    def callfunc(self):
        s = "called callfunc!"
        print(s)
        return s

    test_dict = {
        "topkey" : {
            "subkey1" : {
                "__type__" : {
                    "name" : "SomeTypeName",
                    "bases" : ["thewired.NamespaceNodeBase"],
                    "dict" : {
                        "__call__" : callfunc
                    }
                }
            }
        }
    }

    parser = NamespaceConfigParser2()
    ns = parser.parse(test_dict)

    assert isinstance(ns.get('.topkey'), NamespaceNodeBase)

    #- always adds NamespaceNodeBase as a base type
    assert isinstance(ns.get('.topkey.subkey1'), NamespaceNodeBase)
    assert ns.get('.topkey.subkey1').__class__.__name__ == 'SomeTypeName'
    assert callable(ns.get('.topkey.subkey1'))
    assert ns.root.topkey.subkey1() == "called callfunc!"


def test_input_mutator_1():
    def callfunc(self):
        s = "called callfunc!"
        print(s)
        return s

    test_dict = {
        "topkey" : {
            "mutate_me" : {
                "__type__" : {
                    "name" : "SomeTypeName",
                    "bases" : ["thewired.NamespaceNodeBase"],
                    "dict" : {
                        "__call__" : callfunc
                    }
                }
            }
        }
    }

    target_keys = ['mutate_me']
    def input_mutator(dictConfig, key):
        print("input_mutator called!")
        mutated_config = dictConfig.copy()
        mutated_config[key]['__type__']['name'] = 'MutatedTypeName'
        return mutated_config, key

    parser = NamespaceConfigParser2(callback_target_keys=target_keys, input_mutator_callback=input_mutator)
    ns = parser.parse(test_dict)
    assert(ns.root.topkey.mutate_me.__class__.__name__ == 'MutatedTypeName')

def test_input_mutator_2():
    def callfunc(self):
        s = "called callfunc!"
        print(s)
        return s


    def input_mutator(dictConfig, key):
        print("input_mutator called!")
        mutated_config = dictConfig.copy()
        mutated_config[key]['__type__']['name'] = 'MutatedTypeName'
        mutated_config['mutated_node'] = mutated_config[key]
        mutated_config.pop(key)
        return mutated_config, 'mutated_node'

    test_dict = {
        "topkey" : {
            "mutate_me" : {
                "__type__" : {
                    "name" : "SomeTypeName",
                    "bases" : ["thewired.NamespaceNodeBase"],
                    "dict" : {
                        "__call__" : callfunc
                    }
                }
            }
        }
    }


    target_keys = ['mutate_me']
    parser = NamespaceConfigParser2(callback_target_keys=target_keys, input_mutator_callback=input_mutator)
    ns = parser.parse(test_dict)
    assert(ns.root.topkey.mutated_node.__class__.__name__ == 'MutatedTypeName')
    assert(str(ns.root.topkey.mutated_node.nsid) == '.topkey.mutated_node')

def test_parse_when_namespace_is_a_handle():
    test_dict = {
        "all" : {
            "work" : {
                "no" : {
                  "play" : {
                      "dull_boy" : {}
                  }
                }
            }
        }
    }

    nscp = NamespaceConfigParser2()
    ns = nscp.parse(dictConfig=test_dict)

    handle = ns.get_handle('.all.work.no')
    test_dict_2 = {
        "meaning" : {
            "will" : {
                "leave" : {
                  "you" : {
                      "empty_inside" : {}
                  }
                }
            }
        }
    }
    nscp = NamespaceConfigParser2(namespace=handle)
    nscp.parse(test_dict_2)

    for nsid in get_nsid_ancestry('.all.work.no.meaning.will.leave.you.empty_inside'):
        assert isinstance(ns.get(nsid), NamespaceNodeBase)
