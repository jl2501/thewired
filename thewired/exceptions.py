
class CollectiveEvalDelegateObjectError(AttributeError):
    """
    Description:
        raised from within FilteredCollection objects collective_eval.
        Subclasses from AttributeError in order to fit in with expected semantics for
        copy.deepcopy()
    """
    pass

class NamespaceLookupError(AttributeError):
    pass

class NamespaceCollisionError(Exception):
    pass

class NamespaceConfigParsingError(SyntaxError):
    pass

class InternalError(RuntimeError):
    pass

class NamespaceInternalError(InternalError):
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
