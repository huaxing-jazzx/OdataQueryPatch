from typing import Any, Optional

from sly.lex import Token


class ODataException(Exception):
    """
    Base class for all exceptions in this library.
    """

    pass


class ODataSyntaxError(ODataException):
    """
    Base class for syntax errors.
    """

    pass


class TokenizingException(ODataSyntaxError):
    """
    Thrown when the lexer cannot tokenize the query.
    """

    def __init__(self, token: Token):
        self.token = token
        super().__init__(f"Failed to tokenize at: {token}")


class ParsingException(ODataSyntaxError):
    """
    Thrown when the parser cannot parse the query.
    """

    def __init__(self, token: Optional[Token], eof: bool = False):
        self.token = token
        self.eof = eof
        super().__init__(f"Failed to parse at: {token}")


class FunctionCallException(ODataException):
    """
    Base class for errors in function calls.
    """

    pass


class UnknownFunctionException(FunctionCallException):
    """
    Thrown when the parser encounters an undefined function call.
    """

    def __init__(self, function_name: str):
        self.function_name = function_name
        super().__init__(f"Unknown function: '{function_name}'")


class ArgumentCountException(FunctionCallException):
    """
    Thrown when the parser encounters a function called with a wrong number
    of arguments.
    """

    def __init__(
        self, function_name: str, exp_min_args: int, exp_max_args: int, given_args: int
    ):
        self.function_name = function_name
        self.exp_min_args = exp_min_args
        self.exp_max_args = exp_max_args
        self.n_args_given = given_args
        if exp_min_args != exp_max_args:
            super().__init__(
                f"Function '{function_name}' takes between {exp_min_args} and "
                f"{exp_max_args} arguments. {given_args} given."
            )
        else:
            super().__init__(
                f"Function '{function_name}' takes {exp_min_args} arguments. "
                f"{given_args} given."
            )


class UnsupportedFunctionException(FunctionCallException):
    """
    Thrown when a function is used that is not implemented yet.
    """

    def __init__(self, function_name: str):
        self.function_name = function_name
        super().__init__(f"Function '{function_name}' is not implemented yet.")


class ArgumentTypeException(FunctionCallException):
    """
    Thrown when a function is called with argument of the wrong type.
    """

    def __init__(
        self,
        function_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_type: Optional[str] = None,
    ):
        self.function_name = function_name
        self.expected_type = expected_type
        self.actual_type = actual_type

        if function_name:
            message = f"Unsupported or invalid type for function or operator '{function_name}'"
        else:
            message = "Invalid argument type for function or operator."
        if expected_type:
            message += f" Expected {expected_type}"
            if actual_type:
                message += f", got {actual_type}"

        super().__init__(message)


class TypeException(ODataException):
    """
    Thrown when doing an invalid operation on a value.
    E.g. `10 gt null` or `~date()`
    """

    def __init__(self, operation: str, value: str):
        self.operation = operation
        self.value = value
        super().__init__(f"Cannot apply '{operation}' to '{value}'")


class ValueException(ODataException):
    """
    Thrown when a value has an invalid value, such as an invalid datetime.
    """

    def __init__(self, value: Any):
        self.value = value
        super().__init__(f"Invalid value: {value}")


class InvalidFieldException(ODataException):
    """
    Thrown when a field mentioned in a query does not exist.
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Invalid field: {field_name}")


class EnumTypeException(ODataException):
    """
    Thrown when an invalid enum type is used in a query.
    """

    def __init__(self, enum_type: str, field_name: str):
        self.enum_type = enum_type
        self.field_name = field_name
        super().__init__(
            f"Invalid enum type '{enum_type}' for field '{field_name}'"
        )


class InvalidEnumValueException(ODataException):
    """
    Thrown when an invalid enum value is used in a query.
    """

    def __init__(self, enum_value: str, enum_type: str, valid_values: list):
        self.enum_value = enum_value
        self.enum_type = enum_type
        self.valid_values = valid_values
        super().__init__(
            f"Invalid enum value '{enum_value}' for type '{enum_type}'. "
            f"Valid values are: {', '.join(valid_values)}"
        )


class EnumComparisonException(ODataException):
    """
    Thrown when comparing an enum field with a non-enum value.
    """

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(
            f"Field '{field_name}' is an enum and must be compared with an enum value "
            f"using the syntax: EnumType'value'"
        )
