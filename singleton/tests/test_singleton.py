from singleton import Singleton


class NoSingleton:
    VALUE = 0

    def __init__(self):
        NoSingleton.VALUE += 1


class IsSingleton(metaclass=Singleton):
    VALUE = 0

    def __init__(self):
        IsSingleton.VALUE += 1


async def test_no_singleton():
    no_singleton_1 = NoSingleton()
    assert no_singleton_1.VALUE == 1
    no_singleton_2 = NoSingleton()
    assert no_singleton_2.VALUE == 2
    assert no_singleton_1 is not no_singleton_2


async def test_is_singleton():
    is_singleton_1 = IsSingleton()
    assert is_singleton_1.VALUE == 1
    is_singleton_2 = IsSingleton()
    assert is_singleton_2.VALUE == 1
    assert is_singleton_1 is is_singleton_2
