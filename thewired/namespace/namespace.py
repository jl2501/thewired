"""
Purpose:
    provide a single API for all user code interacting with NamespaceNodes

Notes:
    namespaces are made up of namespacenodes
    they have a root node and other properties which are all encoded here

"""

from logging import getLogger, LoggerAdapter
from types import SimpleNamespace
from typing import Union, List, Dict
from warnings import warn

from thewired.loginfo import make_log_adapter
from .namespacenode import NamespaceNodeBase, HandleNode
from thewired.namespace.nsid import Nsid, list_nsid_segments, get_parent_nsid, validate_nsid, get_nsid_ancestry, \
                                    strip_common_prefix, find_common_prefix, make_child_nsid, \
                                    nsid_basename, get_nsid_from_ref, is_valid_nsid_ref, get_nsid_from_link, \
                                    is_valid_nsid_link
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
            x = func(nsid=".a.b.c", namespace=self)
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
        if is_valid_nsid_ref(nsid):
            log.debug(f'dreferencing NSID ref: {nsid=}')
            nsid = get_nsid_from_ref(str(nsid))
        elif is_valid_nsid_link(nsid):
            log.debug(f'getting node from NSID symlink')
            nsid = get_nsid_from_link(nsid)
        else:
            log.debug(f'no nsid-ref nor nsid symlink found')
        self._validate_namespace_nsid_head(nsid)
        _nsid_ = Nsid(nsid)
        current_node = self.root
        nsid_segments = list_nsid_segments(nsid)[1:] #- attribute names to get; skip initial empty string ""

        n = 0
        while current_node.nsid != _nsid_:
            #log.debug(f"target {_nsid_=} != {current_node.nsid=}")
            try:
                nsid_segment = nsid_segments[n]
            except IndexError as err:
                raise NamespaceInternalError(f"while looking for nsid \"{_nsid_}\", ran out of nsid_segments: {nsid_segments} at index {n} ({current_node=}") from err
            try:
                current_node = getattr(current_node, nsid_segment)
                if not isinstance(current_node, NamespaceNodeBase):
                    warn("Rogue node type detected in the namespace. Will most likely cause errors.")
            except AttributeError as e:
                raise NamespaceLookupError(f"{current_node} has no attribute named '{nsid_segment}'") from e
            n += 1

        log.debug(f"Exiting: {nsid=} | Returning this node: {current_node=}")
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
        log.debug(f"Entering: {nsid=} | {node_factory=}")
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
            log.debug(f"creating node: {self=} | {new_node_nsid=}")
            if i == len(nsid_segments) - 1:
                try:
                    log.debug(f"creating node w/ non-default factory: {node_factory=}")
                    new_node = node_factory(*args, nsid=new_node_nsid, namespace=self, **kwargs)
                except TypeError as e:
                    raise TypeError(f"node_factory failed to create node: {str(e)}") from e

            else:
                log.debug(f"creating node with default factory")
                new_node = self.default_node_factory(nsid=new_node_nsid, namespace=self)

            created_nodes.append(new_node)
            log.debug(f"adding new node to the namespace: {deepest_ancestor=} | {child_attribute_name=} | {new_node=}")
            setattr(deepest_ancestor, child_attribute_name, new_node)
            deepest_ancestor = getattr(deepest_ancestor, child_attribute_name)
            log.debug(f"got next ancestor: {deepest_ancestor=}")

        log.debug(f"Exiting. {created_nodes=}")
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
        log = LoggerAdapter(logger, dict(name_ext="namespace.add_exactly_one"))
        log.debug(f"Entering: {nsid=} {node_factory=}")
        nsid_segments = list_nsid_segments(nsid, skip_root=True)
        if len(nsid_segments) > 1:
            try:
                #- if the parent exists, this will add only one
                log.debug(f"checking if parent exists: {get_parent_nsid(nsid)}")
                self.get(get_parent_nsid(nsid))
                log.debug(f"parent exists for {nsid=}")
            except NamespaceLookupError as e:
                err_msg = f"add_exactly_one: error: input \"{nsid}\" would create more" +\
                          f" than one new node. ({len(nsid_segments)} > 1) {self.root=}"
                raise ValueError(err_msg) from e

        new_nodes = self.add(nsid, node_factory, *args, **kwargs)

        if len(new_nodes) > 1:
            raise NamespaceInternalError(f"created more than one new node! ({new_nodes})")

        log.debug(f"Exiting. {new_nodes=}")
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


    def walk(self, start:Union[NamespaceNodeBase,None]=None, walk_dict:Union[Dict,None]=None) -> Union[Dict, object]:
        """
        Description:
            walk the namespace nodes
        Output:
            Dictionary representing the namespace's structure
        """
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.walk"))

        if start is None:
            start = self.root

        if walk_dict is None:
            walk_dict = dict()

        if not isinstance(start, NamespaceNodeBase):
            return start

        key = nsid_basename(start.nsid.nsid)
        walk_dict[key] = dict()


        for attr_name in dir(start):
            if not attr_name.startswith('_') and not attr_name == "nsid":
                attr = getattr(start, attr_name)
                updated_dict = self.walk(start=attr, walk_dict=walk_dict[key])

                if not isinstance(updated_dict, dict):
                    walk_dict[key][attr_name] = attr
                else:
                    walk_dict[key].update(updated_dict)

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

    def get_subnodes(self, start_node_nsid):
        """
        Description:
        return a generator for all the nodes that are descendants of the node at the given NSID <start_node_nsid>
        Input:
        start_node_nsid: what NSID to consider the root
        Output:
        all the nodes that are descendants of the node with NSID given as start_node_nsid
        """
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.get_subnodes"))
        start_node = self.get(start_node_nsid)
        for attr_name in dir(start_node):
            attr = getattr(start_node, attr_name)
            if isinstance(attr, NamespaceNodeBase):
                log.debug(f"yielding {attr=}")
                yield attr
                yield from self.get_subnodes(str(attr.nsid))

    def get_leaf_nodes(self, start_node_nsid):
        """
        return the nodes that are leaves
        (its a leaf if none of the attributes link to other NamespaceNodes)
        """
        log = make_log_adapter(logger, self.__class__, "get_leaf_nodes")
        start_node = self.get(start_node_nsid)
        is_leaf = True
        for attr_name in dir(start_node):
            attr = getattr(start_node, attr_name)
            if isinstance(attr, NamespaceNodeBase):
                is_leaf = False
                yield from self.get_leaf_nodes(str(attr.nsid))
        if is_leaf:
            yield start_node

    def __repr__(self):
        return f"Namespace(root={self.root})"




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
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.get: {self.prefix=}"))
        if nsid == self.delineator:
            real_nsid = self.prefix
        elif is_valid_nsid_ref(nsid):
            real_nsid = self.prefix + get_nsid_from_ref(nsid)
        elif is_valid_nsid_link(nsid):
            real_nsid = self.prefix + get_nsid_from_link(nsid)
        else:
            real_nsid = self.prefix + nsid

        log.debug(f"getting {real_nsid=}")
        return HandleNode(self.ns.get(real_nsid), ns_handle=self)


    def add(self, nsid:Union[str,Nsid], *args, **kwargs) -> List[NamespaceNodeBase]:
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.add: {self.prefix=}"))
        real_nsid = self.prefix + nsid

        log.debug(f"adding {real_nsid=}")
        return self.ns.add(real_nsid, *args, **kwargs)


    def remove(self, nsid:Union[str,Nsid]) -> NamespaceNodeBase:
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.remove: {self.prefix=}"))
        real_nsid = self.prefix + nsid

        log.debug(f"removing: {real_nsid=}")
        return self.ns.remove(real_nsid)


    def get_subnodes(self, start_node_nsid):
        log = LoggerAdapter(logger, dict(name_ext=f"{self.__class__.__name__}.get_subnodes: {self.prefix=}"))
        log.debug(f"{start_node_nsid=}")
        start_node = self.get(start_node_nsid)
        for attr_name in dir(start_node):
            attr = getattr(start_node, attr_name)
            if isinstance(attr, NamespaceNodeBase):
                handle_node = HandleNode(attr, self)
                log.debug(f"yielding {handle_node=}")
                yield handle_node
                next_nsid = '.' + self.strip_prefix(str(attr.nsid))

                log.debug(f"{next_nsid=}")
                yield from self.get_subnodes(next_nsid)

    def get_leaf_nodes(self, start_node_nsid):
        """
        return the nodes that are leaves
        (its a leaf if none of the attributes link to other NamespaceNodes)
        """
        log = make_log_adapter(logger, self.__class__, "get_leaf_nodes")
        start_node = self.get(start_node_nsid)
        is_leaf = True
        for attr_name in dir(start_node):
            attr = getattr(start_node, attr_name)
            if isinstance(attr, NamespaceNodeBase):
                is_leaf = False
                yield from self.get_leaf_nodes(str('.' + self.strip_prefix(attr.nsid)))
        if is_leaf:
            yield HandleNode(start_node, self)

    def strip_prefix(self, nsid:str) -> str:
        try:
            nsid = '.' + self.ns.strip_prefix(nsid)
        except AttributeError:
            #- self.ns is a Namespace, not a stacked NamespaceHandle
            pass

        return strip_common_prefix(self.prefix, nsid)[1]


    def __repr__(self):
        return f"NamespaceHandle(root={self.root}, prefix={self.prefix})"

