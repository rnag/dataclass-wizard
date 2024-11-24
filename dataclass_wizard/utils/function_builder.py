from dataclasses import MISSING

from ..class_helper import is_builtin_class
from ..log import LOG


class FunctionBuilder:
    __slots__ = (
        'current_function',
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

    def __enter__(self):
        self.indent_level += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        indent_lvl = self.indent_level = self.indent_level - 1

        if not indent_lvl:
            self.finalize_function()

    def function(self, name: str, args: list, return_type=MISSING) -> 'FunctionBuilder':
        """Start a new function definition with optional return type."""
        # noinspection PyAttributeOutsideInit
        self.current_function = {"name": name, "args": args, "body": [], "return_type": return_type}
        return self

    def _with_new_block(self,
                        name: str,
                        condition: 'str | None' = None) -> 'FunctionBuilder':
        """Creates a new block. Used with a context manager (with)."""
        indent = '  ' * self.indent_level

        if condition is not None:
            self.current_function["body"].append(f"{indent}{name} {condition}:")
        else:
            self.current_function["body"].append(f"{indent}{name}:")

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

    def if_(self, condition: str) -> 'FunctionBuilder':
        """Equivalent to the `if` statement in Python.

        Sample Usage:

            >>> with FunctionBuilder().if_('something is True'):
            >>>     ...

        Will generate the following code:

            >>> if something is True:
            >>>     ...

        """
        return self._with_new_block('if', condition)

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
                var_name: 'str | None' = None):
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
            self.globals[cls_name] = cls

        return self._with_new_block('except', statement)

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
        func_code = '\n'.join(self.current_function["body"])
        self.functions[self.current_function["name"]] = ({"args": self.current_function["args"],
                                                          "return_type": self.current_function["return_type"],
                                                          "code": func_code})
        self.current_function = None  # Reset current function

    def create_functions(self, *, globals=None, locals=None):
        """Create functions by compiling the code."""
        # Note that we may mutate locals. Callers beware!
        # The only callers are internal to this module, so no
        # worries about external callers.
        if locals is None:  # pragma: no cover
            locals = {}

        # Compute the text of the entire function.
        # txt = f' def {name}({args}){return_annotation}:\n{body}'

        # Build the function code for all functions
        # Free variables in exec are resolved in the global namespace.
        # The global namespace we have is user-provided, so we can't modify it for
        # our purposes. So we put the things we need into locals and introduce a
        # scope to allow the function we're creating to close over them.

        name_to_func_code = {}

        for name, func in self.functions.items():
            args = ','.join(func['args'])
            body = func['code']
            return_type = func['return_type']

            return_annotation = ''
            if return_type is not MISSING:
                locals[f'__dataclass_{name}_return_type__'] = return_type
                return_annotation = f'->__dataclass_{name}_return_type__'

            name_to_func_code[name] = f'def {name}({args}){return_annotation}:\n{body}'

        local_vars = ', '.join(locals.keys())

        txt = '\n'.join([
            f"def __create_{name}_fn__({local_vars}):\n"
            f" {code}\n"
            f" return {name}"
            for name, code in name_to_func_code.items()
        ])

        # Print the generated code for debugging
        # logging.debug(f"Generated function code:\n{all_func_code}")
        LOG.debug(f"Generated function code:\n{txt}")

        ns = {}
        exec(txt, globals | self.globals, ns)

        final_ns = self.namespace = {
            name: ns[f'__create_{name}_fn__'](**locals)
            for name in name_to_func_code
        }

        # Print namespace for debugging
        LOG.debug(f"Namespace after function compilation: {self.namespace}")

        return final_ns
