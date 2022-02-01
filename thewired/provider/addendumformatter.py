from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import importlib, itertools
from collections.abc import Mapping, Iterable, Sequence

from thewired.exceptions import NamespaceLookupError
from thewired.util import is_nsid_ref
from .providerabc import Provider
from .parametizedcall import ParametizedCall

class AddendumFormatter(Provider):
    """
    Description:
        A Provider object providing a shape of:
            * concatenate a string onto an existing provider object
            * get the result from an eval of this operation
            * process these results with a formatter method
            * return the proceses results
    """
    def __init__(self, implementor_namespace, implementor, nsroot=None,
        addendum=None, formatter=None, implementor_key=None,\
        implementor_state_namespace=None, pre_exec=None, post_exec=None):
        """
        Input:
            addendum: string to be concatenated on to implementor object and eval'd
            formatter: callable to pass the returned value of the implementor. Final
                Return value comes from this method
            implementor_namespace: where to lookup the implmentor NSIDs
            implementor: NSID of object that implements the operations, or direct object
                to use as an override
            implementor_state_namespace: optional namespace to look into to dynamically
                control which specific implementors are being used
                Namespace structure is expected to mirror the implementors namespace and
                have the nodes support a "state" attribute that returns "on" or "off".
            pre_exec_call: what to call before evaluating the provider's implmentation
            post_exec_call: what to call after the provider's implementation has run

        Notes:
            roughly equivalent to:
                return self.formatter(eval("self.implementor{}".format(addendum)))
        """
        log = LoggerAdapter(logger, {'name_ext' : 'AddendumFormatter.__init__'})
        log.debug("Entering")
        self._pre_exec = pre_exec
        self._post_exec = post_exec
        self.implementor_ns = implementor_namespace
        self.implementor_state_ns = implementor_state_namespace

        self.formatter = lambda x: x

        if isinstance(implementor, str):
            #- treat as NSID
            log.debug(f"implementor is a string {implementor=}")
            self.implementor_nsid = implementor
            self.implementor = None
        else:
            log.debug(f"implementor is a non-string object {implementor=}")
            self.implmentor_nsid = None
            self.implementor = implementor

        #- addendums can be single string or list
        self._addendums = list()
        if isinstance(addendum, str):
            self._addendums.append(addendum)
        elif isinstance(addendum, Sequence):
            self._addendums.extend(addendum)

        self.nsroot = nsroot
        self.key = implementor_key

        if callable(formatter):
            self.formatter = formatter
        else:
            try:
                module_name = '.'.join(formatter.split('.')[0:-1][0])
                formatter_name = formatter.split('.')[-1]

            except (AttributeError, TypeError) as e:
                log.warning(f"Couldn't create formatter from {formatter}")
                msg = " will use direct return value of implementor {}".format(\
                        self.implementor_nsid)
                log.warning(msg)

            except IndexError as e:
                log.warning(f"defaulting to formatter {formatter} being a builtin...")
                module_name = "builtins"
                formatter_name = formatter

            module = importlib.import_module(module_name)
            try:
                self.formatter = getattr(module, formatter_name)
            except AttributeError as e:
                log.warning("failed to find {formatter} in 'builtins'. Using default formatter!")



    def get_addendum(self, nsid=None, implementor=None, *args, **kwargs):
        """
        Description:
            addendums can be callables or strings
            this wraps the differences up

        Input:
            nsid: nsid of the implementor to get the addendum for
            implementor: implementor object to get the addendum for
            *args: ignored
            **kwargs: passed to the ParametizedCall object if this is a dynamic addendum
                type
        """
        log = LoggerAdapter(logger, {'name_ext': 'AddendumFormatter.get_addendum'})
        log.debug("Entering")
        log.debug("args: {}".format(args))
        log.debug("kwargs: {}".format(kwargs))

        if implementor and self.key:
            log.debug("Getting key function")
            key_func = self.get_key_func()
            key = key_func(implementor)
        else:
            key = None
        log.debug("key: {}".format(key))

        log.debug("_addendums: {}".format(self._addendums))
        addendums = list()
        for addendum in self._addendums:
            if is_nsid_ref(addendum):
                log.debug("Dereferencing addendum: {}".format(addendum))
                addendum = self.nsroot.get(addendum)
            
            if isinstance(addendum, Mapping):
                log.debug("Found mapping addendum")
                if ParametizedCall.is_param_call_map(addendum):
                    log.debug("Found Parametized Call addendum")
                    method_name, params = ParametizedCall.get_params(addendum, **kwargs)
                    addendum = ParametizedCall(self.nsroot, method_name, params)
                    log.debug("Instantiated ParametizedCall")

            if callable(addendum):
                log.debug("Calling addendum w/ key: {}".format(key))
                addendums.append(addendum(nsid=nsid, implementor=implementor, key=key))
            else:
                log.debug("Using bare addendum text: {}".format(addendum))
                addendums.append(addendum)

        final_addendum = ''.join(addendums)
        log.debug("final addendum: {}".format(final_addendum))
        log.debug("Exiting")
        return final_addendum


    def get_key_func(self):
        """
        Description:
            key methods are possibly NSIDs, so we may have to look them up at run time.
        """
        if self.key:
            if is_nsid_ref(self.key):
                key_func = self.nsroot.get(self.key)
                return key_func
        else:
            return None


    def pre_exec_hook(*args, **kwargs):
        if self._pre_exec:
            if callable(self._pre_exec()):
                self._pre_exec()
            else:
                warnings.warn('{}: skipping non-callable pre_exec_hook'.format(self.nsid))


    def post_exec_hook(*args, **kwargs):
        if self._post_exec:
            if callable(self._post_exec()):
                self._post_exec()
            else:
                warnings.warn('{}: skipping non-callable post_exec_hook'.format(self.nsid))


    def _get_implementor_iterator(self):
        """
        Description:
            utility method for provide() that checks if we are overriding implementors
            with direct objects and creates an iterator for direct objects that may or may
            not already be iterable.

        Notes:
            this will always generate a value for looking up in the flipswitch namespace
            that will fail for direct overrides. This is intentional.
            There may be a valid use case for being able to pass in what flipswitch nsids
            you'd like to control your list of iterators, so perhaps this behavior will
            change
        """
        #- find which implementor object(s) to use
        if self.implementor is None:
            #- use NSID if there is no direct object
            implementor_root_node = self.implementor_ns.get(self.implementor_nsid)
            imp_iter = implementor_root_node._list_leaves(nsids=True)
        else:
            implementor = self.implementor
            #- make it an iterable
            if not isinstance(implementor, Iterable):
                try:
                    _iter = iter(implementor)
                    imp_iter = zip(itertools.repeat('_user_override_'), _iter)
                except TypeError:
                    #- can't make an iterator out of the implementor override
                    #- stick it in a list of one
                    imp_iter = [('_user_override_', implementor)]
            else:
                #- it is already an iterator, just give a fake NSID for the loop
                imp_iter = zip(itertools.repeat('_user_override_'), implementor)
        return imp_iter


    def provide(self, *args, request_id=None, show_progress=True, **kwargs):
        """
        Description:
            perform the implementation for the requested service

        Input:
            *args: passed into self.get_addendum method
            request_id: None (unused in this provider)
            show_progress: show a message when calling each implementor object
            **kwargs: passed into self.get_addendum method

        Notes:
            If an object is set for the 'implementor' attribute, this will be used as the
            implmentor object, else, we will default to looking up the implmentor in a
            root node and iterating over all the sub-nodes.
        """
        log = LoggerAdapter(logger, {'name_ext' : 'AddendumFormatter.provide'})
        log.debug("Entering")
        log.debug("varargs: {}".format(args))
        log.debug("kwargs: {}".format(kwargs))

        imp_iter = self._get_implementor_iterator()
        log.debug("got implementor iterator: {}".format(imp_iter))
        #- loop through all the iterators and apply the addendum
        all_outputs = list()
        formatted_outputs = list()
        all_formatted_outputs = list()
        for nsid, implementor in imp_iter:
            if self.implementor_state_ns:
                try:
                    log.debug("checking implementor flipswitch via nsid: {}".format(nsid))
                    if not self.implementor_state_ns.get(nsid):
                        #- skip til next implementor
                        log.debug("Skipping inactive implementor: {}".format(nsid))
                        continue
                except NamespaceLookupError:
                    log.warning("No dynamic state for implementor: {}".format(nsid))

            #- per-implementor addendums use key method
            addendum = self.get_addendum(nsid, implementor, *args, **kwargs)
            if show_progress:
                log.info("Calling: {}{}".format(nsid, addendum))

            #TODO: define globals and locals
            outputs = eval("implementor{}".format(addendum), globals(), locals())
            all_outputs += outputs
            formatted_outputs = self.formatter(outputs)
            all_formatted_outputs += formatted_outputs
            if show_progress:
                try:
                    n = len(list(outputs))
                except TypeError:
                    n = 1 if outputs else 0
                log.info("        {} objects returned".format(n))
        log.info("Total: {}".format(len(all_formatted_outputs)))
        return all_formatted_outputs


    def __str__(self):
        return 'AddendumFormatter: addendums={}, formatter={}'.format(self._addendums,\
            str(self.formatter))


    def __repr__(self):
        return str(self)
