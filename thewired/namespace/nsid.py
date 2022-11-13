"""
All the things for dealing with NSIDs
There are many module-level methods here as I didn't want to make the Nsid object's core
purpose obfuscated by all of the helper methods for dealing with NSIDs as strings.
The main purpose of the Nsid type is really to be able to lean on the typing system for
input validation and I wanted to keep it pretty small and crisp. There are a lot of
logical operations that are common when dealing with NSID strings, but they really don't
need to be all be stuffed into the Nsid object IMO. This makes importing all these methods
a bit more precise at the expense of having to be explicit as to which methods are being
imported
"""

import logging
import re
from typing import List

from thewired.loginfo import make_log_adapter
from thewired.exceptions import NsidError, InvalidNsidError, NsidSanitizationError

logger = logging.getLogger(__name__)

class NsidBase(object):
    """
    Description:
        simple way to inherit common properties
    """
    default_separator = '.'
    def __init__(self, separator=None):
        #- character used to deliniate NSID components
        self.nsid_separator = self.default_separator if separator is None else separator


class Nsid(NsidBase):
    """
    Description:
        simple string type, but we want to lean on the type system to be able to discern
        the two more easily.
        NSIDs are the Name Space ID that every node in a namespace contains.
        NSIDs follow a hierarchy, much like a filesystem in an OS, and employ some similar
        concepts such as symbolic references ("symlinks" in FS-world)
    """

    nsid_link_prefix = 'nsid://'
    nsid_ref_prefix = 'nsid-ref://'

    def __init__(self, nsid, fully_qualified=False):
        """
        Inputs:
            nsid: the string to be converted into an NSID
        """
        super().__init__()
        log = make_log_adapter(logger, self.__class__, '__init__')
        self.nsid = ''

        validate_nsid(nsid, symrefs_ok=False, fully_qualified=fully_qualified)
        #log.debug(f'nsid validated: {nsid}')
        self.nsid = str(nsid)


    def __repr__(self):
        return f'Nsid({self.nsid})'

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
            self.nsid == other.nsid)


    def __str__(self):
        return self.nsid



def validate_nsid(nsid, nsid_root_ok=True, symrefs_ok=True, separator='.', fully_qualified=True):
    if not is_valid_nsid_str(nsid, symrefs_ok=symrefs_ok, separator=separator, fully_qualified=fully_qualified):
        raise InvalidNsidError(f'invalid NSID: "{nsid}"')


def is_valid_nsid_str(nsid, nsid_root_ok=True, symrefs_ok=True, separator='.', fully_qualified=True):
    log = make_log_adapter(logger, None, 'is_valid_nsid_str')

    if isinstance(nsid, Nsid):
        #- already has been validated
        #- this technically could allow someone to instantiate
        #- with an Nsid object that has been reassigned after validation
        #- using internal properties,but, its python, so thats acceptable
        return True

    if fully_qualified and nsid[0] != separator:
        return False

    if isinstance(nsid, str):
        if ' ' in nsid:
            return False

        if nsid == separator:
            return nsid_root_ok
        elif symrefs_ok and is_valid_nsid_link(nsid, separator=separator):
            return True
        else:
            parts = get_nsid_parts(nsid)
            if len(parts) > 1:
                valid_nsid = False
                for n, part in enumerate(parts):
                    if not isinstance(part, str):
                       break
                    if part == '':
                        if n != 0:
                            #- first part can be dot, but no two consecutive dots
                            break
                    elif not part.isidentifier():
                        break
                else:
                    #- we never hit break
                    valid_nsid = True
            else:
                #- to be valid must be its own NS root
                valid_nsid = nsid_root_ok
    else:
        valid_nsid = False
    return valid_nsid


def is_valid_nsid_link(symref, separator='.'):
    log = make_log_adapter(logger, None, 'is_valid_nsid_link')
    if symref.startswith(Nsid.nsid_link_prefix):
        prefix,nsid = symref.split(Nsid.nsid_link_prefix)
        return is_valid_nsid_str(nsid, symrefs_ok=False, separator=separator)

def is_valid_nsid_ref(ref, separator='.'):
    log = make_log_adapter(logger, None, 'is_valid_nsid_ref')
    if ref.startswith(Nsid.nsid_ref_prefix):
        prefix,nsid = ref.split(Nsid.nsid_ref_prefix)
        return is_valid_nsid_str(nsid, symrefs_ok=False, separator=separator)

def sanitize_nsid(nsid, separator='.'):
    """
    Description:
        make simple changes needed to correct an NSID, when possible.
        Looks for things like multiple consecutive NSID separator characters.
    Input:
        unsanitized nsid string
    Output:
        standard-conformant nsid string
    """
    log = make_log_adapter(logger, None, 'sanitize_nsid')
    try:
        sanitized_nsid = re.sub(f"\{separator}\{separator}+", f"{separator}", nsid)
    except (NameError, TypeError) as err:
        raise NsidSanitizationError(f'error sanitizing nsid {nsid}: {err}')
    else:
        if sanitized_nsid != nsid:
            log.debug("Sanitized NSID: {} ---> {}".format(\
                nsid, sanitized_nsid))
    return sanitized_nsid


def make_child_nsid(parent_nsid, child, separator='.'):
    log = make_log_adapter(logger, None, 'make_child_nsid') 
    if is_valid_nsid_str(parent_nsid, separator=separator, fully_qualified=False):
        if  is_valid_nsid_str(child, separator=separator, fully_qualified=False):
            if parent_nsid == separator:    #is root?
                return separator.join(['', child])
            else:
                if child.startswith(separator):
                    return ''.join([parent_nsid, child])
                else:
                    return separator.join([parent_nsid, child])
        else:
            raise InvalidNsidError(f'invalid child NSID "{child}"')
    else:
        raise InvalidNsidError(f'invalid parent NSID "{parent_nsid}"')


def get_parent_nsid(nsid, parent_num=1, separator='.'):
    validate_nsid(nsid)
    retval = separator.join(
        nsid.split(separator)[0:-parent_num]
    )
    if retval == '':
        return '.'
    else:
        return retval


def get_nsid_parts(nsid, separator='.'):
    return nsid.split(separator)

def list_nsid_segments(nsid, separator='.', skip_root=False) -> List:
    if nsid == separator:
        return [nsid]

    segments = nsid.split(separator)
    if segments[0] == '':
        if not skip_root:
            segments[0] = separator
        else:
            segments.remove(segments[0])
    return segments

def find_common_prefix(nsid1, nsid2, separator='.'):
    nsid1 = str(nsid1) if isinstance(nsid1, Nsid) else nsid1
    nsid2 = str(nsid2) if isinstance(nsid2, Nsid) else nsid2

    nsid1_parts = get_nsid_parts(nsid1, separator=separator)
    nsid2_parts = get_nsid_parts(nsid2, separator=separator)

    i = 0
    while (i < len(nsid1_parts) and
            i < len(nsid2_parts) and
            nsid1_parts[i] == nsid2_parts[i]):
        i += 1
    if i == 0:
        return None
    else:
        return separator.join(nsid1_parts[0:i])


def strip_schema(nsid):
    _nsid = nsid.split( Nsid.nsid_link_prefix )[1:]
    _nsid = nsid.split( Nsid.nsid_ref_prefix )[1:]
    return _nsid

def strip_prefix(prefix, nsid, separator='.'):
    stripped = list()
    prefix_len = len(prefix.split(separator))
    for n, part in enumerate(nsid.split(separator)):
        if n > prefix_len:
            stripped.append(part)
    return separator.join(stripped)


def strip_common_prefix(nsid1, nsid2, separator='.'):
    common_prefix = find_common_prefix(nsid1, nsid2, separator=separator)
    common_prefix_len = len(common_prefix.split(separator))

    stripped_nsid1 = list()
    common_prefix_parts = common_prefix.split(separator)
    for n, part in enumerate(nsid1.split(separator)):
        if n > len(common_prefix_parts) - 1:
            stripped_nsid1.append(part)
    stripped_nsid1 = separator.join(stripped_nsid1)

    #- same thing for nsid2
    stripped_nsid2 = list()
    common_prefix_parts = common_prefix.split(separator)
    for n, part in enumerate(nsid2.split(separator)):
        if n > len(common_prefix_parts) - 1:
            stripped_nsid2.append(part)
    stripped_nsid2 = separator.join(stripped_nsid2)

    return stripped_nsid1, stripped_nsid2


def get_nsid_ancestry(nsid, separator='.'): 
    nsid_segments = get_nsid_parts(nsid)
    ancestry = list()
    for i in range(len(nsid_segments)):
        new_ancestor_segments = list()
        for n in range(i+1):
            new_ancestor_segments.append(nsid_segments[n])
        new_ancestor = separator.join(new_ancestor_segments)
        if new_ancestor == '':
            new_ancestor = separator
        ancestry.append(new_ancestor)
    return ancestry


def nsid_basename(nsid, separator='.'):
    if nsid == separator:
        return nsid
    return str(nsid).split(separator)[-1]

def get_nsid_from_ref(nsidref):
    return nsidlref.split(Nsid.nsid_ref_prefix)[1]

def get_nsid_from_link(nsidlink):
    return nsidlink.split(Nsid.nsid_link_prefix)[1]
