from dataclasses import MISSING

from ..log import LOG


def is_builtin_class(cls: type) -> bool:
    """Check if a class is a builtin in Python."""
    return cls.__module__ == 'builtins'


class FunctionBuilder:
    __slots__ = (
        'current_function',
        'prev_function',
        'functions',
        'globals',
        'indent_level',
        'namespace',
    )

    def __init__(self):
        self.functions = {}
        self.indent_level = 0
        self.globals = {}
        self.namespace = {}

    def __ior__(self, other):
        """
        Allows `|=` operation for :class:`FunctionBuilder` objects,
        e.g. ::
            my_fn_builder |= other_fn_builder

        """
        self.functions |= other.functions
        return self

    def __enter__(self):
        self.indent_level += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        indent_lvl = self.indent_level = self.indent_level - 1

        if not indent_lvl:
            self.finalize_function()

    # noinspection PyAttributeOutsideInit
    def function(self, name: str, args: list, return_type=MISSING,
                 locals=None) -> 'FunctionBuilder':
        """Start a new function definition with optional return type."""
        curr_fn = getattr(self, 'current_function', None)
        if curr_fn is not None:
            curr_fn['indent_level'] = self.indent_level
            self.prev_function = curr_fn

        self.current_function = {
            "name": name,
            "args": args,
            "body": [],
            "return_type": return_type,
            "locals": locals if locals is not None else {},
        }

        self.indent_level = 0
        return self

    def _with_new_block(self,
                        name: str,
                        condition: 'str | None' = None,
                        comment: str = '') -> 'FunctionBuilder':
        """Creates a new block. Used with a context manager (with)."""
        indent = '  ' * self.indent_level

        if comment:
            comment = f'  # {comment}'

        if condition is not None:
            self.current_function["body"].append(f"{indent}{name} {condition}:{comment}")
        else:
            self.current_function["body"].append(f"{indent}{name}:{comment}")

        return self

    def for_(self, condition: str) -> 'FunctionBuilder':
        """Equivalent to the `for` statement in Python.

        Sample Usage:

            >>> with FunctionBuilder().for_('i in range(3)'):
            >>>     ...

        Will generate the following code:

            >>> for i in range(3):
            >>>     ...

        """
        return self._with_new_block('for', condition)

    def if_(self, condition: str, comment: str = '') -> 'FunctionBuilder':
        """Equivalent to the `if` statement in Python.

        Sample Usage:

            >>> with FunctionBuilder().if_('something is True'):
            >>>     ...

        Will generate the following code:

            >>> if something is True:
            >>>     ...

        """
        return self._with_new_block('if', condition, comment)

    def elif_(self, condition: str) -> 'FunctionBuilder':
        """Equivalent to the `elif` statement in Python.

        Sample Usage:

            >>> with FunctionBuilder().elif_('something is True'):
            >>>     ...

        Will generate the following code:

            >>> elif something is True:
            >>>     ...

        """
        return self._with_new_block('elif', condition)

    def else_(self) -> 'FunctionBuilder':
        """Equivalent to the `else` statement in Python.

        Sample Usage:

            >>> with FunctionBuilder().else_():
            >>>     ...

        Will generate the following code:

            >>> else:
            >>>     ...

        """
        return self._with_new_block('else')

    def try_(self) -> 'FunctionBuilder':
        """Equivalent to the `try` block in Python.

        Sample Usage:

            >>> with FunctionBuilder().try_():
            >>>     ...

        Will generate the following code:

            >>> try:
            >>>     ...

        """
        return self._with_new_block('try')

    def except_(self,
                cls: type[Exception],
                var_name: 'str | None' = None,
                *custom_classes: type[Exception]):
        """Equivalent to the `except` block in Python.

        Sample Usage:

            >>> with FunctionBuilder().except_(TypeError, 'exc'):
            >>>     ...

        Will generate the following code:

            >>> except TypeError as exc:
            >>>     ...

        """
        cls_name = cls.__name__
        statement = f'{cls_name} as {var_name}' if var_name else cls_name

        if not is_builtin_class(cls):
            if cls_name not in self.globals:
                # TODO
                # LOG.debug('Ensuring class in globals, cls=%s', cls_name)
                self.globals[cls_name] = cls

        if custom_classes:
            for cls in custom_classes:
                if not is_builtin_class(cls):
                    cls_name = cls.__name__
                    if cls_name not in self.globals:
                        # LOG.debug('Ensuring class in globals, cls=%s', cls_name)
                        self.globals[cls_name] = cls

        return self._with_new_block('except', statement)

    def except_multi(self, *classes: type[Exception]):
        """Equivalent to the `except` block in Python.

        Sample Usage:

            >>> with FunctionBuilder().except_multi(AttributeError, TypeError, ValueError):
            >>>     ...

        Will generate the following code:

            >>> except (AttributeError, TypeError, ValueError):
            >>>     ...

        """
        if len(classes) == 1:
            statement = classes[0].__name__
        else:
            class_names = ', '.join([cls.__name__ for cls in classes])
            statement = f'({class_names})'

        return self._with_new_block('except', statement)

    def break_(self):
        """Equivalent to the `break` statement in Python."""
        self.add_line('break')

    def add_line(self, line: str):
        """Add a line to the current function's body with proper indentation."""
        indent = '  ' * self.indent_level
        self.current_function["body"].append(f"{indent}{line}")

    def add_lines(self, *lines: str):
        """Add lines to the current function's body with proper indentation."""
        indent = '  ' * self.indent_level
        self.current_function["body"].extend(
            [f"{indent}{line}" for line in lines]
        )

    def increase_indent(self):  # pragma: no cover
        """Increase indentation level for nested code."""
        self.indent_level += 1

    def decrease_indent(self):  # pragma: no cover
        """Decrease indentation level."""
        if self.indent_level > 1:
            self.indent_level -= 1

    def finalize_function(self):
        """Finalize the function code and add to the list of functions."""
        # Add the function body and don't re-add the function definition
        curr_fn = self.current_function
        func_code = '\n'.join(curr_fn["body"])
        self.functions[curr_fn["name"]] = {
            "args": curr_fn["args"],
            "return_type": curr_fn["return_type"],
            "locals": curr_fn["locals"],
            "code": func_code
        }

        if (prev_fn := getattr(self, 'prev_function', None)) is not None:
            self.indent_level = prev_fn.pop('indent_level')
            self.current_function = prev_fn
            self.prev_function = None
        else:
            self.current_function  # Reset current function

    def create_functions(self, _globals=None):
        """Create functions by compiling the code."""
        # Note that we may mutate locals. Callers beware!
        # The only callers are internal to this module, so no
        # worries about external callers.

        # Compute the text of the entire function.
        # txt = f' def {name}({args}){return_annotation}:\n{body}'

        # Build the function code for all functions
        # Free variables in exec are resolved in the global namespace.
        # The global namespace we have is user-provided, so we can't modify it for
        # our purposes. So we put the things we need into locals and introduce a
        # scope to allow the function we're creating to close over them.

        fn_name_locals_and_code = []

        for name, func in self.functions.items():
            args = ','.join(func['args'])
            body = func['code']
            return_type = func['return_type']
            locals = func['locals']

            return_annotation = ''
            if return_type is not MISSING:
                locals[f'__dataclass_{name}_return_type__'] = return_type
                return_annotation = f'->__dataclass_{name}_return_type__'

            fn_name_locals_and_code.append(
                (name,
                 locals,
                 f'def {name}({args}){return_annotation}:\n{body}')
            )

        txt = '\n'.join([
            f"def __create_{name}_fn__({', '.join(locals.keys())}):\n"
            f" {code}\n"
            f" return {name}"
            for name, locals, code in fn_name_locals_and_code
        ])

        # Print the generated code for debugging
        # logging.debug(f"Generated function code:\n{all_func_code}")
        LOG.debug("Generated function code:\n%s", txt)

        ns = {}

        # TODO
        _globals = self.globals if _globals is None else _globals | self.globals

        LOG.debug("Globals before function compilation: %s", _globals)

        exec(txt, _globals, ns)

        # TODO do we need self.namespace?
        final_ns = self.namespace = {}

        # TODO: add function to dependent function `locals` rather than to `globals`

        for name, locals, _ in fn_name_locals_and_code:
            _globals[name] = final_ns[name] = ns[f'__create_{name}_fn__'](**locals)

        # final_ns = self.namespace = {
        #     name: ns[f'__create_{name}_fn__'](**locals)
        #     for name, locals, _ in fn_name_locals_and_code
        # }

        # Print namespace for debugging
        LOG.debug("Namespace after function compilation: %s", final_ns)

        return final_ns
