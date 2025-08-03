import secrets
import string


def generate_id(prefix: str, length: int = 16) -> str:
    """
    Generates a unique ID with a given prefix.
    Example: task-AbcDef123456
    """
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}-{random_part}"
