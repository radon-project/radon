from __future__ import annotations

from enum import Enum


class BackgroundColor(Enum):
    """Background color"""

    BLACK = "\033[40m"
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    PURPLE = "\033[45m"
    CYAN = "\033[46m"
    WHITE = "\033[47m"
    ORANGE = "\033[48;5;208m"
    TOMATO = "\033[48;5;203m"
    PINK = "\033[48;5;205m"
    VIOLET = "\033[48;5;99m"
    GRAY = "\033[48;5;240m"
    DARKGREEN = "\033[48;5;22m"
    GOLD = "\033[48;5;220m"
    YELLOWGREEN = "\033[48;5;154m"
    LIGHTGRAY = "\033[48;5;250m"
    LIGHTBLUE = "\033[48;5;153m"
    LIGHTGREEN = "\033[48;5;154m"
    LIGHTYELLOW = "\033[48;5;227m"
    LIGHTPURPLE = "\033[48;5;200m"
    LIGHTCYAN = "\033[48;5;159m"
    LIGHTWHITE = "\033[48;5;255m"
    LIGHTSEAGREEN = "\033[48;5;37m"
    LIGHTRED = "\033[48;5;203m"
    LIGHTPINK = "\033[48;5;217m"
    LIGHTORANGE = "\033[48;5;208m"
    LIGHTVIOLET = "\033[48;5;99m"
    TRANSPARENT = "\033[49m"


class ForegroundColor(Enum):
    """Foreground color"""

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    PURPLE = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[38m"
    ORANGE = "\033[38;5;208m"
    TOMATO = "\033[38;5;203m"
    PINK = "\033[38;5;205m"
    VIOLET = "\033[38;5;99m"
    GRAY = "\033[38;5;244m"
    DARKGREEN = "\033[38;5;22m"
    GOLD = "\033[38;5;220m"
    YELLOWGREEN = "\033[38;5;154m"
    LIGHTGRAY = "\033[38;5;250m"
    LIGHTBLUE = "\033[38;5;117m"
    LIGHTGREEN = "\033[38;5;118m"
    LIGHTYELLOW = "\033[38;5;226m"
    LIGHTPURPLE = "\033[38;5;141m"
    LIGHTCYAN = "\033[38;5;123m"
    LIGHTWHITE = "\033[38;5;255m"
    LIGHTSEAGREEN = "\033[38;5;37m"
    LIGHTRED = "\033[38;5;203m"
    LIGHTPINK = "\033[38;5;217m"
    LIGHTORANGE = "\033[38;5;208m"
    LIGHTVIOLET = "\033[38;5;99m"
    TRANSPARENT = "\033[0m"


class Style(Enum):
    """Style"""

    BLINK = "\033[5m"
    BOLD = "\033[1m"
    CLEAR = "\033[2;0m"
    CONCEALED = "\033[8m"
    INVISIBLE = "\033[8m"
    ITALIC = "\x1b[3m"
    OVERLINE = "\033[53m"
    REVERSE = "\033[7m"
    STRIKE = "\033[9m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    UNDERLINE_SOLID = "\033[4m"
    UNDERLINE_WAVY = "\033[4:3m" + "\033[58;2;104m"
    UNDERLINE_DOTTED = "\033[4;2m"
    UNDERLINE_DOUBLE = "\033[21m"
    UNDERLINE_DASHED = "\033[4;3m"


class Log:
    @staticmethod
    def deep_error(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.RED.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def deep_warning(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.YELLOW.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def deep_info(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.BLUE.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def deep_success(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.GREEN.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def light_error(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.LIGHTRED.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def light_warning(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.LIGHTORANGE.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def light_info(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.LIGHTBLUE.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def light_success(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.LIGHTGREEN.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def deep_purple(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.PURPLE.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def light_purple(text: str, bold: bool = False) -> str:
        value = f"{ForegroundColor.LIGHTORANGE.value}{text}{ForegroundColor.TRANSPARENT.value}"
        if bold:
            return f"{Style.BOLD.value}{value}"
        return value

    @staticmethod
    def underline(text: str, bold: bool = False) -> str:
        return f"{Style.UNDERLINE.value}{text}{Style.CLEAR.value}"

    @staticmethod
    def italic(text: str, bold: bool = False) -> str:
        return f"{Style.ITALIC.value}{text}{Style.CLEAR.value}"

    @staticmethod
    def strike(text: str, bold: bool = False) -> str:
        return f"{Style.STRIKE.value}{text}{Style.CLEAR.value}"

    @staticmethod
    def reverse(text: str, bold: bool = False) -> str:
        return f"{Style.REVERSE.value}{text}{Style.CLEAR.value}"

    @staticmethod
    def blink(text: str, bold: bool = False) -> str:
        return f"{Style.BLINK.value}{text}{Style.CLEAR.value}"
