"""XOR doubly-linked list with a single pointer field per node.

The library exposes a :class:`XorLinkedList` and a :class:`Node` whose
``link`` field holds the XOR of the addresses of its previous and next
neighbours. This halves the per-node pointer storage compared with a
classic doubly linked list at the cost of O(1) extra bookkeeping while
traversing.
"""

from .core import Node, XorLinkedList

__all__ = ["Node", "XorLinkedList"]
