"""
only exist to support tests

the parser can only use a non-default factory when it is importable
this makes these objects importable
"""

from thewired import NamespaceNodeBase, Namespace, Nsid


class Something(object):
    def __init__(self, arg1):
        self.thing = arg1

from typing import Union
NsidU = Union[str, Nsid]

class SomeNodeType(NamespaceNodeBase):
    def __init__(self, nsid: NsidU, namespace: Namespace, something: Something):
        self.somethings_thing = something.thing
        #super().__init__('.SomeNamespaceNode_Instance', Namespace())
        #lol. bug ^^ that confuses ns.add() TODO fix
        super().__init__(nsid, namespace)


class SomethingElse(object):
    def __init__(self, something: Something):
        self.somethings_thing = something.thing

class SomeOtherNodeType(NamespaceNodeBase):
    def __init__(self, nsid: NsidU, namespace: Namespace, somethingelse: SomethingElse):
        self.something_elses_thing = somethingelse.somethings_thing
        super().__init__(nsid, namespace)
