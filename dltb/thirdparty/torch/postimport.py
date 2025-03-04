"""
This module adds some hooks to work with torch:

* adapt :py:func:`dltb.base.image.Data` to allow transformation of
  `Datalike` objects to :py:class:`torch.Tensor` (as_torch) as well
  as and from :py:class:`PIL.Image.Image` to other formats.

* add a data kind 'torch' and an associated loader to the
  :py:class:`Datasource` class.

"""

# standard imports
import logging

# third party imports
import numpy as np
import torch

# toolbox imports
from ...base.data import Data, Datalike
from ...datasource import Datasource

# logging
LOG = logging.getLogger(__name__)


def as_torch(data: Datalike, copy: bool = False) -> torch.Tensor:
    """Get a :py:class:`torch.Tensor` from a :py:class:`Datalike`
    object.
    """
    if isinstance(data, torch.Tensor):
        return data.clone().detach() if copy else data

    if isinstance(data, str) and data.endswith('.pt'):
        return torch.load(data)

    if isinstance(data, Data):
        if not hasattr(data, 'torch'):
            data.add_attribute('torch', Data.as_torch(data.array, copy=copy))
        return data.torch

    if not isinstance(data, np.ndarray):
        data = Data.as_array(data)

    # from_numpy() will use the same data as the numpy array, that
    # is changing the torch.Tensor will also change the numpy.ndarray.
    # On the other hand, torch.tensor() will always copy the data.

    # pylint: disable=not-callable
    # torch bug: https://github.com/pytorch/pytorch/issues/24807
    return torch.tensor(data) if copy else torch.from_numpy(data)


LOG.info("Adapting dltb.base.data.Data: adding static method 'as_torch'")
Data.as_torch = staticmethod(as_torch)

# add a loader for torch data: typical suffix is '.pt' (pytorch)
Datasource.add_loader('torch', torch.load)
