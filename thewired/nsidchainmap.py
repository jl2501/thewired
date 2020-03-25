from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

from collections import ChainMap
from thewired.exceptions import NamespaceLookupError


class NsidChainMap(dict):
    """
    Description:
        ChainMap-inspired type that stores references to the dicts that make up the
        sequence symbolically as NSIDs that are looked up at run-time dynamically.
        
        This type deviates from the ChainMap semantics as follows:
            * all references to other maps are done via NSID
            * there is a NamespaceNode that is passed in as a mandatory nsroot parameter
                - all maps are lookedup via nsroot._lookup(<nsid>)
            * we store a local dictionary that is used as the mapping to perform all
              updates on
            * new_child overwrites the local dict with a blank one
            * parents gets is equivalent to getting the maps attribute directly
    """
    def __init__(self, nsroot, *map_nsids, local=None):
        """
        Input:
            nsroot: root of namespace to lookup NSIDs in
            local: dict to use for the root dictionary
            *map_nsids: variable length arguments of NSIDs
        """
        self.nsroot = nsroot
        
        self.data = local if local else dict()
        self.map_nsids = map_nsids if map_nsids else list()
        self._LOOKUP_FAIL_CANARY = '___nsidchainmap_lookup_failure_canary___'



    def __missing__(self, key):
        """
        Description:
            Support DefaultDict and others that call this method when a key is missing
            instead of directly raising ValueError
        """
        raise KeyError(key)



    def __getitem__(self, key):
        """
        Description:
            Go through self and the sequence of maps to find the first match for the given
            key

        Input:
            key: key for the item to get
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NsidChainMap.__getitem__'})
        value = self._LOOKUP_FAIL_CANARY
        try:
            value = self.data[key]
            return value
        except KeyError:
            log.debug("{} not found in local dict".format(key))
            for m_nsid in self.map_nsids:
                try:
                    map = self.nsroot._lookup(m_nsid)
                except NamespaceLookupError:
                    log.warning('Unable to lookup map: {}'.format(m_nsid))

                try:
                    value = map[key]
                    break
                except KeyError:
                    log.debug('KeyError in {}. Trying next...'.format(m_nsid))
                    continue

            if value == self._LOOKUP_FAIL_CANARY:
                self.__missing__(key)
            else:
                return value



    def __setitem__(self, key, value):
        """
        Description:
            set local dict [key] = value

        Input:
            key: key name
            value: value to set for key
        """
        log = LoggerAdapter(logger, {'name_ext' : 'NsidChainMap.__setitem__'})
        log.debug("setting local dict {} to {}".format(key, value))
        self.data[key] = value




    def __delitem__(self, key):
        """
        Description:
            delete key from local dict instance
        """
        del(self.data[key])



