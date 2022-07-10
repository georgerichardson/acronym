import re


def camel_to_snake(text: str) -> str:
    """Converts a string in lowerCamelCase or upperCamelCase to snake_case."""
    snakey = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", snakey).lower()
