
def per_cls(cache, cls, factory=dict):
    # returns the per-class dict, creating if absent
    value = cache.get(cls)
    if value is None:
        value = cache[cls] = factory()
    return value


def is_builtin(o):

    # Fast path: check if object is a builtin singleton
    # TODO replace with `match` statement once we drop support for Python 3.9
    # match x:
    #     case None: pass
    #     case True: pass
    #     case False: pass
    #     case builtins.Ellipsis: pass
    if o in {None, True, False, ...}:
        return True

    return getattr(o, '__class__', o).__module__ == 'builtins'


def create_new_class(
        class_or_instance, bases,
        suffix=None, attr_dict=None):

    if not suffix and bases:
        suffix = get_class_name(bases[0])

    new_cls_name = f'{get_class_name(class_or_instance)}{suffix}'

    return type(
        new_cls_name,
        bases,
        attr_dict or {'__slots__': ()}
    )


def get_class_name(class_or_instance):

    try:
        return class_or_instance.__qualname__
    except AttributeError:
        # We're dealing with a dataclass instance
        return type(class_or_instance).__qualname__


def get_outer_class_name(inner_cls, default=None, raise_=True):

    try:
        name = get_class_name(inner_cls).rsplit('.', 1)[-2]
        # This is mainly for our test cases, where we nest the class
        # definition in the test func. Either way, it's not a valid class.
        assert not name.endswith('<locals>')

    except (IndexError, AssertionError):
        if raise_:
            raise
        return default

    else:
        return name


def get_class(obj):

    return obj if isinstance(obj, type) else type(obj)


def is_subclass(obj, base_cls):

    cls = obj if isinstance(obj, type) else type(obj)
    return issubclass(cls, base_cls)


def is_subclass_safe(cls, class_or_tuple):

    try:
        return issubclass(cls, class_or_tuple)
    except TypeError:
        return False
