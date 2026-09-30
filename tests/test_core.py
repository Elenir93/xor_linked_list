import unittest

from xor_linked_list import Node, XorLinkedList


class TestEmptyList(unittest.TestCase):
    def test_empty_has_no_head_or_tail(self):
        lst = XorLinkedList()
        self.assertIsNone(lst.head)
        self.assertIsNone(lst.tail)

    def test_empty_iterates_to_nothing(self):
        lst = XorLinkedList()
        self.assertEqual(list(lst), [])
        self.assertEqual(list(lst.values()), [])
        self.assertEqual(len(lst), 0)

    def test_pop_head_empty_raises(self):
        with self.assertRaises(IndexError):
            XorLinkedList().pop_head()

    def test_pop_tail_empty_raises(self):
        with self.assertRaises(IndexError):
            XorLinkedList().pop_tail()

    def test_bool_false_when_empty(self):
        self.assertFalse(bool(XorLinkedList()))


class TestAppend(unittest.TestCase):
    def test_append_one_node(self):
        lst = XorLinkedList()
        node = lst.append("a")
        self.assertIs(lst.head, node)
        self.assertIs(lst.tail, node)
        # Both neighbours are the sentinel, so link is 0.
        self.assertEqual(node.link, 0)
        self.assertEqual(list(lst.values()), ["a"])
        self.assertEqual(len(lst), 1)
        self.assertTrue(bool(lst))

    def test_append_three_nodes_forward_and_reverse(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        c = lst.append(3)
        self.assertEqual([n.value for n in lst.forward()], [1, 2, 3])
        self.assertEqual([n.value for n in lst.reverse()], [3, 2, 1])
        # Interior node links to XOR of its two neighbours.
        self.assertEqual(b.link, a.addr ^ c.addr)
        # Endpoints keep their sole neighbour's address.
        self.assertEqual(a.link, b.addr)
        self.assertEqual(c.link, b.addr)

    def test_append_then_pop_tail_to_empty(self):
        lst = XorLinkedList()
        lst.append("x")
        self.assertEqual(lst.pop_tail(), "x")
        self.assertEqual(len(lst), 0)
        self.assertIsNone(lst.head)
        self.assertIsNone(lst.tail)

    def test_append_then_pop_head_keeps_tail_pointer(self):
        lst = XorLinkedList()
        lst.append("first")
        b = lst.append("second")
        self.assertEqual(lst.pop_head(), "first")
        self.assertIs(lst.head, b)
        self.assertIs(lst.tail, b)
        # Now the only node, so link reverts to 0.
        self.assertEqual(b.link, 0)


class TestPrepend(unittest.TestCase):
    def test_prepend_into_empty(self):
        lst = XorLinkedList()
        node = lst.prepend("a")
        self.assertIs(lst.head, node)
        self.assertIs(lst.tail, node)
        self.assertEqual(list(lst.values()), ["a"])

    def test_prepend_builds_reverse_order(self):
        lst = XorLinkedList()
        lst.append("a")
        lst.prepend("b")
        lst.prepend("c")
        self.assertEqual(list(lst.values()), ["c", "b", "a"])
        self.assertEqual([n.value for n in lst.reverse()], ["a", "b", "c"])

    def test_prepend_after_append_updates_link(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.prepend(0)
        self.assertEqual(a.link, b.addr)
        self.assertEqual(b.link, a.addr)


class TestPops(unittest.TestCase):
    def test_pop_tail_middle_relinks(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        c = lst.append(3)
        self.assertEqual(lst.pop_tail(), 3)
        self.assertIs(lst.tail, b)
        # a <-> b now; b is tail, so its link holds just a.addr.
        self.assertEqual(b.link, a.addr)
        self.assertEqual(a.link, b.addr)
        self.assertEqual(list(lst.values()), [1, 2])

    def test_pop_head_then_tail_then_empty(self):
        lst = XorLinkedList()
        lst.append(1)
        lst.append(2)
        self.assertEqual(lst.pop_head(), 1)
        self.assertEqual(lst.pop_tail(), 2)
        self.assertEqual(len(lst), 0)
        self.assertFalse(bool(lst))


class TestRemove(unittest.TestCase):
    def test_remove_only_node(self):
        lst = XorLinkedList()
        node = lst.append("only")
        lst.remove(node)
        self.assertIsNone(lst.head)
        self.assertIsNone(lst.tail)
        self.assertEqual(list(lst.values()), [])

    def test_remove_head(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        c = lst.append(3)
        lst.remove(a)
        self.assertIs(lst.head, b)
        # b is now head: link holds just c.addr.
        self.assertEqual(b.link, c.addr)
        self.assertEqual(c.link, b.addr)
        self.assertEqual(list(lst.values()), [2, 3])

    def test_remove_tail(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        c = lst.append(3)
        lst.remove(c)
        self.assertIs(lst.tail, b)
        self.assertEqual(b.link, a.addr)
        self.assertEqual(a.link, b.addr)
        self.assertEqual(list(lst.values()), [1, 2])

    def test_remove_interior(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        c = lst.append(3)
        lst.remove(b)
        # a and c become direct neighbours.
        self.assertEqual(a.link, c.addr)
        self.assertEqual(c.link, a.addr)
        self.assertEqual(list(lst.values()), [1, 3])
        self.assertEqual([n.value for n in lst.reverse()], [3, 1])

    def test_remove_node_from_other_list_raises(self):
        lst_a = XorLinkedList()
        node = lst_a.append(1)
        lst_b = XorLinkedList()
        with self.assertRaises(KeyError):
            lst_b.remove(node)

    def test_remove_freed_node_raises(self):
        lst = XorLinkedList()
        node = lst.append("a")
        lst.remove(node)
        with self.assertRaises(KeyError):
            lst.remove(node)


class TestFind(unittest.TestCase):
    def test_find_returns_first_match(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        c = lst.append(1)
        found = lst.find(1)
        self.assertIs(found, a)
        # find(2) skips the duplicate 1s and returns b.
        self.assertIs(lst.find(2), b)
        # find(1) again is still a (first occurrence).
        self.assertIs(lst.find(1), a)
        self.assertIs(c, lst.tail)

    def test_find_missing_returns_none(self):
        lst = XorLinkedList()
        lst.append("a")
        self.assertIsNone(lst.find("z"))

    def test_find_in_empty_returns_none(self):
        self.assertIsNone(XorLinkedList().find("anything"))


class TestTraversalConsistency(unittest.TestCase):
    def test_forward_and_reverse_agree_after_mixed_ops(self):
        lst = XorLinkedList()
        lst.append("b")
        lst.prepend("a")
        lst.append("c")
        lst.append("d")
        lst.pop_head()  # drops "a"
        lst.pop_tail()  # drops "d"
        forward = [n.value for n in lst.forward()]
        reverse = [n.value for n in lst.reverse()]
        self.assertEqual(forward, ["b", "c"])
        self.assertEqual(reverse, ["c", "b"])

    def test_forward_passes_actual_nodes(self):
        lst = XorLinkedList()
        a = lst.append(1)
        b = lst.append(2)
        seen = list(lst.forward())
        self.assertEqual(seen, [a, b])

    def test_len_matches_iteration_count(self):
        lst = XorLinkedList()
        for i in range(5):
            lst.append(i)
        lst.pop_head()
        lst.pop_tail()
        # 5 minus the two pops == 3.
        self.assertEqual(len(lst), 3)
        self.assertEqual(sum(1 for _ in lst.forward()), 3)


class TestNodeRepr(unittest.TestCase):
    def test_repr_mentions_value(self):
        lst = XorLinkedList()
        node = lst.append({"k": 1})
        r = repr(node)
        self.assertIn("addr=", r)
        # Value is included via its repr so the dict renders literally.
        self.assertIn("{'k': 1}", r)


if __name__ == "__main__":
    unittest.main()
