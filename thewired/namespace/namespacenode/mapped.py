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
from thewired.namespace.nsid import is_valid_nsid_str

class MappedAttributesNode(NamespaceNodeBase):
    def __init__(self, nsid, attribute_map=None):
        super().__init__(nsid)
        self._attribute_map = attribute_map

    def __getattr__(self, attr):
        attr_value = None
        raw_attr_value = self._attribute_map.get(attr, None)

        if not raw_attr_value:
            raise AttributeError(f"No such attribute: {attr}")

        if callable(raw_attr_value):
            provider = raw_attr_value
            attr_value = provider()
        elif is_valid_nsid_str(raw_attr_value):
            print(f"VALID NSID DETECTED: {raw_attr_value}")
            pass
            #TODO: lookup NSID
        else:
            #- provider is not a callable nor an NSID
            #- whatever it is, just return it raw
            attr_value = raw_attr_value

        return attr_value

#- SecondLifeNode/ SecondLifeMapNode might be a more clear name
#- as essentially we just make a second __dict__ lookup in
#- our own internal mapping if python's normal attribute lookup fails
#- (in which case it will call __getattr__ if defined, and thus we do)
#- so its kinda like the attribute has a second life, or a second chance
#- to be found if a theres an entry for it in this mapping and to figure out
#- what we want the run time value to be, the value object in the second life mapping
#- can also be a callable, in which case we call the object to obtain the value for the attribute
#- It can also be a namespace ID (nsid) in which case we will attempt to look up a namespace object
#- by that name and then invoke it, returning the value of this invocation.
SecondLifeMapNode = MappedAttributesNode
