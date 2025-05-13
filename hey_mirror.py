import time
from speech_recognition_module import SpeechRecognizer
from openai_nlp import NLPProcessor
from text_to_speech import TextToSpeech
import subprocess
class SmartMirror:
    def __init__(self, silence_threshold=6):
        """Initialize components and settings."""
        self.silence_threshold = silence_threshold
        self.recognizer = SpeechRecognizer()  # Speech Recognition Module
        self.nlp = NLPProcessor()  # OpenAI NLP Module
        self.tts = TextToSpeech()  # Text-to-Speech Module
    
    def handle_general_request(self, transcript):
        """Handle non-fashion related queries"""
        response = self.nlp.generate_response(transcript)
        self.tts.speak(response)
        return response
    def capture_image(self, image_path="/home/smart-mirror/Pictures/captured_image.jpg"):
        """Capture image using libcamera."""
        command = ["libcamera-still", "-o", image_path]
        try:
            subprocess.run(command, check=True)
            print(f"📸 Image captured successfully at: {image_path}")
            return image_path
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to capture image: {e}")
            return None
    def capture_image_with_countdown(self):
        """Capture image with countdown announcement."""
        for i in range(3, 0, -1):
            self.tts.speak(str(i))
            time.sleep(1)
        self.tts.speak("Smile!")
        return self.capture_image()
    
    def handle_fashion_request(self, transcript, intent):
        """Specialized handler for fashion requests"""
        self.tts.speak("I'll capture your image in 3... 2... 1...")
        image_path = self.capture_image_with_countdown()
        
        if not image_path:
            self.tts.speak("Sorry, I couldn't capture your image. Let's try again later.")
            return None
        
        # Get wardrobe items
        wardrobe_items = self.nlp.fetch_wardrobe_items()
        
        # Generate response based on detected intent
        response = self.nlp.generate_fashion_response(
            transcript=transcript,
            image_path=image_path,
            wardrobe_urls=wardrobe_items,
            requested_categories=intent
        )
        self.tts.speak(response)
    def get_gpt_response(self, transcript, image_path=None):
        """Handle natural language requests intelligently"""
        # First detect what the user is asking for
        intent = self.nlp.detect_intent(transcript)
        
        # If fashion-related request, handle with image capture
        if any(keyword in intent for keyword in ["outfit", "makeup", "jewelry"]):
            return self.handle_fashion_request(transcript, intent)
        
        return self.handle_general_request(transcript, intent)
    
    def get_transcript(self):
        """Listen for user speech and return transcribed text."""
        print("🎙 Speak now... ")
        transcript = self.recognizer.recognize()
        if transcript:
            print(f"🗣 You said: {transcript}")
            return transcript
        print("🤔 Could not understand speech.")
        return None
    
    def listen_for_wake_word(self):
        """Continuously listen for 'Hey Mirror' and activate when detected."""
        print("🎧 Listening for 'Hey Mirror'...")
        while True:
            command = self.recognizer.recognize()
            if command and "hey mirror" in command.lower():
                print("✅ Wake word detected!")
                return True
            

    def run_once(self):
        """Run a single interaction: wake word → command → response"""
        if self.listen_for_wake_word():
            transcript = self.get_transcript()
            if transcript:
                self.get_gpt_response(transcript)
        return None
