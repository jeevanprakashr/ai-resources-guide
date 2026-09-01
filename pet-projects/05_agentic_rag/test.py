from types import UnionType
from typing import Any


class Node:
    def __init__(self, num):
        self.num = num

    def __or__(self, obj):
        print("self:", self.num)
        print("obj:", obj.num)
        return Node(self.num + obj.num)

    def __ror__(self, val):
        return self | Node(val)

a = Node(5)
b = Node(4)
c = 4 | a
print(c.num)