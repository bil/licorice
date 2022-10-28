import warnings

import SharedArray as sa


def create_shared_array(name, shape, dtype):
    """Create a SharedArray safely.

    Creates a SharedArray. If one with the same name already exists, issue a
    warning, delete the named SharedArray and try again.

    Args:
        shape (int or tuple of ints): Shape of the new SharedArray
        dtype (data-type): The desired data-type for the SharedArray.

    Returns:
        sig (numpy.ndarray): SharedArray object represented as numpy array
            stored in POSIX shared memory
    """
    try:
        sig = sa.create(name, shape, dtype=dtype)
    except FileExistsError:
        warnings.warn(f"SharedArray with name {name} already exists.")
        sa.delete(name)
        sig = sa.create(name, shape, dtype=dtype)

    return sig
