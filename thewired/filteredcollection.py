import logging 
from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

import collections.abc
from .exceptions import CollectiveEvalDelegateObjectError

FAIL_CANARY_TYPE = '_FilteredCollection_underlying_object_type_error_canary_'
FAIL_CANARY_ATTRIBUTE = '_FilteredCollection_underlying_object_attribute_error_canary_'
FAIL_CANARY_NAME = '_FilteredCollection_evaluation_name_error_canary_'

class FilteredCollection(collections.abc.Sequence):
    '''
    Description:
        A set of objects and a sequence of filters.
        The filters are applied whenever the collection is to be iterated over.
        This allows a collection to be dynamically filtered based on run time
        properties of the objects.
    '''

    def __init__(self, collection=None, filters=None, collection_factory=list):
        '''
        Description:
            Initialize a FilteredCollection instance with a collection, filters and a
            factory
        Input:
            collection: the underlying collection to be used as the primary unfiltered
                collection
            filters: a sequence of filters to apply by default
            collection_factory: constructor of the returned collection (post filter(s)
                application(s))
        '''
        super().__init__()
        self._collection_factory = collection_factory

        #- the unfiltered list of objects
        if collection:
            self._collection = collection
        else:
            self._collection = self._collection_factory()

        self.all = self._collection

        if filters:
            self.filters = filters
        else:
            self.filters = self._collection_factory()

        self._fail_canaries = [FAIL_CANARY_TYPE, FAIL_CANARY_ATTRIBUTE, FAIL_CANARY_NAME]

    def __getitem__(self, index):
        '''
        Description:
            index into the filtered collection
        Input:
            index: the index to use on the filtered version of the collection
        '''
        return self._filtered_collection[index]



    def append(self, item):
        '''
        Description:
            append an item to the unfiltered primary collection
        Input:
            item: what to append to the unfiltered primary collection
        '''
        self._collection.append(item)



    def __len__(self):
        '''
        Description:
           return length of filtered collection
        '''
        return len(self._filtered_collection)



    @property
    def _filtered_collection(self):
        '''
        Description:
            property to access the collection with the filters applied
            this is a property so it can be accessed as an attribute, but so that it
            always returns the current run-time version of itself
        Output:
            list of the filtered collection
        TODO: cache it; update when filters / elements are updated
        '''
        filtered_collection = self._collection

        #- sequentially apply all of the set filters
        for filter_x in self.filters:
            filtered_collection = filter(filter_x, filtered_collection)

        return list(filtered_collection)



    def collective_eval(self, eval_string, formatter=None):
        '''
        Description:
            this is a more general version of calling a method on each provider object.
            The problem with calling one method, is that often you want to simply use the
            provider collection as a single unit directly and not have to do everything step
            by step.
            basically, this is:
                eval_string: eval('x.{}'.format(eval_string)) for x in self_collection
        Input:
            eval_string: string to pass into eval. Will first be appended to the current
                object, for every object in the filtered collection
            formatter: a callable that will take the returned value from each object in
                the filtered collection's previously described eval and can alter/format this
                return value before returning
        Output:
            results from evaluation in a collection specified by this instances collecton
                factory
        '''

        log = LoggerAdapter(logger, {'name_ext': 'FilteredCollection.collective_eval'})
        log.debug('enter: eval_string: {} | formatter:{}'.format(eval_string, formatter))
        results = self._collection_factory()

        for c in self._filtered_collection:
            try:
                result = eval('c{}'.format(eval_string))
                log.debug('result: {}'.format(result))
                if callable(formatter):
                    result = formatter(result)
            except AttributeError:
                log.debug('eval "{}": AttributeError'.format(eval_string))
                result = FAIL_CANARY_ATTRIBUTE
            except TypeError:
                log.debug('eval "{}": TypeError'.format(eval_string))
                result = FAIL_CANARY_TYPE
            except NameError:
                log.debug('eval "{}": NameError'.format(eval_string))
                result = FAIL_CANARY_NAME

            #- keep a single flat collection
            if isinstance(result, collections.abc.Sequence):
                results.extend(result)
            else:
                results.append(result)

        
        if results:
            for result_x in results:
                if result_x not in self._fail_canaries:
                    log.debug('Non fail canary found: {}'.format(result_x))
                    break
            else:
                #- all are fails
                log.debug('All values are fail canaries: {}'.format(results))
                raise CollectiveEvalDelegateObjectError(results)

        return results



    def __deepcopy__(self, memo):
        return self.__class__(self._collection, self.filters)


    def __getattr__(self, attr):
        log = LoggerAdapter(logger, {'name_ext' : 'FilteredCollection.__getattr__'})
        log.debug("FilteredCollection.__getattr('{}')".format(attr))
        eval_str = '.{}'.format(attr)
        log.debug("calling collective_eval({})".format(eval_str))
        return self.collective_eval(eval_str)


    def __str__(self):
        return str(self._collection)


    def __iter__(self):
        return iter(self._filtered_collection)
