"""Core implementation of the XOR doubly-linked list.

Each node stores a single integer field, ``link``, which is the bitwise XOR
of the integer addresses of its predecessor and successor. To walk from node
A to node B you need to know A *and* the node you came from, because::

    next = link XOR prev

Python objects are not integers and are moved by the garbage collector, so
we never derive a pointer value from an object. Instead every node carries a
stable integer ``addr`` and the XOR combines those integers. The list keeps a
mapping from ``addr`` to the live node object, which is what lets us turn an
XOR result back into a real node. This is the trade-off that makes the trick
work in a safe, GC-friendly way.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Optional


class Node:
    """A node in an :class:`XorLinkedList`.

    ``addr`` is the integer used in XOR arithmetic. ``link`` is the XOR of the
    addresses of this node's predecessor and successor; ``0`` means "both
    neighbours are the sentinel address", i.e. this node is the only one in the
    list. Each node registers itself with its owning list so the XOR values can
    be resolved back to live objects.
    """

    __slots__ = ("value", "addr", "link", "_owner")

    def __init__(self, value: object, addr: int, owner: "XorLinkedList") -> None:
        self.value = value
        self.addr = addr
        # XOR of the addresses of the predecessor and successor.
        # 0 is the natural "both neighbours are the sentinel (addr 0)" value.
        self.link = 0
        self._owner = owner

    def __repr__(self) -> str:
        return f"Node(value={self.value!r}, addr={self.addr})"


class XorLinkedList:
    """A doubly linked list that stores one pointer field per node.

    The list uses ``0`` as a sentinel address: XOR-ing against ``0`` leaves
    the other address unchanged, so the endpoints naturally keep the address
    of their single neighbour in ``link``. Addresses are small, dense
    integers handed out by the list itself, which keeps the address registry
    small and the XOR bookkeeping trivial to follow.
    """

    __slots__ = ("_head", "_tail", "_registry", "_next_addr")

    def __init__(self) -> None:
        # Addresses start at 1; 0 is reserved as the sentinel.
        self._next_addr = 1
        self._registry: dict[int, Node] = {}
        self._head: Optional[Node] = None
        self._tail: Optional[Node] = None

    # -- internal helpers ------------------------------------------------

    def _new_addr(self) -> int:
        addr = self._next_addr
        self._next_addr += 1
        return addr

    def _resolve(self, addr: int) -> Optional[Node]:
        """Return the live node for ``addr``.

        The sentinel address ``0`` resolves to ``None``.
        """
        if addr == 0:
            return None
        return self._registry.get(addr)

    def _xor(self, a: int, b: int) -> int:
        return a ^ b

    # -- public API ------------------------------------------------------

    def append(self, value: object) -> Node:
        """Append ``value`` at the tail and return the new node."""
        node = Node(value, self._new_addr(), self)
        self._registry[node.addr] = node
        if self._tail is None:
            # First node in an empty list. Both neighbours are the sentinel.
            node.link = 0
            self._head = node
            self._tail = node
        else:
            prev = self._tail
            # The new node's only neighbour so far is `prev`.
            node.link = prev.addr
            # `prev` previously knew prev.prev XOR sentinel; we XOR in the
            # new successor so prev.link becomes prev.prev XOR node.addr.
            prev.link = self._xor(prev.link, node.addr)
            self._tail = node
        return node

    def prepend(self, value: object) -> Node:
        """Prepend ``value`` at the head and return the new node."""
        node = Node(value, self._new_addr(), self)
        self._registry[node.addr] = node
        if self._head is None:
            node.link = 0
            self._head = node
            self._tail = node
        else:
            nxt = self._head
            node.link = nxt.addr
            nxt.link = self._xor(nxt.link, node.addr)
            self._head = node
        return node

    def pop_head(self) -> object:
        """Remove and return the head value.

        Raises :class:`IndexError` if the list is empty.
        """
        if self._head is None:
            raise IndexError("pop from an empty XorLinkedList")
        node = self._head
        nxt = self._resolve(node.link)
        if nxt is None:
            self._head = None
            self._tail = None
        else:
            # `nxt` previously knew node.addr XOR sentinel; drop the head by
            # XOR-ing its own address back in, leaving nxt.prev XOR sentinel.
            nxt.link = self._xor(nxt.link, node.addr)
            self._head = nxt
        del self._registry[node.addr]
        return node.value

    def pop_tail(self) -> object:
        """Remove and return the tail value.

        Raises :class:`IndexError` if the list is empty.
        """
        if self._tail is None:
            raise IndexError("pop from an empty XorLinkedList")
        node = self._tail
        prev = self._resolve(node.link)
        if prev is None:
            self._head = None
            self._tail = None
        else:
            prev.link = self._xor(prev.link, node.addr)
            self._tail = prev
        del self._registry[node.addr]
        return node.value

    def forward(self) -> Iterator[Node]:
        """Yield nodes from head to tail.

        The XOR trick needs the previous address to recover the next one, so
        traversal carries a ``prev`` address alongside the cursor.
        """
        prev_addr = 0
        cur = self._head
        while cur is not None:
            yield cur
            next_addr = self._xor(cur.link, prev_addr)
            prev_addr = cur.addr
            cur = self._resolve(next_addr)

    def reverse(self) -> Iterator[Node]:
        """Yield nodes from tail to head."""
        next_addr = 0
        cur = self._tail
        while cur is not None:
            yield cur
            prev_addr = self._xor(cur.link, next_addr)
            next_addr = cur.addr
            cur = self._resolve(prev_addr)

    def values(self) -> Iterator[object]:
        """Yield values from head to tail."""
        for node in self.forward():
            yield node.value

    def __iter__(self) -> Iterator[object]:
        return self.values()

    def __len__(self) -> int:
        count = 0
        for _ in self.forward():
            count += 1
        return count

    def __bool__(self) -> bool:
        return self._head is not None

    @property
    def head(self) -> Optional[Node]:
        """The head node, or ``None`` if the list is empty."""
        return self._head

    @property
    def tail(self) -> Optional[Node]:
        """The tail node, or ``None`` if the list is empty."""
        return self._tail

    def remove(self, node: Node) -> None:
        """Remove ``node`` from the list.

        Raises :class:`KeyError` if ``node`` is not part of this list.
        Removing the first or only node is handled directly; for any other
        node we walk from the head to find its predecessor (we need the
        predecessor's address to decrypt the link field).
        """
        if node.addr not in self._registry or self._registry[node.addr] is not node:
            raise KeyError("node is not a member of this list")

        if node is self._head and node is self._tail:
            self._head = None
            self._tail = None
        elif node is self._head:
            nxt = self._resolve(node.link)
            # nxt is non-None: node is head but not tail, so it has a successor.
            assert nxt is not None
            nxt.link = self._xor(nxt.link, node.addr)
            self._head = nxt
        elif node is self._tail:
            prev = self._resolve(node.link)
            # node is tail but not head, so it has a predecessor.
            assert prev is not None
            prev.link = self._xor(prev.link, node.addr)
            self._tail = prev
        else:
            # Interior node: walk to find it as seen from the head, which gives
            # us both the predecessor and successor addresses in the form the
            # link fields are stored.
            prev_addr = 0
            cur = self._head
            while cur is not None and cur is not node:
                next_addr = self._xor(cur.link, prev_addr)
                prev_addr = cur.addr
                cur = self._resolve(next_addr)
            if cur is None:
                # Should be unreachable given the membership check above.
                raise KeyError("node is not reachable from the head")
            prev = self._resolve(prev_addr)
            # prev is non-None because node is not the head.
            assert prev is not None
            next_addr = self._xor(node.link, prev.addr)
            nxt = self._resolve(next_addr)
            # nxt is non-None because node is not the tail.
            assert nxt is not None
            # Splice: each neighbour's link drops `node.addr` and gains the
            # other neighbour's address.
            prev.link = self._xor(prev.link, self._xor(node.addr, nxt.addr))
            nxt.link = self._xor(nxt.link, self._xor(node.addr, prev.addr))

        del self._registry[node.addr]
        node._owner = None  # type: ignore[assignment]

    def find(self, value: object) -> Optional[Node]:
        """Return the first node whose value equals ``value``, else ``None``."""
        for node in self.forward():
            if node.value == value:
                return node
        return None
