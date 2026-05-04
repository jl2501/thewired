class TheWiredError(Exception):
    """Base class for all exceptions in thewired lib"""
    pass

class CollectiveEvalDelegateObjectError(TheWiredError, AttributeError):
    """
    Description:
        raised from within FilteredCollection objects collective_eval.
        Subclasses from AttributeError in order to fit in with expected semantics for
        copy.deepcopy()
    """
    pass

class NamespaceError(TheWiredError):
    pass

class NamespaceLookupError(NamespaceError, AttributeError):
    pass

class NamespaceCollisionError(NamespaceError):
    pass

class NamespaceConfigParsingError(NamespaceError, SyntaxError):
    pass

class NamespaceInternalError(NamespaceError, RuntimeError):
    pass

class ProviderError(TheWiredError, RuntimeError):
    pass

class ProviderMapLookupError(TheWiredError, KeyError):
    pass

class NsidError(TheWiredError):
    pass

class NsidSanitizationError(NsidError):
    pass

class InvalidNsidError(NsidError):
    pass

class SecondLifeError(TheWiredError):
    pass

class SecondLifeNsLookupError(SecondLifeError, NamespaceLookupError):
    pass
