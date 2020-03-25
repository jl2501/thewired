NSID_REF_PREFIX = 'nsid://'

def is_nsid_ref(value):
    """
    Description:
        return a boolean saying whether or not the supplied argument is an NSID
        reference

    Input:
        value: what to inspect to see if it is a valid NSID reference
    """
    if isinstance(value, str) and value.startswith(NSID_REF_PREFIX):
        return True
    return False



def get_nsid_from_ref(value):
    """
    Description:
        return the NSID that an NSID reference value refers to

    Input:
        value: the NSID reference
    """
    return ''.join(value.split(NSID_REF_PREFIX)[1:])
