from pathlib import Path
from typing import Literal, Optional

from core.colortools import Log
from core.tokens import BASE_DIR, Position

# Define all types of security prompts
SecurityPromptType = Literal["pyapi_access", "disk_access", "network_access"]
type_messages: dict[str, str] = {
    "pyapi_access": "This program is attempting to use the Python API",
    "disk_access": "This program is attempting to access the disk",
    "network_access": "This program is attempting to access the network",
}

# List of allowed actions (used during code execution)
allowed: dict[str, bool] = {}

# The interpreter's own stdlib/ directory -- code that lives here is part of
# the interpreter's trusted internals, not user-supplied.
_STDLIB_DIR = (BASE_DIR / "stdlib").resolve()


# !!! Only used for tests !!!
def allow_all_permissions() -> None:
    allowed["pyapi_access"] = True
    allowed["disk_access"] = True
    allowed["network_access"] = True


def is_trusted_source(fn: Optional[str]) -> bool:
    """Whether `fn` is a source file the interpreter ships itself (stdlib/), as
    opposed to a user-supplied script or module.

    This is a location check, not a content check -- there is no in-language
    keyword or function a script can write to grant itself this trust. Being
    physically located under the interpreter's own stdlib/ directory is the
    only thing that counts, and a script can't place a file there without
    already having write access to the interpreter's own installation.
    """
    if not fn:
        return False
    try:
        return Path(fn).resolve().is_relative_to(_STDLIB_DIR)
    except (OSError, ValueError):
        return False


def security_prompt(type: SecurityPromptType, pos: Optional[Position] = None) -> None:
    # If action already allowed, continue
    if type in allowed:
        return
    # Trusted internal call sites (the interpreter's own stdlib) never prompt.
    if pos is not None and is_trusted_source(pos.fn):
        return
    # Log the message and get a y/n prompt by user
    print(f"{Log.deep_warning(f'[{type.upper()}]')} {Log.deep_info(type_messages[type], True)}. Continue execution?")
    print(f"{Log.deep_purple('[Y/n] -> ')}", end="")
    # If user agreed
    if input().lower() == "y":
        # Add action to allowed list
        allowed[type] = True
        return
    # Exit program
    print("Permission denied by user.")
    exit(1)
    return
