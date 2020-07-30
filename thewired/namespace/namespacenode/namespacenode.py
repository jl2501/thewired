import collections
import itertools
import re
import warnings
from functools import partial

from thewired.exceptions import NamespaceLookupError, ProviderError, ProviderMapLookupError
from types import SimpleNamespace
from thewired.provider import ProviderMap
from thewired.util import is_nsid_ref, get_nsid_from_ref

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)


class NamespaceNode(SimpleNamespace):
    """
    Description:
        NamespaceNode objects come in two types: provided or unprovided, determined by the
        value of the special 'provider_map' attribute.

        Conceptually, these act like SimpleNamespace objects, with the addition of an
        optional namespace identifier (the nsid property) and can have a provider_map
        object set that will take care of implmenting attributes that trigger a call to
        __getattr__ via the normal python modes of invoking this method.

        Provided NamespaceNodes have the special 'provider_map' attribute set to a
        ProviderMap object.

        Unprovided NamespaceNodes have the special 'provider_map' attribute set to None.

        To turn one into the other, set or remove the provider_map attribute which is used
        during a call to __getattr__() to see how to provide the implementation for a
        requested attribute. As the provider is called from within __getattr__, if the
        NamespaceNode has the requested attribute in its __dict__ directly, the provider
        mapping will be skipped as there will be no call to __getattr__.

        The provider_map attribute is a mapping of attribute names to callable Provider
        objects (inherit from thewired.provider.Provider) that will be invoked and passed
        the NamespaceNode object and the name of the requested attribute. The provider is
        responsible for returning the value that should be used for the requested
        attribute access, or raising an exception, if appropriate.

        NamespaceNodes have a namespace_id which serves to identify them specifically
        so that a generic provider can be used that will be able to lookup the appropriate
        action to take based on the ProvidedNode's namespace_id and the requested
        attribute.
    """
    _nsid_ref_prefix = 'nsid://'

    def __init__(self, namespace_id=None, provider_map=None,\
        ns_items=None, nsroot=None, is_nsroot=False, **kwargs):
        """
        Input:
            namespace_id: the namespace id of this ProvidedNode object.
            provider_map: provides the missing attributes via __getattr__
            ns_items: dict of items to add
            nsroot: the root of the namespace to use for symbolic reference lookups
            is_nsroot: set this node to be the nsroot of the rest of the children nodes
            **kwargs: kw attributes set as per SimpleNamespace

        """
        log = LoggerAdapter(logger, {'name_ext': 'NamespaceNode.__init__'})
        #- using ghost is deprecated and will be removed
        #- TODO: remove ghost
        self._ghost = None

        #- identify lookup values referring to other NSIDs in other namespaces
        self._namespace_id = '_anonymous_' if namespace_id is None else\
            self._sanitize_nsid(namespace_id)

        self._name = self._namespace_id.split('.')[-1]
        self._provider_map = provider_map

        if ns_items and isinstance(ns_items, collections.Mapping):
            self._ns_items = dict(ns_items)
        else:
            self._ns_items = dict()

        #- new node factory
        self._new_node = self.__class__
        if namespace_id == '.' or is_nsroot:
            self._nsroot = self
        else:
            self._nsroot = nsroot

        if self._nsroot:
            #- add future child nodes will have this node set as nsroot
            #- if created with methods from this node
            self._new_node = partial(self._new_node, nsroot=self._nsroot)
            #- update possibly already existing children in ns_items
            for item in self._ns_items.values():
                item._nsroot = self._nsroot
            #if self._nsroot is not self:
            #    #- nsroot needs to also be linked to self
            #    log.debug("Adding self into nsroot")
            #    #STACK OVERFLOW here +
            #    #                    |
            #    #                    v
            #    #self._nsroot._add_item(self._nsid, self, overwrite=True)
        else:
            msg = "NamespaceNodes with 'None' for nsroot is deprecated.({})".format(\
                namespace_id)
            warnings.warn(msg)
                


        #- set raw attributes directly via SimpleNamespace.__init__
        super().__init__(**kwargs)


    @staticmethod
    def _sanitize_nsid(nsid):
        """
        Description: 
            take a proposed NSID and remove consecutive dots
        Input:
            unsanitized nsid string
        Output:
            standard-conformant nsid string
        """
        logname = {'name_ext' : 'NamespaceNode._sanitize_nsid'}
        log = LoggerAdapter(logger, logname)
        sanitized_nsid = re.sub("\.\.+", ".", nsid)
        if sanitized_nsid != nsid:
            log.debug("Sanitized NSID: {} ---> {}".format(\
                nsid, sanitized_nsid))
        return sanitized_nsid



    def _add_child(self, child_name, overwrite=False):
        """
        Description:
            add a child node to this node
        Input:
            child_name: child's namespace id without prefix

        Effects:
            adds a new instance of this class to self named 'child_name' with its nsid set
            correctly
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._add_child'})
        log.debug('{}: adding child node: {}'.format(self._nsid, child_name))
        if self._nsroot == self:
            #- we are nsroot
            child_nsid = self._nsid + child_name
        else:
            child_nsid = '.'.join( [self._nsid, child_name] )
        new_node = self._new_node(child_nsid, nsroot=self._nsroot)
        self._add_item(child_name, new_node, iter=True, overwrite=overwrite)
        return new_node


    def __getattr__(self, attr):
        """
        Description:
            called when attribute lookup fails. used to implement semantics for provided
            attributes. If Python calls this method we will use this class'
            provider_map to get the provider for this attribute access and then call
            the provider and return the provider's return value as the value of the
            attribute

        Input:
            attr: the name of the attribute that wasn't found via the normal Python
            attribute lookup mechanisms.

        Output:
            Output of the provider returned by the provider factory of this class.
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode.__getattr__'})
        log.debug('{}.__getattr__({})'.format(self._nsid, attr))
        if self._provider_map:
            try:
                if callable(self._provider_map[attr]):
                    self._ghost = self._provider_map[attr]()
                #- TODO: allow a string to be set. Use more specific logic
                #- TODO:     to determine if this is an NSID
                elif isinstance(provider_map[attr], str):
                    #- treat as NSID
                    try:
                        provider = self.provider_ns._lookup(self._provider_map[attr])
                        self._ghost = provider()
                    except NamespaceLookupError as err:
                        raise ProviderError from err
                    except TypeError as err:
                        log.error(f'{self._nsid}.{attr}: provider not callable')
            except ProviderError as err:
                log.error('{}: provider error: {}'.format(self._nsid, err))
            except ProviderMapLookupError as err:
                log.error('No mapped provider for {}.{}'.format(self._nsid, attr))
                raise AttributeError from err

            log.debug('{}.{} provider returned: {}'.format(self._nsid, attr, self._ghost))
        else:
            raise AttributeError('{} object has no provider_map and no attribute \'{}\''.format(\
                self.__class__.__name__, attr))

        return self._ghost


    def __call__(self, *args, **kwargs):
        log = LoggerAdapter(logger, {'name_ext': 'NamespaceNode.__call__'})
        log.debug("args: {}".format(args))
        log.debug("kwargs: {}".format(kwargs))
        if self._provider_map is None:
            raise TypeError('{} object is not callable'.format(self.__class__.__name__))
        else:
            provider = self._provider_map.get_provider('__call__')
            self._ghost = provider(*args, **kwargs)
            return self._ghost


    @property
    def _nsid(self):
        return self._namespace_id

    @_nsid.setter
    def _nsid(self, value):
        self._namespace_id = value

    @property
    def _provider_map(self):
        return self.__provider_map

    @_provider_map.setter
    def _provider_map(self, mapping):
        """
        Description:
            implement setting the provider map for this object

        Restrictions:
            * All values for the provider map must inherit from Provider ABC

        Raises:
            ValueError if any value is not an instance of Provider ABC
        """

        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode.provider_map setter'})
        log.debug('setting providers for NamespaceNode {}'.format(self._nsid))
            
        self.__provider_map = ProviderMap(mapping=mapping)



    def __repr__(self):
        repr = '{}( namespace_id={}, provider_map={}, ghost={})'.format(\
            self.__class__.__name__, self._namespace_id, self._provider_map.__repr__(),\
            self._ghost.__repr__())

        #repr += 'ns_items = ['
        #for ns_item in self._ns_items:
        #    repr += "\n    {}".format(ns_item.__repr__())
        #repr += '])\n'

        return repr



    def __str__(self):
        return '{}( {} )'.format(self.__class__.__name__, self._namespace_id)


    def __dir__(self):
        original_dir = super().__dir__()
        original_dir.remove('__call__')  # only useable if in provider map
        extended_dir = list(self.__provider_map.keys())

        return original_dir + extended_dir



    def _name_to_path(self, name):
        """
        Description:
            internal utility method to split a name into a list of namespace components

        Input:
            name: what to split into a list of components
        """
        #return filter(None, name.split('.'))
        return name.split('.')


    def _lookup(self, namespace_id, follow_symrefs=True):
        """
        Description:
            Get an object in the namespace by its namespace id
        Input:
            namespace_id: id of the object to retrieve
            follow_symrefs: whether or not to try to perform a deep lookup
                deep lookups can contain other NSIDs which will be looked up in turn until
                a final value is found and returned. For this feature to be enabled, this
                node's ._nsroot attribute must also be a valid NamespaceNode-like object
                that supports a lookup() method that will be passed an NSID.

        Output:
            item if found, else NamespaceLookupError raised
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._lookup'})
        log.debug('[{}] lookup([{}])'.format(self._nsid, namespace_id))
        obj = None

        if follow_symrefs and is_nsid_ref(namespace_id): 
            value = self._lookup_symbolic_ref(namespace_id)
            return value

        else:
            #- split the NSID by path seperator (normally a dot)
            path = self._name_to_path(namespace_id)
            #- fully qualified NSID or not?
            if self._nsroot and path[0] == self._nsroot._nsid:
                #- lookup fully qualified NSIDs using the root node
                next_nsid = '.'.join(path[1:])
                return self._nsroot.lookup(next_nsid, follow_symrefs=follow_symrefs)
            else:
                #- lookup relative NSIDs iteratively from current
                obj = self
                for name in path:
                    try:
                        obj = getattr(obj, name)

                        if follow_symrefs and is_nsid_ref(obj):
                            return self._lookup_symbolic_ref(obj)

                    except AttributeError as err:
                        log.error('thewired Failed to find value for [{}] in [{}]'.format(
                                namespace_id,
                                self._nsid))
                        raise NamespaceLookupError("{}.{}".format(self._nsid, namespace_id)) from err

            return obj



    def _lookup_symbolic_ref(self, ref, follow_symrefs=True):
        """
        Description:
            lookup a value in starting from NSROOT, instead of a value in this namespace
            node. (if nsroot is not set, we lookup from this node.)
        Input:
            ref: the symbolic reference to lookup
            follow: whether to follow links that lead to links or not
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamspaceNode._lookup_symbolic_ref'})
        if self._nsroot is None:
            nsroot = self

        else:
            nsroot = self._nsroot

        log.debug("nsid ref: {}".format(ref))
        #- strip the prefix
        nsid = get_nsid_from_ref(ref)
        ref = nsroot._lookup(nsid)

        if follow_symrefs:
            while is_nsid_ref(ref):
                log.debug("nsid ref: {}".format(ref))
                nsid = get_nsid_from_ref(ref)
                ref = nsroot._lookup(nsid)
            #- ref no longer an nsid ref
            
        return ref



    def _add_ns(self, ns_node, iter=True, overwrite=True):
        """
        Description:
            convenience method for adding namespace nodes rooted at this namespace node
        Input:
            ns_node: namespace node to add
            iter: add this to ns_items dict
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._add_ns'})
        log.debug("'{}' adding sub ns: {}".format(self._nsid, ns_node))

        try:
            nsid = ns_node._nsid
        except AttributeError as err:
            log.error("add_ns called on object without 'nsid' attribute:{}".format(\
                ns_node))
            raise 

        nsid_path = nsid.split('.')
        for n, nsid_x in enumerate(nsid_path):
            try:
                #- must match a prefix
                if nsid_x != self._nsid.split('.')[n]:
                    break
            except IndexError:
                break
        else:
            raise ValueError("must have a sub-NSID to add namespacenode")

        #- found an nsid component in nsid_x (at index n) that begins the sub_nsid
        log.debug("found sub_nsid start: {}/{}".format(nsid_path[n], nsid_path))
        sub_nsid = '.'.join(nsid_path[n:])
        return self._add_item(sub_nsid, ns_node, iter=iter, overwrite=overwrite)



    def _set_item(self, namespace_id, value, iter=False, overwrite=True):
        """
        Description:
            Wrapper to add_item, with overwrite defaulting to True and iter defaulting to
            False
        """
        self._add_item(namespace_id, value, iter=iter, overwrite=overwrite)



    def _add_item(self, namespace_id, value, iter=True, overwrite=False):
        """
        Description:
            create new/set existing item in the namespace to a new value
            this will not overwrite existing values, unless overwrite is True

        Input:
            namespace_id: the name of the new / existing object to set
            value: what to set the new item to
            iter: whether or not to add this to our sequence of iterables for this node
            overwrite: whether or not to overrwrite an existing value

        Output:
            Nothing; pure side effect of setting the value
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._add_item'})

        ns_path = self._name_to_path(namespace_id)
        log.debug(f'ns_path: {ns_path}')
        if len(ns_path) == 1:
            #- set this on self
            try:
                val = getattr(self, ns_path[0])
                attr_exists = True
            except AttributeError:
                attr_exists = False

            if overwrite or not attr_exists:
                if not attr_exists:
                    log.debug('{} adding item: {}: {}'.format(self._nsid,\
                        namespace_id, value))
                else:
                    log.debug('{} overwriting item: {}: {}'.format(self._nsid,\
                        namespace_id, value))

                setattr(self, ns_path[0], value)
                if iter:
                    #- TODO: these should be automatically sync'd, not manually
                    self._ns_items[ns_path[0]] = value
                return

            else:
                msg = '[{}] Not overwriting existing item: {}'.format(self._nsid, ns_path[0])
                log.info(msg)
                log.debug("overwrite: {}".format(overwrite))
                return

        else:
            #- ask the next node to set this
            try:
                next_node = getattr(self, ns_path[0])
            except AttributeError:
                #- TODO: make a flag to add children or not
                next_node = self._add_child(ns_path[0])

            #- TODO: support other classes that don't have add_item with setattr?
            new_nsid = '.'.join(ns_path[1:])
            next_node._add_item(new_nsid, value, iter=iter, overwrite=overwrite)
            return



    def _all(self, nsids=False):
        """
        Description:
            get all the nsitems that were added with add_item(iter=True)
        Input:
            nsids: if True, return the tuple of nsid and value, else return only the
                values
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._all'})
        all = list()
        if nsids:
            for name,value in self._ns_items.items():
                nsid = '.'.join([self._nsid, name])
                all.append((nsid, value))
        else:
            for value in self._ns_items.values():
                all.append(value)

        return all



    def _shallowiterator(self):
        """
        Description:
            shallow iteration over all items in _ns_items
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._shallowiterator'})
        log.debug("Shallow iterator invoked on {}".format(self._nsid))
        return iter(self._all(nsids=False))


    def __iter__(self):
        """
        Description:
            default iteration is an unfiltered shallow iteration
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode.__iter__'})
        log.debug("Default iterator invoked on {}".format(self._nsid))
        return self._shallowiterator()


    def _list_leaves(self, nsids=False, cur_nsid=None):
        """
        Description:
            return a list of all the leaf nodes
        Input:
            nsids:
                - True: return a list of pairs of (nsid, leaf_node)
                - False: return a list of leaf_node's
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._list_leaves'})
        log.debug("invoked on: {} | cur_nsid: {} ".format(self._nsid, cur_nsid))
        leaves = list()

        for nsid, ns_item in self._all(nsids=True):
            try:
                #- if an object has this method, we don't consider it a leaf itself
                next_leaves = ns_item._list_leaves(nsids=nsids, cur_nsid=nsid)
                log.debug("extending with {}".format(next_leaves))
                leaves += next_leaves

            except (TypeError, AttributeError):
                log.debug("leaf found: {}".format(ns_item))
                if nsids:
                    leaf = (nsid, ns_item)
                else:
                    leaf = ns_item
                leaves.append(leaf)

        log.debug("generated leaves: {}".format(leaves))
        return leaves


    @property
    def _nsroot(self):
        return self.__nsroot



    @_nsroot.setter
    def _nsroot(self, root):
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceNode._nsroot setter'})
        self.__nsroot = root
        for item in self._ns_items.values():
            #- only set nsroot on NamespaceNode-like objects
            try:
                #- nsroot only used for symbolic ref lookups
                method = item._lookup_symbolic_ref
            except AttributeError:
                #- if you don't support symbolic ref lookup, you don't get an nsroot
                #- just need something to check w/out an explicit type check
                continue
            try:
                item._nsroot = root
                log.debug("set nsroot for child: {}".format(item))
            except AttributeError:
                log.debug("failed setting nsroot for child: {}".format(item))




class NamespaceNodeDelegator(object):
    """
    Description:
        Simple Delegation to an underlying NamespaceNode.
        Idea behind this class is that everything that goes into a namespace should
        support basic NamespaceNode functionality, but some nodes (notably the leaves),
        are storing other datastructutures within themselves. This class is being written
        to pivot the namespace away from having raw entries of other datastructures into
        having a namespace where the semantics are a little more well-defined throughout.
    """

    _undelegated = ['primary', 'delegate_nsid', 'nsroot', 'delegate', '__dict__']
    def __init__(self, primary, delegate_nsid, nsroot):
        """
        Input:
            primary_obj: the primary object. (the one we want to stick into the namespace)
            delegate_nsid: namespacenode NSID to delegate NamespaceNode operations to
            nsroot: namespace root to look up delegate inside of
        """
        self.primary = primary 
        self.delegate_nsid = delegate_nsid
        self.nsroot = nsroot

    def __getattr__(self, attr):
        print(f'self.__dict__.keys(): {list(self.__dict__.keys())}')
        print(f'NamespaceNodeDelegator.__getattr__:self.{attr}')
        if attr not in self._undelegated:
            print(f'{attr} not in {self._undelegated}')
            try:
                return getattr(self.primary, attr)
            except AttributeError:
                pass
            try:
                return getattr(self.delegate, attr)
            except AttributeError:
                raise 
        else:
            return super().__getattr__(attr)


    def __setattr__(self, attr, value):
        print(f'self.__dict__.keys(): {list(self.__dict__.keys())}')
        print(f'NamespaceNodeDelegator.__setattr__:self.{attr}')
        if attr not in self._undelegated:
            print(f'{attr} not in {self._undelegated}')
            return setattr(self.primary, attr, value)
        else:
            return super().__setattr__(attr, value)


    @property
    def delegate(self):
        """
        Description:
            property to get the delegate namespacenode
        """
        return self.nsroot._lookup(self.delegate_nsid)
