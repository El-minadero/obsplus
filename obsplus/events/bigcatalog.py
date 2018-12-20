"""
A catalog based on SQLlite backend.
"""
import sqlite3
from typing import List
from collections import UserList

import pandas as pd
from obspy import Catalog
from obspy.core.event import ResourceIdentifier
from obsplus.interfaces import EventClient


def _get_resource_id_default(name: str) -> object:
    """
    The default function for getting resource identifiers.

    Parameters
    ----------
    name
        Any identifier that can be loaded.
    """
    return ResourceIdentifier(name).get_referred_object()


class _LazyList(UserList):
    """
    A lazy list that stores resource IDs. When each element is accessed the
    referred object is loaded.
    """

    # classes that can be used to refer to a lazy resource
    key_classes = (str, ResourceIdentifier)

    def __init__(self, *args, object_fetcher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._obj_fetcher = object_fetcher or _get_resource_id_default
        self._failed_str = set()  # strs/resource_ids that could not be loaded

    def __getitem__(self, item):
        # if the item has already been loaded return it.
        obj = super().__getitem__(item)
        if not isinstance(obj, self.key_classes) or item in self._failed_str:
            return obj
        # try to load the referred object
        out = self._obj_fetcher(obj)
        # if does not actually refer to anything just return it
        if out is None and isinstance(obj, str):
            self._failed_str.add(out)
            out = obj
        else:  # cache loaded object
            self.data[item] = out
        return out

    def __setitem__(self, key, value):
        if isinstance(value, ResourceIdentifier):
            value = str(value)
        super().__setitem__(key, value)

    @property
    def _isloaded(self) -> List[bool]:
        """ return a list of booleans corresponding to if each element in list
        has been loaded. """
        return [
            not (isinstance(x, str) and x not in self._failed_str) for x in self.data
        ]


class BigCatalog(Catalog):
    """
    A big lazy catalog.
    """


def to_big_catalog(events: EventClient) -> BigCatalog:
    """
    Convert an event client into a big catalog.

    Parameters
    ----------
    events
        Any event source.
    """

    return BigCatalog(events)
