from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)



import collections
from .providerabc import Provider, ProviderError
from thewired.exceptions import NamespaceLookupError, ProviderMapLookupError


FAIL_CANARY = '_provider_map_lookup_canary_fail_return_value_'

class ProviderMap(collections.UserDict):
    '''
    Description:
        This object is simply a map from one namespace key to another namespace key.
        The initial namespace key is usually the namespace ID of a User Interfacing Node
        object and it will usually map this node's namespace id + an attribute name to a
        name that is then looked up in the provider namespace.
    '''
    def __init__(self, mapping=None, provider_ns=None, fail_to_parent=False, fail_up_height=0):
        '''
        Input:
            mapping: the mapping object to use for lookups

            fail_to_parent: if True, in the case that the lookup for the specifically
                given id fails, we will return the parent's provider if the parent is within
                <fail_up_height> distance from the requested node.

            fail_up_height: if fail_to_parent is True, this determines the maximum
                distance that the parent can be from the child in order for the Fail Up to
                succeed. Set to math.inf to set to infinite.
        '''
        log_name_ext = {'name_ext' : '{}.__init__'.format(self.__class__.__name__)}
        log = LoggerAdapter(logger, log_name_ext)

        super().__init__()
        self._provider_ns = provider_ns
        self.fail_to_parent = fail_to_parent
        self.fail_up_height = fail_up_height

        #- Check ProviderMap initial mapping for valid Provider objects
        if mapping:
            if isinstance(mapping, collections.Mapping):
                if len(mapping.values()) > 0:
                    log.debug("Checking ProviderMap initial mapping for valid Provider objects")
                    for provider in mapping.values():
                        #- TODO: Duckify by catching this when providers are used, not
                        #-       instantiated
                        if provider is not None and not isinstance(Provider):
                            log.error('Invalid provider: {}'.format(str(p)))
                            msg = 'NamespaceNode providers must be an instance of Provider None, not {}'.format(p)
                            raise ValueError(msg)

                    providers = list(mapping.keys())
                    log.debug("Setting providers for the attributes: {}".format(providers))
                    self.data = mapping
            else:
                msg = "Non collections.Mapping type passed for ProviderMap mapping"
                raise ValueError(msg)

        else:
            self.data = dict()




    def cascading__getitem__(self, item_key):
        '''
        Description:
            place holder for implementing cascading fail up for providers to fail over to
            the providers earlier in the provider namespace
        '''
        current = self.data
        current_provider = None
        key_path = item_key.split('.')

        for n, key in enumerate(key_path):
            try:
                current = current[key]
                current_provider = current.provider

            except KeyError as err:
                if self.fail_to_parent:
                    log_level = logging.DEBUG
                    fail_height = len(key_path) - n
                    if fail_height > self.fail_up_height:
                        current_provider = None
                else:
                    log_level = logging.WARNING
                    current_provider = None

                log.log(log_level, 'No provider found for {}'.format(item_key))
                log.debug('Last provider found in lookup: {}'.format(key_path[n-1]))
                break

        return current_provider


    def set_provider(self, key, provider):
        log = LoggerAdapter(logger, {'name_ext' : 'ProviderMap.set_provider'})
        if isinstance(provider, str):
            log.debug("setting provider by NSID")
            nsid = provider
            self.data[key] = nsid
            try:
                provider_instance = self._provider_ns._lookup(nsid)
            except NamespaceLookupError:
                msg = 'No such provider [{}] in provider namespace'.format(nsid)
                log.warn(msg)

        elif isinstance(provider, Provider):
            log.debug("setting provider by direct reference")
            self.data[key] = provider

        else:
            msg = '{} is not a valid Provider instance or subclass'.format(provider)
            raise ProviderError(msg)



    def get_provider(self, key):
        log = LoggerAdapter(logger, {'name_ext': 'ProviderMap.get_provider'})
        try:
            provider_ = self.data[key]
            if isinstance(provider_, Provider):
                return provider_

            elif isinstance(provider_, str):
                return self._provider_ns._lookup(provider_)

        except (KeyError, NamespaceLookupError):
            raise ProviderError('No provider for {}'.format(key))


    def set_provider_namespace(self, provider_ns):
        log = LoggerAdapter(logger, {'name_ext' : 'ProviderMap.set_provider_namespace'})
        log.debug("setting provider namespace")
        self._provider_ns = provider_ns



    def __getitem__(self, key):
        log = LoggerAdapter(logger, {'name_ext' : 'ProviderMap.__getitem__'})
        val = self.data.get(key, FAIL_CANARY)
        log.debug('data.get({}) returned: {}'.format(key, val))
        if val == FAIL_CANARY:
            raise ProviderMapLookupError('No provider for {}'.format(key))
        else:
            return val


    def __str__(self):
        s = "{}( keys=[".format(self.__class__.__name__)
        for key in self.data.keys():
            s += '{}, '.format(key)
        s += '])'
        return s


    def __repr__(self):
        return self.__str__()

