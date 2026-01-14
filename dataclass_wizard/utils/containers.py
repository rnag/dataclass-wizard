import json

from ..class_helper import str_pprint_fn
from ..decorators import cached_property
from ..type_def import T
from ._dataclass_compat import set_new_attribute


class Container(list[T]):

    __slots__ = ('__dict__',
                 '__orig_class__')

    @cached_property
    def __model__(self):

        try:
            # noinspection PyUnresolvedReferences
            return self.__orig_class__.__args__[0]
        except AttributeError:
            cls_name = self.__class__.__qualname__
            msg = (f'A {cls_name} object needs to be instantiated with '
                   f'a generic type T.\n\n'
                   'Example:\n'
                   f'  my_list = {cls_name}[T](...)')

            raise TypeError(msg) from None

    # noinspection PyShadowingBuiltins
    def __init_subclass__(cls,
                          str=False):
        super().__init_subclass__()

        # Add a `__str__` method to the subclass, if needed
        if str:
            set_new_attribute(cls, '__str__', str_pprint_fn())

    def prettify(self, encoder = json.dumps,
                 ensure_ascii=False,
                 **encoder_kwargs):

        return self.to_json(
            indent=2,
            encoder=encoder,
            ensure_ascii=ensure_ascii,
            **encoder_kwargs
        )

    def to_json(self, encoder=json.dumps,
                **encoder_kwargs):
        from ..dumpers import asdict

        cls = self.__model__
        list_of_dict = [asdict(o, cls=cls) for o in self]

        return encoder(list_of_dict, **encoder_kwargs)

    def to_json_file(self, file, mode = 'w',
                     encoder=json.dump,
                     **encoder_kwargs):
        # TODO
        from ..dumpers import asdict

        cls = self.__model__
        list_of_dict = [asdict(o, cls=cls) for o in self]

        with open(file, mode) as out_file:
            encoder(list_of_dict, out_file, **encoder_kwargs)
