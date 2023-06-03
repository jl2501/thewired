"""
Purpose:
    a namespacenode node that can have its attributes changed at run time without ever changing the node itself
        - implements a second-level attribute lookup dict searched when not found in usual __dict__ (via implementing a __getattr__ )
        - this lookup method will return the output of whatever it finds as the provider for this attribute (a callable; 'provider' in the codebase) as the
          runtime value of the requested attribute

    with the provider namespace configuration files and the implementor provisioner scripts, this allows us to chop into small pieces how much code we have to write to create new functional namespaces that can begin to organize the functionality of the implementor SDK into logical namespaces

"""

from .base import NamespaceNodeBase
from thewired.namespace.nsid import is_valid_nsid_link
from thewired.exceptions import NamespaceLookupError,SecondLifeNsLookupError

from logging import getLogger, LoggerAdapter

logger = getLogger(__name__)



class SecondLifeNode(NamespaceNodeBase):
    def __init__(self, *args, nsid, namespace, secondlife_ns=None, secondlife=None, **kwargs):
        """
        Input:
            nsid: NSID string
            secondlife: attribute mapping dict
                keys are attributes to be implemented as lookups
                values are either:
                    * callable - value of attribute is return value of callable
                    * NSID - value of the attribute is return value from invoking the Node given by the NSID
                        - thus the node referred to must be callable
                    * anything else - if it doesn't match the others, return this value exactly as it is
        """
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}.__init__'))
        log.debug("entering")
        log.debug(f"Calling super().__init__: {args=} | {nsid=} | {namespace=} | {kwargs=}")
        super().__init__(*args, nsid=nsid, namespace=namespace, **kwargs)
        self._secondlife = secondlife
        self._attribute_lookup_fail_canary = "__ATTRIBUTE_LOOKUP_FAIL_CANARY__"
        self._secondlife_ns = secondlife_ns if secondlife_ns else self._ns
        log.debug("exiting")

    def __getattr__(self, attr):
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}.__getattr__'))
        log.debug(f"entering: {attr=}")
        secondlife_value = None
        raw_attr_value = self._secondlife.get(attr, self._attribute_lookup_fail_canary)

        if raw_attr_value == self._attribute_lookup_fail_canary:
            raise AttributeError(f"No such attribute: {attr}")
        if callable(raw_attr_value):
            secondlife_value = raw_attr_value()
        elif is_valid_nsid_link(raw_attr_value):
            log.debug(f"is_valid_nsid_link: {raw_attr_value=}")
            try:
                node = self._secondlife_ns.get(raw_attr_value)
            except NamespaceLookupError as err:
                raise SecondLifeNsLookupError(f"dynamic lookup of {raw_attr_value} failed") from err
            if attr == "__call__":
                secondlife_value = node()
            else:
                secondlife_value = node
        else:
            #- provider is not a callable nor an NSID
            #- whatever it is, just return it raw
            secondlife_value = raw_attr_value

        log.debug(f"exiting: {secondlife_value=}")
        return secondlife_value

    def __repr__(self):
        return f"{self.__class__.__name__}(nsid={self.nsid}, namespace={self._ns}, secondlifens={self._secondlife_ns},secondlife={self._secondlife})"


class CallableSecondLifeNode(SecondLifeNode):
    def __init__(self, *args, nsid, namespace, secondlife_ns=None, secondlife=None, **kwargs):
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}.__init__'))
        log.debug("entering")
        log.debug(f"Calling super().__init__: {args=} | {nsid=} | {namespace=} | {secondlife_ns=} | {secondlife=} | {kwargs=}")
        super().__init__(*args, nsid=nsid, namespace=namespace, secondLife_ns=secondlife_ns, secondLife=secondlife, **kwargs)
        log.debug("exiting")

    def __call__(self, *args, **kwargs):
        log = LoggerAdapter(logger, dict(name_ext=f'{self.__class__.__name__}.__call__'))
        log.debug(f"Entering: {args=} | {kwargs=}")
        callable_node = self._secondlife.get('__call__', self._attribute_lookup_fail_canary)
        if x == self._attribute_lookup_fail_canary:
            log.debug("No __call__ key in secondlifedict")
            return None

        x = callable_node(*args, **args)
        log.debug("secondlife['__call__']() returned {x}")
        return x
