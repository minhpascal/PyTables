from ..backend_h5py import open_backend
from .group import File


def open_file(*args, title='', **kwargs):
    backend = open_backend(*args, **kwargs)
    backend.attrs['TITLE'] = title
    return File(backend=backend)