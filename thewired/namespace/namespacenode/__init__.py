"""
Purpose:
    NamespaceNode objects have several different access patterns and semantics that can be
    grouped into types and represented more clearly by leveraging the type system.

    All the NamespaceNode subclasses in this package are limited in definition and
    semantics to specific use cases.
"""
from .namespacenode import NamespaceNode
from .base import NamespaceNodeBase
from .secondlife import SecondLifeNode, CallableSecondLifeNode
from .delegate import DelegateNode, CallableDelegateNode
from .handle import HandleNode, CallableHandleNode
