# mobile_app/voice_commands.py

import requests
from typing import Callable, Dict

# TODO: Replace with your actual Roku IP
ROKU_IP = "192.168.68.50"
ROKU_PORT = 8060


def roku_keypress(key: str) -> None:
    url = f"http://{ROKU_IP}:{ROKU_PORT}/keypress/{key}"
    requests.post(url)


def roku_launch(channel_id: str) -> None:
    url = f"http://{ROKU_IP}:{ROKU_PORT}/launch/{channel_id}"
    requests.post(url)


def roku_search(text: str) -> None:
    roku_keypress("Search")
    # TODO: Add text entry support
    pass


CommandFn = Callable[[], None]

# -------------------------------
# MAIN COMMAND REGISTRY
# -------------------------------
COMMANDS: Dict[str, CommandFn] = {
    # D-Pad
    "up": lambda: roku_keypress("Up"),
    "down": lambda: roku_keypress("Down"),
    "left": lambda: roku_keypress("Left"),
    "right": lambda: roku_keypress("Right"),
    "ok": lambda: roku_keypress("Select"),
    "back": lambda: roku_keypress("Back"),

    # System
    "home": lambda: roku_keypress("Home"),
    "replay": lambda: roku_keypress("InstantReplay"),
    "info": lambda: roku_keypress("Info"),

    # Apps (replace IDs with your actual Roku channel IDs)
    "launch netflix": lambda: roku_launch("12"),
    "launch youtube": lambda: roku_launch("837"),
}

# -------------------------------
# NATURAL LANGUAGE ALIASES
# -------------------------------
ALIASES: Dict[str, str] = {
    "go up": "up",
    "scroll up": "up",
    "move up": "up",

    "go down": "down",
    "scroll down": "down",

    "go left": "left",
    "go right": "right",

    "select": "ok",
    "okay": "ok",
    "confirm": "ok",

    "go back": "back",

    "go home": "home",
    "main menu": "home",

    "open netflix": "launch netflix",
    "start netflix": "launch netflix",
    "open youtube": "launch youtube",
}


def normalize(text: str) -> str:
    return text.lower().strip()


def resolve_command(text: str) -> CommandFn | None:
    text = normalize(text)

    # direct match
    if text in COMMANDS:
        return COMMANDS[text]

    # alias match
    if text in ALIASES:
        return COMMANDS.get(ALIASES[text])

    # contains match
    for phrase, fn in COMMANDS.items():
        if phrase in text:
            return fn

    for phrase, canonical in ALIASES.items():
        if phrase in text:
            return COMMANDS.get(canonical)

    return None


def execute_command(text: str) -> bool:
    cmd = resolve_command(text)
    if not cmd:
        return False
    cmd()
    return True


# -------------------------------
# SMART NAVIGATION (AI HOOK)
# -------------------------------
def smart_navigate(text: str) -> bool:
    """
    Expand this later with AI-powered navigation.
    """
    if execute_command(text):
        return True

    # Example: "scroll down 5 times"
    if "scroll down" in text:
        times = 5
        for _ in range(times):
            roku_keypress("Down")
        return True

    return False
