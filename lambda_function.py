"""
Alexa Skill Lambda Function for Roku Voice Assistant

This Lambda function handles Alexa voice commands to control a Roku device
via the Roku External Control Protocol (ECP).

CONFIGURATION REQUIRED:
1. Set ROKU_IP_ADDRESS below to your Roku device's IP address
   - Find your Roku IP: Settings → Network → About on your Roku device
2. Deploy this function to AWS Lambda
3. Link it to your Alexa Skill
4. Ensure your Roku has "Control by mobile apps" enabled
   - Settings → System → Advanced system settings → Control by mobile apps

Dependencies are managed via requirements.txt and must be included in the
deployment package.
"""

import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response
import requests

# Set up logging for the skill
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Roku Configuration ---
# IMPORTANT: Replace with your Roku device's IP address
# In production, consider using environment variables or AWS Systems Manager Parameter Store
ROKU_IP_ADDRESS = "YOUR_ROKU_IP_ADDRESS"  # Example: "192.0.2.100"
ROKU_PORT = 8060

# Roku App ID Catalog
# These app IDs are standard across most Roku devices
APP_CATALOG = {
    "netflix": {
        "id": "12",
        "display_name": "Netflix",
    },
    "hulu": {
        "id": "2285",
        "display_name": "Hulu",
    },
    "youtube": {
        "id": "837",
        "display_name": "YouTube",
    },
    "prime video": {
        "id": "13",
        "display_name": "Prime Video",
    },
    "amazon prime": {
        "id": "13",
        "display_name": "Prime Video",
    },
    "disney plus": {
        "id": "291097",
        "display_name": "Disney+",
    },
    "disney+": {
        "id": "291097",
        "display_name": "Disney+",
    },
    "hbo max": {
        "id": "61322",
        "display_name": "HBO Max",
    },
    "max": {
        "id": "61322",
        "display_name": "HBO Max",
    },
}

# --- Roku Interaction Functions ---

def send_roku_command(command_path, method="POST", params=None):
    """Sends a command to the Roku device via ECP."""
    # Check if ROKU_IP_ADDRESS is still the placeholder
    if ROKU_IP_ADDRESS == "YOUR_ROKU_IP_ADDRESS":
        logger.error("ROKU_IP_ADDRESS is not configured. Please set your Roku device's IP address.")
        return False, "Roku not configured. Please set ROKU_IP_ADDRESS in lambda_function.py."
    
    url = f"http://{ROKU_IP_ADDRESS}:{ROKU_PORT}/{command_path}"
    try:
        if method == "POST":
            response = requests.post(url, data="" if not params else params, timeout=5)
        else:  # GET
            response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        logger.info(f"Roku command '{command_path}' successful")
        return True, "Command sent successfully"
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Roku command '{command_path}': {e}")
        return False, "Connection error"

def control_roku_keypress(key):
    """Simulates a keypress on the Roku remote."""
    success, message = send_roku_command(f"keypress/{key}")
    return f"Sent {key} command" if success else "Failed to send command"

def control_roku_play_pause():
    """Simulates play/pause action on Roku."""
    return control_roku_keypress("Play")

def control_roku_volume_up():
    """Simulates volume up action on Roku."""
    return control_roku_keypress("VolumeUp")

def control_roku_volume_down():
    """Simulates volume down action on Roku."""
    return control_roku_keypress("VolumeDown")

def control_roku_mute():
    """Simulates mute action on Roku."""
    return control_roku_keypress("VolumeMute")

def control_roku_home():
    """Goes to the Roku home screen."""
    return control_roku_keypress("Home")

def control_roku_back():
    """Simulates back button."""
    return control_roku_keypress("Back")

def control_roku_select():
    """Simulates select/OK button."""
    return control_roku_keypress("Select")

def control_roku_rewind():
    """Simulates rewind."""
    return control_roku_keypress("Rev")

def control_roku_fast_forward():
    """Simulates fast forward."""
    return control_roku_keypress("Fwd")

def control_roku_left():
    """Simulates left directional."""
    return control_roku_keypress("Left")

def control_roku_right():
    """Simulates right directional."""
    return control_roku_keypress("Right")

def control_roku_up():
    """Simulates up directional."""
    return control_roku_keypress("Up")

def control_roku_down():
    """Simulates down directional."""
    return control_roku_keypress("Down")

def get_roku_app_id_for_name(app_name):
    """
    Retrieves the Roku app ID for a given app name.
    Uses the APP_CATALOG dictionary for known apps.
    
    Args:
        app_name: Name of the app (case-insensitive)
    
    Returns:
        str: App ID if found, None otherwise
    """
    normalized_name = app_name.lower().strip()
    app_info = APP_CATALOG.get(normalized_name)
    return app_info["id"] if app_info else None

def launch_app_on_roku(app_name):
    """Launches an app on Roku by name."""
    app_id = get_roku_app_id_for_name(app_name)
    
    if app_id:
        success, message = send_roku_command(f"launch/{app_id}")
        if success:
            return f"Launched {app_name}"
        else:
            return f"Failed to launch {app_name}"
    else:
        # Generate app list from APP_CATALOG display names
        unique_apps = sorted(set(info["display_name"] for info in APP_CATALOG.values()))
        app_list = ", ".join(unique_apps)
        return f"App '{app_name}' not found. Try {app_list}."

def control_roku_search(content_title):
    """
    Attempts to search for content on Roku.
    Note: Direct text search via ECP is limited. This opens the home screen
    as a fallback and notifies the user to search manually.
    """
    logger.info(f"Search requested for: {content_title}")
    # Roku's ECP doesn't have a universal search command
    # Best we can do is go to home and let the user search manually
    result = control_roku_home()
    if "Failed" in result:
        logger.warning(f"Failed to navigate home for search: {result}")
        return "Unable to navigate to home screen. Please check your Roku connection."
    return f"Please search for {content_title} manually from the Roku home screen"

# --- Alexa Skill Intent Handlers ---

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Welcome to your Roku Assistant! How can I help you?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class PlayContentIntentHandler(AbstractRequestHandler):
    """Handler for PlayContentIntent - plays content or launches apps."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("PlayContentIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        content_title = slots.get("ContentTitle")
        app_name = slots.get("App")
        
        content_title_value = content_title.value if content_title and content_title.value else None
        app_name_value = app_name.value if app_name and app_name.value else None

        if app_name_value:
            # Try to launch the app
            response_text = launch_app_on_roku(app_name_value)
            if content_title_value:
                # Do not trigger a global Roku search (which may press Home and exit the app)
                # after launching an app. Instead, give the user guidance to search inside the app.
                speak_output = (
                    f"{response_text}. "
                    f"Once {app_name_value} opens, use your Roku remote to search for "
                    f"{content_title_value}."
                )
            else:
                speak_output = response_text
        elif content_title_value:
            # Just search for the content using Roku's global search
            speak_output = control_roku_search(content_title_value)
        else:
            speak_output = "I need either an app name or content title to help you."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SearchContentIntentHandler(AbstractRequestHandler):
    """Handler for SearchContentIntent - searches for content."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SearchContentIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        content = slots.get("ContentTitle")
        content_title = content.value if content and content.value else None

        if content_title:
            response_text = control_roku_search(content_title)
            speak_output = f"Searching for {content_title}. {response_text}"
        else:
            speak_output = "What would you like me to search for?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class ControlPlaybackIntentHandler(AbstractRequestHandler):
    """Handler for ControlPlaybackIntent - controls playback and volume."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ControlPlaybackIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        action = slots.get("Action")
        action_value = action.value.lower() if action and action.value else ""

        speak_output = "I'm not sure what you want me to do."

        if "play" in action_value or "pause" in action_value:
            response_text = control_roku_play_pause()
            speak_output = f"Okay. {response_text}"
        elif "volume up" in action_value or "louder" in action_value:
            response_text = control_roku_volume_up()
            speak_output = f"Okay. {response_text}"
        elif "volume down" in action_value or "quieter" in action_value:
            response_text = control_roku_volume_down()
            speak_output = f"Okay. {response_text}"
        elif "mute" in action_value:
            response_text = control_roku_mute()
            speak_output = f"Okay. {response_text}"
        elif "rewind" in action_value:
            response_text = control_roku_rewind()
            speak_output = f"Okay. {response_text}"
        elif "forward" in action_value:
            response_text = control_roku_fast_forward()
            speak_output = f"Okay. {response_text}"
        elif "home" in action_value:
            response_text = control_roku_home()
            speak_output = f"Okay. {response_text}"
        elif "back" in action_value:
            response_text = control_roku_back()
            speak_output = f"Okay. {response_text}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class AppControlIntentHandler(AbstractRequestHandler):
    """Handler for launching specific apps."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AppControlIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        app = slots.get("App")
        app_name = app.value if app and app.value else None

        if app_name:
            response_text = launch_app_on_roku(app_name)
            speak_output = f"Okay. {response_text}"
        else:
            speak_output = "Which app would you like me to launch?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = (
            "You can ask me to launch apps like Netflix or Hulu, "
            "control playback with play or pause, "
            "adjust volume, "
            "or navigate with commands like home or back. "
            "What would you like to do?"
        )
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelAndStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = "Goodbye!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """
    This handler will be used for any utterances not caught by other
    handlers and is intended to be a general fallback.
    """
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Sorry, I don't know that one. Please try again."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # Any cleanup logic goes here.
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """
    The intent reflector is used for testing and debugging.
    It simply repeats the intent the user said. You can remove this if
    you are not interested in that functionality.
    """
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = f"You just triggered {intent_name}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors."""
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# --- Skill Builder Initialization ---
sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(PlayContentIntentHandler())
sb.add_request_handler(SearchContentIntentHandler())
sb.add_request_handler(ControlPlaybackIntentHandler())
sb.add_request_handler(AppControlIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelAndStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # Place after all other intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
