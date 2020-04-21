import collections
import typing

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Dict
from .namespace import NamespaceNode
from .exceptions import NamespaceLookupError, NamespaceConfigParsingError
from functools import partial

from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)


class NamespaceConfigParser(object):
    """
    Description:
        Base Parsing class for old-style Namespace Configurations wihtout a top-level
        Namespace abstraction. This is for collections of Nodes, like the original
        Namespacenode type that is a one-stop-shop for namespace building, but itself has
        little control over what ends up in the Namespace

        Makes every key in the dictionary into a NamespaceNode, except for the final keys that
        map directly to items. (Sets those items directly.)

        In other words, if the key in a dictConfig is another dictionary, we add a
        NamespaceNode for that key and then recurse.
        Base Case is if the key in the current dictConfig is NOT another dictionary, but an
        immediate value, in which case this class will then set that value on the last created
        node directly.

        To use a dict as an immediate value, put it under a YAML key named '__raw__'.

        There are a few different styles of dictionary configurations, and each one of those
        subclasses this class and overrides the "parse_submap()" method to get specific
        semantics for the sub-keys in a dictionary configuration.

        You could equally override the top-level "parse()" method, but, in practice, this
        often leads to duplicating its functionality just because of the current format of
        the configs usually has a top-level of keys that are really just to namespace the
        rest of the configuration. If there is a top-level that is an immediate object to
        be parsed, then override "parse()" as well.
    """

    def __init__(self, nsroot=None, node_factory=NamespaceNode, prefix=None):
        """
        Input:
            node_factory: callable to create the node objects
            prefix: optional prefix for the generated NSIDs
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceConfigParser.__init__'})
        self.nsroot = nsroot
        self.prefix = prefix

        #-XXX node_factory must take nsroot param
        self.new_node = partial(node_factory, nsroot=self.nsroot)
        #- marks things in the config to leave as a dict
        self._raw_marker = '__raw__'
        #- default final NSID value for things left as a dict
        self._raw_id = 'raw'



    def parse(self, dictConfig=None):
        '''
        Input:
            dictConfig: the dictConfig that initializes the namespace
        '''
        self._ns_roots = list()

        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceConfigParser.parse'})
        log.debug("Beginning dictConfig parsing...")
        ns_collection = list()
        for key in dictConfig.keys():
            if self.prefix:
                nsid = '.'.join([self.prefix, key])
            else:
                nsid = key
            log.debug('creating new Namespace Root: {}'.format(nsid))
            cur_ns = self.new_node(nsid)
            log.debug('appending {} to ns_collection'.format(cur_ns))
            ns_collection.append(cur_ns)
            log.debug('Calling _parse_dictConfig_sub')
            self.parse_submap(dictConfig[key], cur_ns)

        log.debug('returning {}'.format(ns_collection))
        return ns_collection


    def parse_submap(self, dictConfig, cur_ns, prev_ns=None):
        """
        Description:
            generic dictConfig sub parser. Essentially makes every key into a
            NamespaceNode and then looks at its sub-keys, if each subkey is another
            dictConfig object, it will recurse. At the last level, where the subkeys map to
            an immediate value, the immediate value is used as the value assigned and no
            recursion is performed.

        Input:
            dictConfig: current config root
            cur_ns: current namespace root
            prev_ns: previous namespace root - used for raw overwriting

        Output:
            None; directly adds nodes to cur_ns

        Notes:
            This method can be overridden in subclasses to allow for different styles of
            dictonary configuration, if they all share the property of a set of root-level
            keys that we want to parse into a collection of namespaces.

            See SdkNamespace class for an example of overriding this method.
        """
            
        log = LoggerAdapter(logger, {'name_ext' : 'NamespaceConfigParser.parse_submap'})
        log.debug('Entering with cur_ns: {}'.format(cur_ns))

        if cur_ns is None:
            log.error('Error parsing config: current namespace node is None.')
            raise ValueError('None is not a valid namespace object')

        log.debug('Iterating over keys: {}'.format(list(dictConfig.keys())))
        for key in dictConfig.keys():
            log.debug('----[cur_ns: {} | current key: {}'.format(cur_ns, key))

            if key == self._raw_marker:
                raw_dict = dict(dictConfig[key])
                if prev_ns:
                   prev_ns._add_item(cur_ns._name, raw_dict, overwrite=True)
                else:
                    msg = "Can't set raw item wihout parent node"
                    raise NamespaceConfigParsingError(msg)

            elif isinstance(dictConfig[key], Mapping):
                log.debug('dictConfig[{}] is another dictConfig'.format(key))

                #- recursive case
                next_ns = cur_ns._add_child(key)
                msg = 'recursing to parse dict config for key: [{}]'.format(key)
                log.debug(msg)
                self.parse_submap(dictConfig[key], cur_ns=next_ns, prev_ns=cur_ns)

            else:
                #- leave it as a bare node
                msg = 'Setting immediate value for node {}.[{}]'.format(cur_ns._nsid, key)
                log.debug(msg)
                log.debug('    {}'.format(dictConfig[key]))
                cur_ns._add_item(key, dictConfig[key])

        log.debug('exiting: cur_ns: {}'.format(cur_ns))

