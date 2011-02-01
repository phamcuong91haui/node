from odict import odict
from plumber import (
    plumber,
    Part,
    default,
    extend,
)
from zope.interface import implements
from node.interfaces import INode
from node.parts import (
    Adopt,
    AsAttrAccess,
    DefaultInit,
    Nodify,
    NodeChildValidate,
    DictStorage,
    OdictStorage,
)


class AbstractNode(object):
    __metaclass__ = plumber
    __plumbing__ = (
        Adopt,
        Nodify,
    )


class BaseNode(object):
    """Base node, not ordered.
    
    Uses ``dict`` as ``IFullMapping`` implementation.
    
    Derive this for unordered trees.
    """
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Adopt,
        AsAttrAccess,
        DefaultInit,
        Nodify,
        DictStorage,
    )


class OrderedNode(object):
    """Ordered node.
    
    Uses ``odict`` as ``IFullMapping`` implementation.
    
    Derive this for ordered trees.
    """
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Adopt,
        AsAttrAccess,
        DefaultInit,
        Nodify,
        OdictStorage,
    )
