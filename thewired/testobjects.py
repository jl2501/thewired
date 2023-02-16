"""
only exist to support tests

the parser can only use a non-default factory when it is importable
this makes these objects importable
"""

from thewired import NamespaceNodeBase, Namespace, Nsid
from typing import Union
NsidU = Union[str, Nsid]


class Something(object):
    def __init__(self, arg1):
        self.thing = arg1

class CallableSomething(Something):
    def __init__(self, arg1):
        super().__init__(arg1)

    def __call__(self, *args, **kwargs):
        params = f"{args=} {kwargs=}"
        ret = f"Called with {params}"
        print(ret)
        return ret


class Something(object):
    def __init__(self, arg1):
        self.thing = arg1
class SomeNodeType(NamespaceNodeBase):
    def __init__(self, something: Something, *, nsid: NsidU, namespace: Namespace):
        self.somethings_thing = something.thing
        #super().__init__('.SomeNamespaceNode_Instance', Namespace())
        #lol. bug ^^ that confuses ns.add() TODO fix
        super().__init__(nsid=nsid, namespace=namespace)


class SomethingElse(object):
    def __init__(self, something: Something):
        self.somethings_thing = something.thing

class SomeOtherNodeType(NamespaceNodeBase):
    def __init__(self, somethingelse: SomethingElse, *, nsid: NsidU, namespace: Namespace):
        self.something_elses_thing = somethingelse.somethings_thing
        super().__init__(nsid=nsid, namespace=namespace)
