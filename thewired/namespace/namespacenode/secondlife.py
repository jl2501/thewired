"""
Purpose:
    a namespacenode node that can have its attributes changed at run time without ever changing the node itself
        - implements a second-level attribute lookup dict searched when not found in usual __dict__ (via implementing a __getattr__ )
        - this lookup method will return the output of whatever it finds as the provider for this attribute (a callable; 'provider' in the codebase) as the
          runtime value of the requested attribute

    with the provider namespace configuration files and the implementor provisioner scripts, this allows us to chop into small pieces how much code we have to write to create new functional namespaces that can begin to organize the functionality of the implementor SDK into logical namespaces

 this functionality is essentially what the whole point of this library actually is. the rest of it is just shit I had to do to get this part in a way that is simple to digest, debug and maintain

 it is a refactor of the provider_map implementation in the original polyglot NamespaceNode code
"""

from .base import NamespaceNodeBase
from thewired.namespace.nsid import is_valid_symref_str

class SecondLifeNode(NamespaceNodeBase):
    def __init__(self, nsid, secondlife=None):
        """
        Input:
            nsid: NSID string
            secondlife: attribute mapping dict
                keys are nams of attributes to find in this node
                values are either:
                    * callable - value of attribute is return value of callable
                    * NSID - value of the attribute is return value from invoking the Node given by the NSID
                    * anything else - if it doesn't match the others, return this value exactly as it is
        """
        super().__init__(nsid)
        self._secondlife = secondlife

    def __getattr__(self, attr):
        secondlife_value = None
        raw_attr_value = self._secondlife.get(attr, None)

        if not raw_attr_value:
            raise AttributeError(f"No such attribute: {attr}")

        if callable(raw_attr_value):
            provider = raw_attr_value
            secondlife_value = provider()
        elif is_valid_symref_str(raw_attr_value):
            print(f"VALID NSID DETECTED: {raw_attr_value}")
            pass
            #TODO: lookup NSID
        else:
            #- provider is not a callable nor an NSID
            #- whatever it is, just return it raw
            secondlife_value = raw_attr_value

        return secondlife_value
