from dataclasses import MISSING

from ..errors import ParseError


def safe_get(data, path, default=MISSING, raise_=True):
    current_data = data
    p = path  # to avoid "unbound local variable" warnings

    try:
        for p in path:
            current_data = current_data[p]

        return current_data

    # IndexError -
    #   raised when `data` is a `list`, and we access an index that is "out of bounds"
    # KeyError -
    #   raised when `data` is a `dict`, and we access a key that is not present
    # AttributeError -
    #   raised when `data` is an invalid type, such as a `None`
    except (IndexError, KeyError, AttributeError) as e:
        if raise_ and default is MISSING:
            raise _format_err(e, current_data, path, p) from None
        return default

    # TypeError -
    #   raised when `data` is a `list`, but we try to use it like a `dict`
    except TypeError:
        e = TypeError('Invalid path')
        raise _format_err(e, current_data, path, p, True) from None


def v1_safe_get(data, path, raise_):
    current_data = data

    try:
        for p in path:
            current_data = current_data[p]

        return current_data

    # IndexError -
    #   raised when `data` is a `list`, and we access an index that is "out of bounds"
    # KeyError -
    #   raised when `data` is a `dict`, and we access a key that is not present
    # AttributeError -
    #   raised when `data` is an invalid type, such as a `None`
    except (IndexError, KeyError, AttributeError) as e:
        if raise_:
            p = locals().get('p', path)  # to suppress "unbound local variable"
            raise _format_err(e, current_data, path, p, True) from None

        return MISSING

    # TypeError -
    #   raised when `data` is a `list`, but we try to use it like a `dict`
    except TypeError:
        e = TypeError('Invalid path')
        p = locals().get('p', path)  # to suppress "unbound local variable"
        raise _format_err(e, current_data, path, p, True) from None


def _format_err(e, current_data, path, current_path, invalid_path=False):
    return ParseError(
        e, current_data, dict if invalid_path else None,
        path=' => '.join(repr(p) for p in path),
        current_path=repr(current_path),
    )


# What values are considered "truthy" when converting to a boolean type.
# noinspection SpellCheckingInspection
_TRUTHY_VALUES = frozenset(("True", "true"))

# What values are considered "falsy" when converting to a boolean type.
# noinspection SpellCheckingInspection
_FALSY_VALUES = frozenset(("False", "false"))


# Valid starting separators in our custom "object path",
# for example `a.b[c].d.[-1]` has 5 start separators.
_START_SEP = frozenset(('.', '['))


def split_object_path(_input):
    res = []
    s = ""
    start_new = True
    in_literal = False

    parsed_string_literal = False

    in_braces = False

    escape_next_quote = False
    quote_char = None
    possible_number = False

    for c in _input:
        if c in _START_SEP:
            if in_literal:
                s += c
            else:
                if c == '.':
                    # A period within braces [xxx] OR within a string "xxx",
                    # should be captured.
                    if in_braces:
                        s += c
                        continue
                    in_braces = False
                else:
                    in_braces = True

                start_new = True
                if s:
                    if possible_number:
                        possible_number = False
                        try:
                            num = int(s)
                            res.append(num)
                        except ValueError:
                            try:
                                num = float(s)
                                res.append(num)
                            except ValueError:
                                res.append(s)
                    elif parsed_string_literal:
                        parsed_string_literal = False
                        res.append(s)
                    else:
                        if s in _TRUTHY_VALUES:
                            res.append(True)
                        elif s in _FALSY_VALUES:
                            res.append(False)
                        else:
                            res.append(s)

                    s = ""
        elif c == '\\' and in_literal:
            escape_next_quote = True
        elif escape_next_quote:
            if c != quote_char:
                # It was not an escape character after all!
                s += '\\'
            # Capture escaped character
            s += c
            escape_next_quote = False
        elif c == quote_char:
            in_literal = False
            quote_char = None
            parsed_string_literal = True
        elif c in {'"', "'"} and start_new:
            start_new = False
            in_literal = True
            quote_char = c
        elif (c in {'+', '-'} or c.isdigit()) and start_new:
            start_new = False
            possible_number = True
            s += c
        elif start_new:
            start_new = False
            s += c
        elif c == ']':
            if in_literal:
                s += c
            else:
                in_braces = False
        else:
            s += c

    if s:
        if possible_number:
            try:
                num = int(s)
                res.append(num)
            except ValueError:
                try:
                    num = float(s)
                    res.append(num)
                except ValueError:
                    res.append(s)
        elif parsed_string_literal:
            res.append(s)
        else:
            if s in _TRUTHY_VALUES:
                res.append(True)
            elif s in _FALSY_VALUES:
                res.append(False)
            else:
                res.append(s)

    return res
