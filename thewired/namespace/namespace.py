"""
Purpose:
    provide a single API for all user code interacting with NamespaceNodes

Notes:
    namespaces are made up of namespacenodes
    they have a root node and other properties which are all encoded here

"""

from logging import getLogger, LoggerAdapter
from types import SimpleNamespace
from typing import Union, List
from warnings import warn

from thewired.loginfo import make_log_adapter
from .namespacenode import NamespaceNodeBase
from thewired.namespace.nsid import Nsid, list_nsid_segments, get_parent_nsid, validate_nsid, get_nsid_ancestry
from thewired.namespace.nsid import strip_common_prefix, find_common_prefix, make_child_nsid
from thewired.namespace.nsid import nsid_basename
from thewired.exceptions import NamespaceLookupError, NamespaceCollisionError, InvalidNsidError
from thewired.exceptions import NamespaceInternalError

logger = getLogger(__name__)

class Namespace(SimpleNamespace):
    """
    Description:
        top-level class for everything dealing with namespaces, including operations that
        handle namespacenodes' inter-relations to each other
    """
    #-class level attribute for the default root node NSID
    delineator = '.'
    _root_nsid = '.'

    def __init__(self, default_node_factory=NamespaceNodeBase):
        """
        Input:
            prefix: what namespace prefix is applied to all nodes in this namespace
            default_node_factory: default factory for creating new Nodes in this namespace
        """
        self.log = LoggerAdapter(logger,
            {'name_ext' : f'{self.__class__.__name__}.__init__'})

        self._validate_default_node_factory(default_node_factory)
        self.default_node_factory = default_node_factory

        self.root = self.default_node_factory(nsid=self._root_nsid, namespace=self)



    def __getattr__(self, attr):
        """
        Description:
            to make it look like everything that's actually under the namespacenode .root is
            actually directly part of the namespace object
        """
        return getattr(self.root, attr)


    def _validate_default_node_factory(self, func):
        if not callable(func):
            raise ValueError(f"default_node_facotry must be callable!")

        try:
            x = func(nsid=".a.b.c", namespace=None)
        except TypeError as err:
            raise ValueError("default_node_factory either does not take 'nsid' and 'namespace' keyword parameters, or has additional required parameters!")



    def _validate_namespace_nsid_head(self, nsid: Union[str, Nsid]) -> bool:
        """
        Descripton: make sure that the nsid is fully qualified  (starts with the ns separator char)
        """
        if find_common_prefix(str(self.root.nsid), nsid) is None:
            err_msg = f'nsid ({nsid}) must share a common prefix with Namespace root node nsid'
            err_msg += f'({str(self.root.nsid)})'
            raise InvalidNsidError(err_msg)



    def get(self, nsid : Union[str, Nsid]) -> NamespaceNodeBase:
        """
        Description:
            return a node object specified by NSID
        """
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.get"))
        self._validate_namespace_nsid_head(nsid)
        _nsid_ = Nsid(nsid)
        current_node = self.root
        nsid_segments = list_nsid_segments(nsid)[1:] #- skip initial root segment

        n = 0
        while current_node.nsid != _nsid_:
            log.debug(f"{_nsid_=} != {current_node.nsid=}")
            try:
                nsid_segment = nsid_segments[n]
            except IndexError as err:
                raise NamespaceInternalError(f"while looking for nsid \"{_nsid_}\", ran out of nsid_segments: {nsid_segments} at index {n}") from err
            try:
                current_node = getattr(current_node, nsid_segment)
                if not isinstance(current_node, NamespaceNodeBase):
                    warn("Rogue node type detected in the namespace. Will most likely cause errors.")
            except AttributeError:
                raise NamespaceLookupError(f"{current_node} has no attribute named '{nsid_segment}'")
            n += 1
        return current_node



    def add(self, nsid : Union[str, Nsid], node_factory:Union[callable, None]=None, *args, **kwargs) -> List[NamespaceNodeBase]:
        """
            Description:
                add a new nsid to this namespace
            Input:
                nsid: the nsid to create in this namespace
                node_factory: what factory to use to create the node
                    NOTE: parent nodes will be created with this namespaces default_node_factory method
                *args: passed into the node_factory as args
                **kwargs: passed into the node_factory as kwargs
        """
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.add"))
        if find_common_prefix(str(self.root.nsid), nsid) is None:
            err_msg = f'child nsid ({nsid}) must share a common prefix with Namespace root node nsid'
            err_msg += f'({str(self.root.nsid)})'
            raise InvalidNsidError(err_msg)
        _nsid = Nsid(nsid)

        if node_factory is None:
            node_factory = self.default_node_factory

        #- find the deepest existing ancestor of the node we wish to add
        deepest_ancestor = self.root
        for current_nsid in get_nsid_ancestry(nsid):
            try:
                deepest_ancestor = self.get(current_nsid)
            except NamespaceLookupError:
                break
        else:
            #- we never hit break, so every single nsid in the entire ancestry exists, including the one we want to add
            raise NamespaceCollisionError(f'A node with the nsid "{nsid}" already exists in the namespace.')

        #- if here, we have a valid deepest ancestor to start from
        child_nsid_tail = strip_common_prefix(str(deepest_ancestor.nsid), str(_nsid))[1]
        common_prefix = find_common_prefix(str(deepest_ancestor.nsid), str(_nsid))
        created_nodes = list()      #- keep track of all the nodes we create to return them
        nsid_segments = list_nsid_segments(child_nsid_tail)
        for i,child_attribute_name in enumerate(nsid_segments):
            new_node_nsid = make_child_nsid(str(deepest_ancestor.nsid), child_attribute_name)
            #- use the node factory on the last node only
            if i == len(nsid_segments) - 1:
                log.debug(f"creating node: {node_factory=})")

                #TODO fix this to require the factory function to be callable w/out args
                #force folks to pass in a partial if necessary
                # for now just plow on through I guess
                try:
                    new_node = node_factory(new_node_nsid, self, *args, **kwargs)
                except TypeError:
                    try:
                        new_node = node_factory(new_node_nsid, self)
                    except TypeError:
                            new_node = node_factory()
            else:
                new_node = self.default_node_factory(new_node_nsid, self)
            created_nodes.append(new_node)
            setattr(deepest_ancestor, child_attribute_name, new_node)
            deepest_ancestor = getattr(deepest_ancestor, child_attribute_name)

        return created_nodes



    def add_exactly_one(
        self,
        nsid : Union[str, Nsid],
        node_factory=NamespaceNodeBase,
        *args,
        **kwargs):
        """
            Description:
                add one and only one new node to this namespace and return the new node
            Input:
                nsid: nsid of new node to create
                node_factory: factory method to call to create the node
                *args, **kwargs: passed through to node_factory
            Output:
                exactly one new node created or raises an exception if:
                    - it looks like it will create more than one node: NamespaceLookupError
                    or
                    - if it didn't look like it but somehow it did: NamespaceInternalError
        """
        nsid_segments = list_nsid_segments(nsid, skip_root=True)
        if len(nsid_segments) > 1:
            try:
                #- if the parent exists, this will add only one
                self.get(get_parent_nsid(nsid))
            except NamespaceLookupError:
                err_msg = f"add_exactly_one: error: input \"{nsid}\" would create more" +\
                          f" than one new node. ({len(nsid_segments)} > 1)"
                raise ValueError(err_msg)

        new_nodes = self.add(nsid, node_factory, *args, **kwargs)

        if len(new_nodes) > 1:
            raise NamespaceInternalError(f"created more than one new node! ({new_nodes})")

        return new_nodes[0]


    def remove(self, nsid: Union[str, Nsid]) -> NamespaceNodeBase:
        """
        Description:
            remove a node and all of its children from the namespace
        Input:
            nsid: the nsid of the node to remove

        Note: it is an error to remove a node that doesn't exist
        """
        parent_nsid = get_parent_nsid(nsid)
        parent = self.get(parent_nsid)

        child_short_nsid = strip_common_prefix(str(parent.nsid), nsid)[1]
        node = getattr(parent, child_short_nsid)
        delattr(parent, child_short_nsid)
        return node


    def walk(self, start:Union[NamespaceNodeBase,None]=None, walk_dict:Union[dict,None]=None) -> dict:
        """
        Description:
            walk the namespace nodes
        Output:
            Dictionary representing the namespace's structure
        """
        if start is None:
            start = self.root

        if walk_dict is None:
            walk_dict = dict()

        if not isinstance(start, NamespaceNodeBase):
            return dict()

        key = nsid_basename(start.nsid.nsid)
        walk_dict[key] = dict()

        for attr_name in dir(start):
            if not attr_name.startswith('_'):
                updated_walk = self.walk(start=getattr(start, attr_name),
                                    walk_dict=walk_dict[key])
        return walk_dict


    def get_handle(self, handle_key:Union[Nsid,str], create_nodes:bool=False) -> 'NamespaceHandle':
        """
        Description:
            get a "handle" on a subnamespace. That is, return an object that can be used as a namespace object
            that always operates on the subnamespace given in the handle_key.

        Input:
            handle_key: string/Nsid object representing where the handle's root is
            create_nodes: if the handle key does not exist, should we first add the key and succeed?
                if the key doesn't exist, this will fail with a NamespaceLookupError
        Output:
            a NamespaceHandle object
        """
        try:
            self.get(handle_key)
        except NamespaceLookupError as err:
            if create_nodes:
                self.add(handle_key)
            else:
                raise 
        return NamespaceHandle(self, handle_key)




class NamespaceHandle(Namespace):
    """
    Description:
        basically if I get a handle from an existing namespace object, it should act exactly like a Namespace object,
        only all of the NSIDs are interpreted relative to the handle's prefix as the root
    """
    def __init__(self, ns : Namespace, prefix: Union[str, Nsid]):
        self.ns = ns
        self.prefix = prefix
        self.root = ns.get(prefix)


    def __getattr__(self, attr):
        saved_root = self.ns.root
        self.ns.root = self.root

        retval = getattr(self.ns, attr)
        self.ns.root = saved_root
        return retval


    def get(self, nsid:Union[str,Nsid]) -> NamespaceNodeBase:
        if nsid == self.delineator:
            real_nsid = self.prefix
        else:
            real_nsid = self.prefix + nsid
        return self.ns.get(real_nsid)


    def add(self, nsid:Union[str,Nsid], *args, **kwargs) -> List[NamespaceNodeBase]:
        real_nsid = self.prefix + nsid
        return self.ns.add(real_nsid, *args, **kwargs)


    def remove(self, nsid:Union[str,Nsid]) -> NamespaceNodeBase:
        real_nsid = self.prefix + nsid
        return self.ns.remove(real_nsid)
