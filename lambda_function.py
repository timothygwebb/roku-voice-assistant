import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

# Set up logging for the skill
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Roku Interaction Logic (
import requests # Make sure 'requests' library is installed in your deployment package

# Set up logging for the skill
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Roku Interaction Logic ---
# Adapt your existing Roku control functions to work
# within these intent handlers.
# Replace with your Roku device's IP address.
# In a real-world scenario, you'd likely want to store this securely,
# perhaps in a database or a configuration service, and allow the user
# to associate their Roku device with the Alexa skill.
ROKU_IP_ADDRESS = "YOUR_ROKU_IP_ADDRESS"
ROKU_PORT = 8060

def send_roku_command(command_path, method="POST", params=None):
    """Sends a command to the Roku device via ECP."""
    url = f"http://{ROKU_IP_ADDRESS}:{ROKU_PORT}/{command_path}"
    try:
        if method == "POST":
            response = requests.post(url, data="" if not params else params)
        else: # Assuming GET for other methods
            response = requests.get(url, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors
        logger.info(f"Roku command '{command_path}' successful. Response: {response.text}")
        return True, response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Roku command '{command_path}': {e}")
        return False, str(e)

def control_roku_keypress(key):
    """Simulates a keypress on the Roku remote."""
    success, message = send_roku_command(f"keypress/{key}")
    if success:
        return f"Sent {key} keypress to Roku."
    else:
        return f"Failed to send {key} keypress: {message}"

def control_roku_play_pause():
    """Simulates play/pause action on Roku."""
    # The 'Play' key usually toggles play/pause depending on context
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

def control_roku_search(content_title):
    """Searches for content on Roku by opening the search screen and sending keypresses."""
    # Note: Roku's native search functionality might be limited or require specific app support.
    # This example sends individual keypresses to simulate typing.
    # More advanced search might involve launching the built-in Roku search app first,
    # then sending the text. Or, in some cases, deep linking directly if the app supports it.
    # First, navigate to the Home screen (or potentially search app)
    response_home = control_roku_home()
    if "Failed" in response_home:
        return f"Failed to go home before searching: {response_home}"
    
    # Wait a moment for the Roku to respond (this is a simple simulation, may need refinement)
    # import time
    # time.sleep(1) 
    
    # Simulate pressing the 'Search' button (if available or accessible via home screen)
    # The 'Search' key might not be directly exposed via ECP, you might need to
    # navigate using arrow keys to a search icon if a dedicated search keypress doesn't work.
    # For a robust solution, you might need to launch a specific app and then send text.
    
    # For now, let's assume a generic search which might involve navigating
    # to the search screen after going home.
    # More practical approach: if you know the app ID of the search app, you could launch it.
    
    # A simple approach for generic search, assuming the content title can be typed
    # without navigating first (unlikely for most apps, more for global search).
    
    # Consider using 'Search' keypress if your Roku has it directly accessible via ECP
    # For now, we'll just simulate typing on the current screen.
    
    # Let's assume we're on the global search screen (which can be accessed via a specific sequence of presses)
    # A more reliable method would be to find the app ID of the global search app (if it exists).

    # For now, we'll try sending the characters.
    # This might require prior navigation to a text input field.
    
    # If the user is expected to be on the search screen, you can type.
    # The Roku 'Search' ECP command was deprecated, but you can simulate
    # typing using 'keypress' events for alphanumeric characters.
    
    # Example: Simulating typing "Die Hard"
    # This is a simplified approach and might not work universally without prior navigation.
    # You would need to ensure the Roku is in a state where typing is possible (e.g., on a search screen).
    
    speak_output = f"Attempting to search for {content_title}. Note: This relies on Roku being on a search input screen or capable of receiving direct text input, which might not always be the case."
    
    for char in content_title:
        # Roku ECP keypress for characters needs to be handled carefully.
        # Often it's 'keypress/Lit_<character>' or simply 'keypress/<character>'
        # depending on the Roku OS version and context.
        # This example uses a generic approach; you might need to adapt.
        key_to_send = f"Lit_{char.upper()}" if char.isalnum() else char # Simple guess for alphanumeric
        control_roku_keypress(key_to_send) 
        # Add a small delay if needed: time.sleep(0.1)

    # After typing, simulate pressing 'Enter' or 'Search' to submit
    control_roku_keypress("Select") # Assuming 'Select' acts as Enter
    
    return f"Attempting to search for {content_title}. Check your Roku screen."


def launch_app_on_roku(app_name):
    """Launches an app on Roku."""
    # You'll need a mapping of app names (like "Netflix") to their Roku App IDs.
    # You can get a list of installed apps and their IDs using /query/apps ECP command.
    # Example app_ids_mapping = {"Netflix": "12345", "Hulu": "67890"}
    
    # For demonstration, let's assume you have a way to get the App ID.
    # In a real skill, you might query the Roku, or have a pre-defined list.
    
    # Placeholder: Replace with actual App ID lookup
    app_id = get_roku_app_id_for_name(app_name)

    if app_id:
        success, message = send_roku_command(f"launch/{app_id}")
        if success:
            return f"Launched {app_name} on Roku."
        else:
            return f"Failed to launch {app_name}: {message}"
    else:
        return f"Could not find Roku app ID for {app_name}. Please specify a valid app."

def get_roku_app_id_for_name(app_name):
    """
    Retrieves the Roku app ID for a given app name.
    This would involve querying the Roku device for its installed apps.
    This is a placeholder; you'd need to implement the actual ECP query for /query/apps
    and parse the XML response to find the matching app ID.
    """
    # Example of a hardcoded mapping (for testing)
    app_name_to_id_map = {
        "netflix": "12345", # Replace with actual app IDs
        "hulu": "67890",
        "youtube": "54321",
        "prime video": "98765",
        "disney plus": "11223"
    }
    return app_name_to_id_map.get(app_name.lower())

# You can add more Roku interaction functions here as needed
# for other commands like rewind, fast forward, directional keys, etc.

# Example:
def control_roku_rewind():
    return control_roku_keypress("Rev")

def control_roku_fast_forward():
    return control_roku_keypress("Fwd")

def control_roku_right():
    return control_roku_keypress("Right")

def control_roku_left():
    return control_roku_keypress("Left")

def control_roku_select():
    return control_roku_keypress("Select")

def control_roku_back():
    return control_roku_keypress("Back")

# Remember to ensure your Roku device has "Control by mobile apps" enabled
# in Settings > System > Advanced system settings.
# You'll need to adapt your existing Roku control functions to work
# within these intent handlers.
class PlayContentIntentHandler(AbstractRequestHandler):
    # ... (can_handle and other setup)
    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        content_title = slots["ContentTitle"].value
        app_name = slots["App"].value

        # Call your Roku control function
        # Adapt this based on whether you're launching an app first, then searching,
        # or relying on a more direct Roku search experience if feasible.
        # This example prioritizes search as a fallback.
        if app_name and content_title:
            response_text_launch = launch_app_on_roku(app_name)
            if "Failed" not in response_text_launch:
                # Give the Roku a moment to launch the app
                # time.sleep(2) # You might need a small delay here
                response_text_search = control_roku_search(content_title)
                speak_output = f"{response_text_launch} Then, {response_text_search}"
            else:
                speak_output = response_text_launch
        elif content_title:
            response_text_search = control_roku_search(content_title)
            speak_output = response_text_search
        else:
            speak_output = "I need a title to play or search for."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

def control_roku_play_pause():
    """Simulates play/pause action on Roku."""
    # Replace with your actual Roku control code (e.g., sending HTTP requests)
    logger.info("Simulating Roku Play/Pause")
    return "Playing or pausing Roku."

def control_roku_volume_up():
    """Simulates volume up action on Roku."""
    # Replace with your actual Roku control code
    logger.info("Simulating Roku Volume Up")
    return "Turning Roku volume up."

def control_roku_search(content_title):
    """Searches for content on Roku."""
    # Replace with your actual Roku search logic
    logger.info(f"Searching Roku for: {content_title}")
    return f"Searching Roku for {content_title}."

def launch_app_on_roku(app_name):
    """Launches an app on Roku."""
    # Replace with your actual Roku app launch logic
    logger.info(f"Launching app: {app_name}")
    return f"Launching {app_name} on Roku."

# --- Alexa Skill Logic ---

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
    """Handler for PlayContentIntent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("PlayContentIntent")(handler_input)

    def handle(self, handler_input):
        # Extract content title and app name from slots
        slots = handler_input.request_envelope.request.intent.slots
        content_title = slots["ContentTitle"].value if "ContentTitle" in slots and slots["ContentTitle"].value else "something"
        app_name = slots["App"].value if "App" in slots and slots["App"].value else "Roku"

        # Call your Roku control function
        response_text = control_roku_search(content_title) # Using search as an example

        speak_output = f"Okay, trying to play {content_title} on {app_name}. {response_text}"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SearchContentIntentHandler(AbstractRequestHandler):
    """Handler for SearchContentIntent."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("SearchContentIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        content_title = slots["ContentTitle"].value if "ContentTitle" in slots and slots["ContentTitle"].value else "something"

        response_text = control_roku_search(content_title)

        speak_output = f"Searching for {content_title} on Roku. {response_text}"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class ControlPlaybackIntentHandler(AbstractRequestHandler):
    """Handler for ControlPlaybackIntent (e.g., play/pause, volume)."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ControlPlaybackIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        action = slots["Action"].value if "Action" in slots and slots["Action"].value else ""

        speak_output = "I'm not sure what control action you want me to perform."

        if action:
            if "play" in action or "pause" in action:
                response_text = control_roku_play_pause()
                speak_output = f"Okay. {response_text}"
            elif "volume up" in action:
                response_text = control_roku_volume_up()
                speak_output = f"Okay. {response_text}"
            else:
                speak_output = "I can only play, pause, or adjust volume for now."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class AppControlIntentHandler(AbstractRequestHandler):
    """Handler for launching apps."""
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("AppControlIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        app_name = slots["App"].value if "App" in slots and slots["App"].value else ""

        speak_output = "Which app would you like me to launch?"

        if app_name:
            response_text = launch_app_on_roku(app_name)
            speak_output = f"Okay. {response_text}"

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
        speak_output = "You can ask me to play content, search for titles, or control playback. How can I help?"
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
