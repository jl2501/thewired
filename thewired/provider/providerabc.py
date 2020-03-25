'''
Provider objects are the objects that actually implement the methods that are logically
named in the Treespace Node objects. They are organized into a Namespace object for ease
of remembering where they are and having a shorter way to look them up, rathen than put
them directly in native Python nested dictionaries.
'''
import abc
import collections
import re


import warnings
from logging import getLogger, LoggerAdapter
logger = getLogger(__name__)

from thewired.exceptions import NamespaceLookupError


class ProviderError(BaseException):
    pass


class Provider(abc.ABC):
    '''
    Description:
        Abstract Base Class for all Providers. Idea here is to be able to have different
        Provider shapes. Underlying Implementor objects may require different flowcharts
        of operations to be performed to provide a certain required functionality.
        Each Provider Shape can be thus implemented as a new Provider subclass.
        This ABC ensures that any provider shape will be conformant to a specific set of
        supported operations.
    '''
    @abc.abstractmethod
    def pre_exec_hook(self, *args, **kwargs):
        '''
        Description:
            do something before we call the implementor

        Input:
            *args: variable argument list
            **kwargs: variable keyword argument list

        Output:
            None; the output of these calls are not saved anywhere
        '''
        if self.pre_exec_hook:
            if callable(self.pre_exec_hook):
                self.pre_exec_hook()
            else:
                warnings.warn("Skipping uncallable pre_exec_hook")

            
    @abc.abstractmethod
    def post_exec_hook(self, *args, **kwargs):
        '''
        Description:
            do something after we call the implementor

        Input:
            *args: variable argument list
            **kwargs: variable keyword argument list

        Output:
            None; the output of these calls are not saved anywhere
        '''
        if self.post_exec_hook:
            if callable(self.post_exec_hook):
                self.post_exec_hook()
            else:
                warnings.warn("Skipping uncallable post_exec_hook")


    @abc.abstractmethod
    def provide(self, request_id=None, **kwargs):
        '''
        Description:
            this method is called to provide an implementation for a specific request.
        Input:
            request_id: an identifier the underlying Provider can use to determine what
            flowchart of operations to execute using the implementors.
        '''
        pass

    def __call__(self, *args, **kwargs):
        return self.provide(*args, **kwargs)








def get_provider_classes():
    '''
    Description:
        entry point to building a list of all the known provider class names

    Output:
        a list of available provider classes
    '''
    provider_class_list = Provider.__subclasses__()
    return provider_class_list


