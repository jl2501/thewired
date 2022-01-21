
class CollectiveEvalDelegateObjectError(AttributeError):
    """
    Description:
        raised from within FilteredCollection objects collective_eval.
        Subclasses from AttributeError in order to fit in with expected semantics for
        copy.deepcopy()
    """
    pass

class NamespaceError(Exception):
    pass

class NamespaceLookupError(NamespaceError, AttributeError):
    pass

class NamespaceCollisionError(NamespaceError):
    pass

class NamespaceConfigParsingError(NamespaceError, SyntaxError):
    pass

class NamespaceInternalError(NamespaceError, RuntimeError):
    pass

class ProviderError(RuntimeError):
    pass

class ProviderMapLookupError(KeyError):
    pass

class NsidError(Exception):
    pass

class NsidSanitizationError(NsidError):
    pass

class InvalidNsidError(NsidError):
    pass
