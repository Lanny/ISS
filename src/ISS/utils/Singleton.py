class Singleton(object):
    _INSTANCE = None
    default_args = []
    default_kwargs = {}

    @classmethod
    def get_instance(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls(*cls.default_args, **cls.default_kwargs)

        return cls._INSTANCE
    
