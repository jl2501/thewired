import unittest

import collections
import logging, warnings

import thewired

from functools import partial

from thewired.namespace import Namespace
from thewired.namespace import NamespaceNode
from thewired.namespace import NamespaceNodeBase, SecondLifeNode
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


def test_parse_dynamic_type_callable(caplog):
    caplog.set_level(logging.DEBUG)
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
    subkey_node = ns.get('.topkey.subkey1')
    assert callable(subkey_node)
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

def test_input_mutator_3():
    """ test dict builtin """
    def input_mutator(dictConfig, key):
        print("input_mutator called!")
        new_key_name = "raw"

        mutated_config = {
            new_key_name: {
                "__class__": "builtins.dict",
                "__init__" : dictConfig[key]
            }
        }
        return mutated_config, new_key_name


    test_dict = {
        "topkey" : {
            "mutate_me" : {
                "a" : "a",
                "b": "b",
                "c": "c",
                "d": "d",
                "e": "e"
            }
        }
    }

    target_keys = ['mutate_me']
    parser = NamespaceConfigParser2(callback_target_keys=target_keys, input_mutator_callback=input_mutator)

    ns = parser.parse(test_dict)

    assert(isinstance(ns.root.topkey.raw, dict))
    assert(ns.root.topkey.raw.get('a', None) == 'a')




def test_input_mutator_3(caplog):
    """ test dict builtin wrapped inside a delegateNode """

    #caplog.set_level(logging.DEBUG)

    def input_mutator(dictConfig, key):
        print("input_mutator called!")
        new_key_name = "raw"

        mutated_config = {
            new_key_name: {
                "__class__": "thewired.DelegateNode",
                "__init__": {
                    "delegate" : {
                        "__class__": "builtins.dict",
                        "__init__" : dictConfig[key]
                    }
                }
            }
        }
        return mutated_config, new_key_name


    test_dict = {
        "topkey" : {
            "mutate_me" : {
                "a": "roses are red",
                "b": "violets are VIOLET",
                "c": "they aren't blue. they're VIOLET",
                "d": "they are so NOT blue, that we CALL THEM VIOLETS"
            }
        }
    }

    target_keys = ['mutate_me']
    parser = NamespaceConfigParser2(callback_target_keys=target_keys, input_mutator_callback=input_mutator)

    ns = parser.parse(test_dict)

    assert(isinstance(ns.root.topkey.raw, thewired.DelegateNode))
    assert(isinstance(ns.root.topkey.raw._delegate, dict))
    assert(ns.root.topkey.raw.get('a', None) == 'roses are red')
    assert(ns.root.topkey.raw.get('b', None) == 'violets are VIOLET')
    assert(ns.root.topkey.raw.get('c', None) == "they aren't blue. they're VIOLET")
    assert(ns.root.topkey.raw.get('d', None) == "they are so NOT blue, that we CALL THEM VIOLETS")


def test_input_mutator_4(caplog):
    """ test dict builtin on a nested dict, wrapped inside a delegateNode """

    #caplog.set_level(logging.DEBUG)

    def input_mutator(dictConfig, key):
        print("input_mutator called!")
        new_key_name = "raw"

        mutated_config = {
            new_key_name: {
                "__class__": "thewired.DelegateNode",
                "__init__": {
                    "delegate" : {
                        "__class__": "builtins.dict",
                        "__init__" : dictConfig[key]
                    }
                }
            }
        }
        return mutated_config, new_key_name


    test_dict = {
        "topkey" : {
            "mutate_me" : {
                "a": "roses are red",
                "b": "violets are VIOLET",
                "c": "they aren't blue. they're VIOLET",
                "d": {
                    "dd": "they are so NOT blue, that we CALL THEM VIOLETS"
                }
            }
        }
    }

    target_keys = ['mutate_me']
    parser = NamespaceConfigParser2(callback_target_keys=target_keys, input_mutator_callback=input_mutator)

    ns = parser.parse(test_dict)

    assert(isinstance(ns.root.topkey.raw, thewired.DelegateNode))
    assert(isinstance(ns.root.topkey.raw._delegate, dict))
    assert(ns.root.topkey.raw.get('a', None) == 'roses are red')
    assert(ns.root.topkey.raw.get('b', None) == 'violets are VIOLET')
    assert(ns.root.topkey.raw.get('c', None) == "they aren't blue. they're VIOLET")
    assert(isinstance(ns.root.topkey.raw.get('d', None), dict))
    assert(ns.root.topkey.raw.get('d', None).get('dd', None) == "they are so NOT blue, that we CALL THEM VIOLETS")



def test_input_mutator_5(caplog):
    """ test input mutator overwrite current node """

    #caplog.set_level(logging.DEBUG)

    def input_mutator(dictConfig, key):
        print("input_mutator called!")
        new_key_name = None

        mutated_config = {
            new_key_name: {
                "__class__": "thewired.DelegateNode",
                "__init__": {
                    "delegate" : {
                        "__class__": "builtins.dict",
                        "__init__" : dictConfig[key]
                    }
                }
            }
        }
        return mutated_config, new_key_name


    test_dict = {
        "topkey" : {
            "mutate_me" : {
                "a": "roses are red",
                "b": "violets are VIOLET",
                "c": "they aren't blue. they're VIOLET",
                "d": {
                    "dd": "they are so NOT blue, that we CALL THEM VIOLETS"
                }
            }
        }
    }

    target_keys = ['mutate_me']
    parser = NamespaceConfigParser2(callback_target_keys=target_keys, input_mutator_callback=input_mutator)

    ns = parser.parse(test_dict)

    assert(isinstance(ns.root.topkey, thewired.DelegateNode))
    assert(isinstance(ns.root.topkey._delegate, dict))
    assert(ns.root.topkey.get('a', None) == 'roses are red')
    assert(ns.root.topkey.get('b', None) == 'violets are VIOLET')
    assert(ns.root.topkey.get('c', None) == "they aren't blue. they're VIOLET")
    assert(isinstance(ns.root.topkey.get('d', None), dict))
    assert(ns.root.topkey.get('d', None).get('dd', None) == "they are so NOT blue, that we CALL THEM VIOLETS")


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

def test_parse_callable_node():
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
    assert(callable(ns.root.topkey.mutated_node))
    assert(ns.root.topkey.mutated_node() == 'called callfunc!')

def test_parse_dynamic_type_with_dynamic_init_param(caplog):
    #caplog.set_level(logging.DEBUG)
    log = logging.getLogger(f"{__name__}.test_parse_callable_node_recursive_param")

    test_dict = {
        "topkey" : {
            "subkey" : {
                "__type__" : {
                    "name" : "TestDynamicTypeWithDynamicInitParam",
                    "bases" : ["thewired.NamespaceNodeBase"],
                    "dict" : {
                        "dynamic_argument" : {
                            "__class__" : "thewired.testobjects.Something",
                            "__init__": {
                                "arg1" : "arg1's value"
                            }
                        }
                    }
                }
            }
        }
    }

    parser = NamespaceConfigParser2()
    ns = parser.parse(test_dict)
    print(f"{type(ns.root.topkey.subkey)=}")
    print(f"{type(ns.root.topkey.subkey.dynamic_argument)=}")
    assert(ns.root.topkey.subkey.__class__.__name__ == "TestDynamicTypeWithDynamicInitParam")
    assert(isinstance(ns.root.topkey.subkey.dynamic_argument, thewired.testobjects.Something))
    assert(ns.root.topkey.subkey.dynamic_argument.thing == "arg1's value")


def test_parse_resolve_nsid_ref():
    lookup_ns = Namespace()
    lookup_ns.add(".a.b.c.d.e.f.g")

    test_dict = {
        "topkey" : {
            "subkey" : {
                "referring_key" : "nsid-ref://.a.b.c.d"
            }
        }
    }

    parser = NamespaceConfigParser2(lookup_ns=lookup_ns)
    ns = parser.parse(test_dict)
    assert(isinstance(ns.root.topkey, thewired.NamespaceNodeBase))
    assert(isinstance(ns.root.topkey.subkey, thewired.NamespaceNodeBase))
    assert(lookup_ns.root.a.b.c.d.__class__ == ns.root.topkey.subkey.referring_key.__class__)

    #XXX the nsid-ref will break the NSIDs of the nodes that are referring at parse time
    # it will always overwrite the node directly
    assert(str(ns.root.topkey.subkey.referring_key.nsid) == ".a.b.c.d")

def test_parse_resolve_nsid_link():
    log = logging.getLogger()
    lookup_ns = Namespace()
    lookup_ns.add(".a.b.c.d.e.f.g")

    test_dict = {
        "topkey" : {
            "subkey" : {
                "referring_key" : "nsid://.a.b.c.d"
            }
        }
    }

    parser = NamespaceConfigParser2(lookup_ns=lookup_ns)
    ns = parser.parse(test_dict)
    assert(isinstance(ns.root.topkey, thewired.NamespaceNodeBase))
    assert(isinstance(ns.root.topkey.subkey, thewired.NamespaceNodeBase))
    assert(isinstance(ns.root.topkey.subkey, SecondLifeNode))

    assert str(ns.root.topkey.subkey.nsid) == ".topkey.subkey"
    assert str(ns.root.topkey.subkey.referring_key.nsid) == ".a.b.c.d"
