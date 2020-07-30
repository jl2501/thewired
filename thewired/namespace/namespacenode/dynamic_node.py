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
