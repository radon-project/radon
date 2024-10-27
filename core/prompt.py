from typing import Literal
from core.colortools import Log

# Define all types of security prompts
SecurityPromptType = Literal["unsafe_code", "disk_read", "web_requests"]
type_messages: dict[str, str] = {
    "unsafe_code": "This program is attempting to execute potentially unsafe python code",
    "disk_read": "This program is attempting to access the filesystem",
    "web_requests": "This program is attempting to invoke web requests",
}

# List of allowed actions (used during code execution)
allowed: dict[str, bool] = {}


def security_prompt(type: SecurityPromptType) -> None:
    # If action already allowed, continue
    if type in allowed:
        return
    # Log the message and get a y/n prompt by user
    print(f"{Log.deep_warning(f"[{type.upper()}]")} {Log.deep_info(type_messages[type], True)}. Continue execution?")
    print(f"{Log.deep_purple("[Y/n] -> ")}", end="")
    # If user agreed
    if input().lower() == "y":
        # Add action to allowed list
        allowed[type] = True
        return
    # Exit program
    print("Permission denied by user.")
    exit(1)
    return
