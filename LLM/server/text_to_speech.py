import pyttsx3
import threading
import queue
import time
import logging

class TextToSpeech:
    def __init__(self, rate=150, volume=0.8, voice_index=0):
        """
        Initialize Text-to-Speech engine
        
        Args:
            rate (int): Speaking rate (words per minute)
            volume (float): Volume level (0.0 to 1.0)
            voice_index (int): Voice index (0 for first available voice)
        """
        self.engine = None
        self.rate = rate
        self.volume = volume
        self.voice_index = voice_index
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.worker_thread = None
        self.stop_flag = threading.Event()
        
        self._initialize_engine()
        self._start_worker_thread()
    
    def _initialize_engine(self):
        """Initialize the TTS engine with settings"""
        try:
            self.engine = pyttsx3.init()
            
            # Set speech rate
            self.engine.setProperty('rate', self.rate)
            
            # Set volume
            self.engine.setProperty('volume', self.volume)
            
            # Set voice
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > self.voice_index:
                self.engine.setProperty('voice', voices[self.voice_index].id)
                print(f"🔊 Using voice: {voices[self.voice_index].name}")
            else:
                print("🔊 Using default voice")
                
            # Set up event callbacks
            self.engine.connect('started-utterance', self._on_start)
            self.engine.connect('finished-utterance', self._on_end)
            
        except Exception as e:
            print(f"❌ Error initializing TTS engine: {e}")
            self.engine = None
    
    def _on_start(self, name):
        """Callback when speech starts"""
        self.is_speaking = True
    
    def _on_end(self, name, completed):
        """Callback when speech ends"""
        self.is_speaking = False
    
    def _start_worker_thread(self):
        """Start background thread for processing speech queue"""
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
    
    def _speech_worker(self):
        """Background worker to process speech queue"""
        while not self.stop_flag.is_set():
            try:
                # Get text from queue with timeout
                text = self.speech_queue.get(timeout=1.0)
                if text is None:  # Poison pill to stop worker
                    break
                
                if self.engine:
                    print(f"🔊 Speaking: {text[:50]}...")
                    self.engine.say(text)
                    self.engine.runAndWait()
                
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error in speech worker: {e}")
    
    def speak(self, text, blocking=False):
        """
        Convert text to speech
        
        Args:
            text (str): Text to convert to speech
            blocking (bool): If True, wait for speech to complete
        """
        if not text or not text.strip():
            return
        
        # Clean text for better speech
        cleaned_text = self._clean_text(text)
        
        if blocking:
            # Speak immediately and wait
            if self.engine:
                print(f"🔊 Speaking: {cleaned_text[:50]}...")
                self.is_speaking = True
                self.engine.say(cleaned_text)
                self.engine.runAndWait()
                self.is_speaking = False
        else:
            # Add to queue for background processing
            self.speech_queue.put(cleaned_text)
    
    def _clean_text(self, text):
        """Clean text for better speech synthesis"""
        # Remove markdown formatting
        import re
        
        # Remove markdown headers
        text = re.sub(r'#{1,6}\s*', '', text)
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Replace special characters with spaces
        text = re.sub(r'[^\w\s.,!?;:]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def stop_current_speech(self):
        """Stop current speech"""
        if self.engine and self.is_speaking:
            self.engine.stop()
            self.is_speaking = False
    
    def clear_queue(self):
        """Clear pending speech queue"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
    
    def wait_for_completion(self, timeout=10):
        """Wait for all queued speech to complete"""
        start_time = time.time()
        while not self.speech_queue.empty() or self.is_speaking:
            if time.time() - start_time > timeout:
                print("⚠️ Speech timeout reached")
                break
            time.sleep(0.1)
    
    def get_available_voices(self):
        """Get list of available voices"""
        if not self.engine:
            return []
        
        voices = self.engine.getProperty('voices')
        voice_list = []
        
        for i, voice in enumerate(voices):
            voice_info = {
                'index': i,
                'id': voice.id,
                'name': voice.name,
                'languages': getattr(voice, 'languages', []),
                'gender': getattr(voice, 'gender', 'Unknown')
            }
            voice_list.append(voice_info)
        
        return voice_list
    
    def set_voice(self, voice_index):
        """Change voice by index"""
        if not self.engine:
            return False
        
        voices = self.engine.getProperty('voices')
        if voices and 0 <= voice_index < len(voices):
            self.engine.setProperty('voice', voices[voice_index].id)
            self.voice_index = voice_index
            print(f"🔊 Changed to voice: {voices[voice_index].name}")
            return True
        else:
            print(f"❌ Invalid voice index: {voice_index}")
            return False
    
    def set_rate(self, rate):
        """Change speaking rate"""
        if not self.engine:
            return False
        
        self.rate = max(50, min(300, rate))  # Limit rate between 50-300
        self.engine.setProperty('rate', self.rate)
        print(f"🔊 Changed speaking rate to: {self.rate}")
        return True
    
    def set_volume(self, volume):
        """Change volume level"""
        if not self.engine:
            return False
        
        self.volume = max(0.0, min(1.0, volume))  # Limit volume between 0.0-1.0
        self.engine.setProperty('volume', self.volume)
        print(f"🔊 Changed volume to: {self.volume}")
        return True
    
    def shutdown(self):
        """Shutdown TTS engine and cleanup"""
        print("🔊 Shutting down TTS engine...")
        
        # Stop worker thread
        self.stop_flag.set()
        self.speech_queue.put(None)  # Poison pill
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)
        
        # Stop current speech and cleanup engine
        if self.engine:
            self.stop_current_speech()
            self.engine = None
        
        print("🔊 TTS engine shutdown complete")

# Convenience functions for quick usage
_global_tts = None

def init_tts(rate=150, volume=0.8, voice_index=0):
    """Initialize global TTS instance"""
    global _global_tts
    _global_tts = TextToSpeech(rate=rate, volume=volume, voice_index=voice_index)
    return _global_tts

def speak(text, blocking=False):
    """Quick speak function using global TTS instance"""
    global _global_tts
    if _global_tts is None:
        _global_tts = TextToSpeech()
    _global_tts.speak(text, blocking=blocking)

def shutdown_tts():
    """Shutdown global TTS instance"""
    global _global_tts
    if _global_tts:
        _global_tts.shutdown()
        _global_tts = None

# Example usage and testing
if __name__ == "__main__":
    print("=== Text-to-Speech Test ===")
    
    # Initialize TTS
    tts = TextToSpeech(rate=160, volume=0.9)
    
    # List available voices
    print("\n📢 Available voices:")
    voices = tts.get_available_voices()
    for voice in voices:
        print(f"  {voice['index']}: {voice['name']} ({voice['gender']})")
    
    # Test speech
    test_texts = [
        "Hello! This is a test of the text to speech system.",
        "Smart home assistant is now ready to speak responses.",
        "Lights turned on in the living room successfully."
    ]
    
    print("\n🔊 Testing speech...")
    for i, text in enumerate(test_texts):
        print(f"Test {i+1}: {text}")
        tts.speak(text, blocking=True)
        time.sleep(1)
    
    # Test queue
    print("\n🔊 Testing speech queue...")
    for text in test_texts:
        tts.speak(text, blocking=False)
    
    # Wait for completion
    tts.wait_for_completion()
    
    # Cleanup
    tts.shutdown()
    print("✅ TTS test completed!")