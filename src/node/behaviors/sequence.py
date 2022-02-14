# -*- coding: utf-8 -*-
try:
    from collections.abc import MutableSequence as ABCMutableSequence
    from collections.abc import Sequence as ABCSequence
except ImportError:
    from _abccoll import MutableSequence as ABCMutableSequence
    from _abccoll import Sequence as ABCSequence
from node.behaviors import Nodification
from node.interfaces import ISequenceNode
from node.interfaces import ISequenceStorage
from node.utils import instance_property
from plumber import Behavior
from plumber import default
from plumber import override
from plumber import plumb
from zope.interface import implementer
from zope.interface.common.collections import IMutableSequence
from zope.interface.common.collections import ISequence


@implementer(ISequence)
class Sequence(Behavior):
    __contains__ = default(ABCSequence.__contains__)
    __iter__ = default(ABCSequence.__iter__)
    __reversed__ = default(ABCSequence.__reversed__)
    count = default(ABCSequence.count)
    index = default(ABCSequence.index)

    @default
    def __len__(self):
        raise NotImplementedError

    @default
    def __getitem__(self, index):
        raise NotImplementedError


@implementer(IMutableSequence)
class MutableSequence(Sequence):
    __iadd__ = default(ABCMutableSequence.__iadd__)
    append = default(ABCMutableSequence.append)
    clear = default(ABCMutableSequence.clear)
    extend = default(ABCMutableSequence.extend)
    pop = default(ABCMutableSequence.pop)
    remove = default(ABCMutableSequence.remove)
    reverse = default(ABCMutableSequence.reverse)

    @default
    def __setitem__(self, index, value):
        raise NotImplementedError

    @default
    def __delitem__(self, index):
        raise NotImplementedError

    @default
    def insert(self, index, value):
        raise NotImplementedError


@implementer(ISequenceStorage)
class ListStorage(Behavior):

    @default
    @instance_property
    def storage(self):
        return list()

    @override
    def __len__(self):
        return len(self.storage)

    @override
    def __getitem__(self, index):
        return self.storage[index]

    @override
    def __setitem__(self, index, value):
        self.storage[index] = value

    @override
    def __delitem__(self, index):
        del self.storage[index]

    @override
    def insert(self, index, value):
        self.storage.insert(index, value)


@implementer(ISequenceNode)
class SequenceNode(Nodification, MutableSequence):

    @override
    def __index__(self):
        try:
            return int(self.__name__)
        except (TypeError, ValueError):
            raise IndexError('Node not member of a sequence node')

    @plumb
    def __getitem__(next_, self, index):
        if type(index) is slice:
            raise NotImplementedError('No slice support yet')
        return next_(self, index)

    @plumb
    def __setitem__(next_, self, index, value):
        if type(index) is slice:
            raise NotImplementedError('No slice support yet')
        value.__name__ = str(index)
        value.__parent__ = self
        next_(self, int(index), value)

    @plumb
    def __delitem__(next_, self, index):
        if type(index) is slice:
            raise NotImplementedError('No slice support yet')
        return next_(self, index)

    @plumb
    def insert(next_, self, index, value):
        value.__name__ = str(index)
        value.__parent__ = self
        next_(self, int(index), value)
