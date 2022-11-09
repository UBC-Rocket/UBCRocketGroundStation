from abc import ABC

class A(ABC):
    pass

class B(A):
    pass

def c(v: dict[str, B]):
    print(v)

c({"a": B()})
