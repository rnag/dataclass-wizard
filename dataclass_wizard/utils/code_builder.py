import types
import logging
from dataclasses import MISSING
from timeit import timeit

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')


class CodeBuilder:
    __slots__ = (
        'functions',
        'namespace',
        'indent_level',
        'current_function',
    )

    def __init__(self):
        self.functions = {}
        self.namespace = {}
        self.indent_level = 0

    def __enter__(self):
        self.indent_level += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        indent_lvl = self.indent_level = self.indent_level - 1

        if not indent_lvl:
            self.finalize_function()

    def function(self, name: str, args: list, return_type=None) -> 'CodeBuilder':
        """Start a new function definition with optional return type."""
        self.current_function = {"name": name, "args": args, "body": [], "return_type": return_type}
        # self.add_line(f"def {name}({', '.join(args)})")  # Add function header
        if return_type:
            self.add_line(f"  # Return type: {return_type}")  # Log return type in the comments

        return self

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

    def increase_indent(self):
        """Increase indentation level for nested code."""
        self.indent_level += 1

    def decrease_indent(self):
        """Decrease indentation level."""
        if self.indent_level > 1:
            self.indent_level -= 1

    def finalize_function(self):
        """Finalize the function code and add to the list of functions."""
        # Add the function body and don't re-add the function definition
        func_code = '\n'.join(self.current_function["body"])
        self.functions[self.current_function["name"]] = ({"args": self.current_function["args"], "code": func_code})
        self.current_function = None  # Reset current function

    def compile_with_types(self, *, globals=None, locals=None,
                           return_type=MISSING
                           ):
        """Create functions by compiling the code."""
        # Note that we may mutate locals. Callers beware!
        # The only callers are internal to this module, so no
        # worries about external callers.
        if locals is None:
            locals = {}

        return_annotation = ''

        # if return_type is not MISSING:
        #     locals['__dataclass_return_type__'] = return_type
        #     return_annotation = '->__dataclass_return_type__'
        # args = ','.join(args)
        # body = '\n'.join(f'  {b}' for b in body)

        # Compute the text of the entire function.
        # txt = f' def {name}({args}){return_annotation}:\n{body}'

        # Build the function code for all functions
        # Free variables in exec are resolved in the global namespace.
        # The global namespace we have is user-provided, so we can't modify it for
        # our purposes. So we put the things we need into locals and introduce a
        # scope to allow the function we're creating to close over them.
        local_vars = ', '.join(locals.keys())
        all_func_code = '\n'.join(
            f"def __create_fn__({local_vars}):\n def {name}({','.join(func['args'])}):\n{func['code']}\n return {name}"
            for name, func in self.functions.items()
        )

        # Print the generated code for debugging
        # logging.debug(f"Generated function code:\n{all_func_code}")
        # print(f"Generated function code:\n{all_func_code}")

        ns = {}
        exec(all_func_code, globals, ns)

        # Print namespace for debugging
        # logging.debug(f"Namespace after function compilation: {self.namespace}")

        return ns['__create_fn__'](**locals)

        # txt = f"def __create_fn__({local_vars}):\n{txt}\n return {name}"
        # ns = {}
        # exec(txt, globals, ns)
        # return ns['__create_fn__'](**locals)





    def get_namespace(self):
        """Return the namespace containing all compiled functions."""
        return self.namespace
