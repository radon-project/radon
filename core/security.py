from typing import Literal

from core.colortools import Log

# Define all types of security prompts
SecurityPromptType = Literal["pyapi_access", "disk_access", "network_access"]
type_messages: dict[str, str] = {
    "pyapi_access": "This program is attempting to use the Python API",
    "disk_access": "This program is attempting to access the disk",
    "network_access": "This program is attempting to access the network",
}

# List of allowed actions (used during code execution)
allowed: dict[str, bool] = {}


# !!! Only used for tests !!!
def allow_all_permissions() -> None:
    allowed["pyapi_access"] = True
    allowed["disk_access"] = True
    allowed["network_access"] = True


def security_prompt(type: SecurityPromptType) -> None:
    # If action already allowed, continue
    if type in allowed:
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
