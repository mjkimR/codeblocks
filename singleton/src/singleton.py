class Singleton(type):
    """
    A metaclass that creates a Singleton instance (without a lock, so could not be thread-safe).

    This metaclass ensures that only one instance of a class is created.
    If an instance of the class already exists, it returns the existing instance.

    Attributes:
        _instances (dict): A dictionary to store the single instances of the classes.

    Example:
        class MyClass(metaclass=Singleton):
            pass

        instance = MyClass()
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
