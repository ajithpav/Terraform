import os
import asyncio
import websockets
import json
import numpy as np
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from livekit import rtc
from livekit.rtc.track import AudioTrack
from pydub import AudioSegment
import soundfile as sf
import wave
import pyaudio
import threading
import queue

# Environment variables for LiveKit
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "wss://your-livekit-server.com")
LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY", "your-api-key")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET", "your-api-secret")
ROOM_NAME = "chatbot-room"

# Initialize Hugging Face models
class AIModels:
    def __init__(self):
        print("Loading speech recognition model...")
        self.speech_recognizer = pipeline("automatic-speech-recognition", 
                                          model="openai/whisper-small")
        
        print("Loading text generation model...")
        self.generator_model = AutoModelForCausalLM.from_pretrained("gpt2")
        self.generator_tokenizer = AutoTokenizer.from_pretrained("gpt2")
        
        print("Loading text-to-speech model...")
        self.tts_model = pipeline("text-to-speech", model="facebook/fastspeech2-en-ljspeech")
        
        print("All models loaded!")

    def transcribe_audio(self, audio_data, sample_rate=16000):
        """Convert speech to text using Whisper model"""
        try:
            # Save the audio data to a temporary file
            sf.write("temp_audio.wav", audio_data, sample_rate)
            
            # Transcribe using Whisper
            result = self.speech_recognizer("temp_audio.wav")
            transcript = result["text"]
            
            print(f"Transcribed: {transcript}")
            return transcript
        except Exception as e:
            print(f"Error in speech recognition: {e}")
            return ""
        finally:
            # Clean up temp file
            if os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")

    def generate_response(self, input_text):
        """Generate text response using GPT-2"""
        try:
            # Add a prompt prefix to help guide the model
            prompt = f"User: {input_text}\nBot:"
            
            inputs = self.generator_tokenizer(prompt, return_tensors="pt")
            attention_mask = inputs["attention_mask"]
            
            # Generate response
            output = self.generator_model.generate(
                inputs["input_ids"],
                attention_mask=attention_mask,
                max_new_tokens=100,
                temperature=0.7,
                top_p=0.9,
                no_repeat_ngram_size=2,
                pad_token_id=self.generator_tokenizer.eos_token_id
            )
            
            response = self.generator_tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Extract just the bot's response
            if "Bot:" in response:
                response = response.split("Bot:")[1].strip()
            
            print(f"Generated response: {response}")
            return response
        except Exception as e:
            print(f"Error in text generation: {e}")
            return "I'm sorry, I couldn't generate a proper response."

    def text_to_speech(self, text):
        """Convert text to speech using FastSpeech2 model"""
        try:
            speech = self.tts_model(text)
            
            # Save as wav file
            with open("response.wav", "wb") as f:
                f.write(speech["bytes"])
            
            # Load audio data
            audio_data, sample_rate = sf.read("response.wav")
            
            print(f"Generated speech for: {text}")
            return audio_data, sample_rate
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return None, None


class LiveKitAudioHandler:
    def __init__(self, ai_models):
        self.ai_models = ai_models
        self.audio_queue = queue.Queue()
        self.is_processing = False
        self.room = None
        self.local_track = None
        self.audio_buffer = []
        self.processing_thread = None
        
    async def connect_to_room(self):
        """Connect to LiveKit room"""
        try:
            self.room = rtc.Room()
            
            # Set up room callbacks
            @self.room.on("track_subscribed")
            def on_track_subscribed(track, publication, participant):
                if isinstance(track, AudioTrack):
                    print(f"Subscribed to audio track from {participant.identity}")
                    track.set_audio_output(self._handle_audio_frame)
            
            # Connect to the LiveKit room
            connection_info = rtc.ConnectionInfo(
                LIVEKIT_URL, 
                "chatbot", 
                token=self._generate_token("chatbot")
            )
            
            await self.room.connect(connection_info)
            print(f"Connected to room: {ROOM_NAME}")
            
            # Create and publish local audio track
            self.local_track = await rtc.AudioTrack.create_audio_track("local-audio")
            await self.room.local_participant.publish_track(self.local_track)
            
            # Start audio processing thread
            self.processing_thread = threading.Thread(target=self._process_audio_queue)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Keep the connection alive
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error in LiveKit connection: {e}")
    
    def _generate_token(self, participant_identity):
        """Generate LiveKit access token"""
        from livekit import access_token
        
        token = access_token.AccessToken(
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET
        )
        
        token.add_grant(
            room_join=True,
            room=ROOM_NAME,
            participant_identity=participant_identity
        )
        
        return token.to_jwt()
    
    def _handle_audio_frame(self, frame_data, sample_rate, channels):
        """Handler for incoming audio frames"""
        # Convert to mono if needed
        if channels > 1:
            # Average all channels
            mono_data = np.mean(frame_data, axis=1)
        else:
            mono_data = frame_data
            
        # Add to audio buffer
        self.audio_buffer.extend(mono_data.tolist())
        
        # Process if we have enough audio data (2 seconds)
        if len(self.audio_buffer) > sample_rate * 2:
            audio_chunk = np.array(self.audio_buffer)
            self.audio_buffer = []  # Clear buffer
            
            # Add to processing queue
            self.audio_queue.put((audio_chunk, sample_rate))
    
    def _process_audio_queue(self):
        """Process audio chunks from the queue"""
        while True:
            try:
                # Get audio chunk from queue
                audio_chunk, sample_rate = self.audio_queue.get()
                
                if not self.is_processing:
                    self.is_processing = True
                    
                    # Process in a separate thread to not block
                    threading.Thread(
                        target=self._process_audio_chunk, 
                        args=(audio_chunk, sample_rate)
                    ).start()
                    
                self.audio_queue.task_done()
            except Exception as e:
                print(f"Error processing audio queue: {e}")
    
    def _process_audio_chunk(self, audio_chunk, sample_rate):
        """Process a chunk of audio data"""
        try:
            # Transcribe audio to text
            text = self.ai_models.transcribe_audio(audio_chunk, sample_rate)
            
            if text:
                # Generate response
                response_text = self.ai_models.generate_response(text)
                
                # Convert response to speech
                response_audio, audio_sr = self.ai_models.text_to_speech(response_text)
                
                if response_audio is not None:
                    # Send audio response back through LiveKit
                    self._send_audio_response(response_audio, audio_sr)
        except Exception as e:
            print(f"Error processing audio chunk: {e}")
        finally:
            self.is_processing = False
    
    def _send_audio_response(self, audio_data, sample_rate):
        """Send audio response back through LiveKit"""
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save to temporary WAV file
            with wave.open("temp_response.wav", "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            # Play audio through local track
            if self.local_track:
                # Read the file and send through LiveKit
                audio = AudioSegment.from_wav("temp_response.wav")
                raw_data = audio.raw_data
                
                # Use LiveKit's audio interface to send the data
                # Note: This is simplified and may need adaptation based on LiveKit's API
                self.local_track.write_frame(raw_data, len(raw_data))
                
            # Clean up temp file
            if os.path.exists("temp_response.wav"):
                os.remove("temp_response.wav")
                
        except Exception as e:
            print(f"Error sending audio response: {e}")


class WebSocketChatHandler:
    def __init__(self, ai_models):
        self.ai_models = ai_models
        self.clients = set()
        
    async def start_server(self, host="0.0.0.0", port=8765):
        """Start WebSocket server for text chat"""
        server = await websockets.serve(self._handle_client, host, port)
        print(f"WebSocket server started on {host}:{port}")
        await server.wait_closed()
    
    async def _handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        try:
            # Add client to set
            self.clients.add(websocket)
            print(f"New client connected: {websocket.remote_address}")
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "system",
                "message": "Connected to chatbot server"
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if "message" in data:
                        user_message = data["message"]
                        print(f"Received message: {user_message}")
                        
                        # Generate response
                        response = self.ai_models.generate_response(user_message)
                        
                        # Send response
                        await websocket.send(json.dumps({
                            "type": "bot",
                            "message": response
                        }))
                        
                        # Generate speech if needed
                        if data.get("generate_speech", False):
                            # Run in thread to not block
                            threading.Thread(
                                target=self._generate_and_send_speech,
                                args=(response, websocket)
                            ).start()
                            
                except json.JSONDecodeError:
                    print("Received invalid JSON")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)
    
    def _generate_and_send_speech(self, text, websocket):
        """Generate speech and send via WebSocket"""
        try:
            audio_data, sample_rate = self.ai_models.text_to_speech(text)
            
            if audio_data is not None:
                # Convert to WAV
                with wave.open("temp_ws_response.wav", "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
                
                # Read file as binary
                with open("temp_ws_response.wav", "rb") as f:
                    audio_bytes = f.read()
                
                # Send audio data over WebSocket
                asyncio.run(websocket.send(audio_bytes))
                
                # Clean up
                if os.path.exists("temp_ws_response.wav"):
                    os.remove("temp_ws_response.wav")
                    
        except Exception as e:
            print(f"Error sending speech via WebSocket: {e}")


async def main():
    """Main function to run the chatbot"""
    # Initialize AI models
    ai_models = AIModels()
    
    # Create handlers
    livekit_handler = LiveKitAudioHandler(ai_models)
    websocket_handler = WebSocketChatHandler(ai_models)
    
    # Start both services
    await asyncio.gather(
        livekit_handler.connect_to_room(),
        websocket_handler.start_server()
    )

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())