# xor_linked_list

A doubly linked list where each node stores a single pointer field, computed as the XOR of the integer addresses of its predecessor and successor. Exports `Node` and `XorLinkedList`.

```python
from xor_linked_list import XorLinkedList

lst = XorLinkedList()
lst.append("a")
lst.append("b")
lst.prepend("z")
print(list(lst))           # ['z', 'a', 'b']
print(lst.pop_tail())      # 'b'
for node in lst.forward():
    print(node.value)
```

## Why this exists

A normal doubly linked list keeps two pointers per node (`prev` and `next`). The XOR trick folds them into one field by storing `prev_addr XOR next_addr`: given either neighbour's address you recover the other with a single XOR. This library exists to show that pattern working end to end in Python.

The trade-off is that Python objects do not have stable integer addresses you can XOR, so the list assigns each node a small integer `addr` and keeps an `addr -> node` registry to turn XOR results back into live objects. You save one pointer field per node and pay one dict lookup per traversal step. This is an educational data structure, not a performance win over `collections.deque`.

The sentinel address is `0`: XOR-ing against `0` leaves the other address unchanged, so endpoint nodes keep their single neighbour's address directly in `link`, and an isolated node's `link` is `0`.

## Awkward edges

`Node` objects are tied to the `XorLinkedList` that created them. Passing a node from one list into another list's `remove` raises `KeyError`, as does calling `remove` on a node you have already removed. The list does not validate that a `Node` you hand to `remove` came from *this* list via its type — it checks the node's address against its own registry.

`len(lst)` and `list(lst)` both walk the list, so they are O(n), not O(1). There is no caching of the length.
