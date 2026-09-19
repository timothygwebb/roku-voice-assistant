# mobile_app/voice_commands.py

import json
import os
import requests
from typing import Callable, Dict, Any, List

ROKU_IP = "192.168.68.50"  # TODO: your Roku IP
ROKU_PORT = 8060

CommandFn = Callable[[], None]


def roku_keypress(key: str) -> None:
    url = f"http://{ROKU_IP}:{ROKU_PORT}/keypress/{key}"
    requests.post(url)


def roku_launch(channel_id: str) -> None:
    url = f"http://{ROKU_IP}:{ROKU_PORT}/launch/{channel_id}"
    requests.post(url)


def roku_text_entry(text: str) -> None:
    # Simple Roku text entry via Lit_ keys
    for ch in text:
        if ch == " ":
            roku_keypress("Space")
        else:
            url = f"http://{ROKU_IP}:{ROKU_PORT}/keypress/Lit_{ch}"
            requests.post(url)


def roku_go_to_settings() -> None:
    # Example smart navigation: go home, then navigate to settings
    roku_keypress("Home")
    # You can tune these steps to your Roku layout
    roku_keypress("Right")
    roku_keypress("Right")
    roku_keypress("Down")
    roku_keypress("Select")


def roku_captions_on() -> None:
    # Example: open options and toggle captions
    roku_keypress("Info")
    roku_keypress("Down")
    roku_keypress("Select")


COMMANDS: Dict[str, CommandFn] = {}
ALIASES: Dict[str, str] = {}
SMART_COMMANDS: Dict[str, CommandFn] = {}


def _load_commands_from_config() -> None:
    global COMMANDS, ALIASES, SMART_COMMANDS

    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "commands.json")

    with open(config_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    commands: List[Dict[str, Any]] = data.get("commands", [])

    for cmd in commands:
        cmd_id = cmd["id"]
        roku_key = cmd.get("rokuKey")
        smart = cmd.get("smart")
        voice_phrases = cmd.get("voice", [])

        if roku_key:
            COMMANDS[cmd_id] = (lambda key=roku_key: roku_keypress(key))

        if smart == "go_to_settings":
            SMART_COMMANDS[cmd_id] = roku_go_to_settings
        elif smart == "captions_on":
            SMART_COMMANDS[cmd_id] = roku_captions_on

        for phrase in voice_phrases:
            ALIASES[phrase.lower()] = cmd_id


_load_commands_from_config()


def normalize(text: str) -> str:
    return text.lower().strip()


def resolve_command(text: str) -> CommandFn | None:
    text = normalize(text)

    if text in COMMANDS:
        return COMMANDS[text]

    if text in SMART_COMMANDS:
        return SMART_COMMANDS[text]

    if text in ALIASES:
        cmd_id = ALIASES[text]
        if cmd_id in COMMANDS:
            return COMMANDS[cmd_id]
        if cmd_id in SMART_COMMANDS:
            return SMART_COMMANDS[cmd_id]

    for phrase, cmd_id in ALIASES.items():
        if phrase in text:
            if cmd_id in COMMANDS:
                return COMMANDS[cmd_id]
            if cmd_id in SMART_COMMANDS:
                return SMART_COMMANDS[cmd_id]

    return None


def execute_command(text: str) -> bool:
    cmd = resolve_command(text)
    if not cmd:
        return False
    cmd()
    return True


def smart_navigate(text: str) -> bool:
    text = normalize(text)

    if execute_command(text):
        return True

    # Example: "search for X"
    if text.startswith("search for "):
        query = text.replace("search for ", "", 1)
        roku_keypress("Search")
        roku_text_entry(query)
        return True

    return False
