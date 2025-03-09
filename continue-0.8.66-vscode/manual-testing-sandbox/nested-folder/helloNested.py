from typing import List

Vector = List[float]


def main(a: Vector):
    print("Hello Nested!")


class MyClass:
    def __init__(self):
        pass

    def test(a: Vector) -> Vector:
        return a

    def sort_func(self, a: Vector) -> Vector:
        return sorted(a)
        

raise Exception("This is an error")
