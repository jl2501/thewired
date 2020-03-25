"""
stuff that deals with this project's logging specifics
"""

from logging import LoggerAdapter

def make_log_adapter(logger, cls, function_name):
    """
    Description:
        simple method to wrap the parts needed to make a logging adaptor dictionary needed
        for the way that logging is configured for this project
    """
    class_name = cls.__name__ if cls is not None else ''
    addendum = dict(name_ext='.'.join([class_name, function_name]))
    return LoggerAdapter(logger, addendum)
