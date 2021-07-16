def _gen_formatter (code): return f"§{code}"

class Color:
    BLACK =         _gen_formatter ("0")
    DARK_BLUE =     _gen_formatter ("1")
    DARK_GREEN =    _gen_formatter ("2")
    DARK_CYAN =     _gen_formatter ("3")
    DARK_RED =      _gen_formatter ("4")
    PURPLE =        _gen_formatter ("5")
    GOLD =          _gen_formatter ("6")
    GRAY =          _gen_formatter ("7")
    DARK_GRAY =     _gen_formatter ("8")
    BLUE =          _gen_formatter ("9")
    BRIGHT_GREEN =  _gen_formatter ("a")
    CYAN =          _gen_formatter ("b")
    RED =           _gen_formatter ("c")
    PINK =          _gen_formatter ("d")
    YELLOW =        _gen_formatter ("e")
    WHITE =         _gen_formatter ("f")
class Style:
    RANDOM =        _gen_formatter ("k")
    BOLD =          _gen_formatter ("l")
    STRIKETHROUGH = _gen_formatter ("m")
    UNDERLINED =    _gen_formatter ("n")
    ITALIC =        _gen_formatter ("o")
RESET =             _gen_formatter ("r")

def chat_to_plain_str (chat: dict) -> str:
    out = chat ["text"]
    if "extra" in chat:
        for extra_component in chat ["extra"]: out += chat_to_plain_str (extra_component)
    for color_spec in "0123456789abcdefklmnor": out = out.replace (f"§{color_spec}", "")
    return out
