##!FAIL: TupleTypeExpectationError[int]@7:4


def f(x):
    """ int -> int
    Destruction of a non-tuple type """
    a, b = x
    return a + b > 0
