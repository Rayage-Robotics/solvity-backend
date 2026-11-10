import serial
import time
import speech_recognition as sr
import ollama
import json
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
# IMPORTANT: When you plug in the Arduino, change this to your Mac's port.
# It will look like: '/dev/cu.usbmodem1101' or '/dev/cu.usbserial-1420'
ARDUINO_PORT = '/dev/cu.usbmodem1101' 
BAUD_RATE = 9600

# ==========================================
# 2. THE AI FUNCTION
# ==========================================
def analyze_with_ai(transcript):
    print("🧠 Solvity AI Analyzing...")
    
    prompt = f"""
    You are the Solvity AI Safety Dispatcher, an advanced emergency response AI in South Africa.
    A user has pressed their panic button. Here is the environmental audio transcript: "{transcript}"
    
    Analyze the transcript and determine if this is a real emergency or a false alarm.
    
    You must output ONLY a valid JSON object with exactly these three keys:
    1. "threat_level": "HIGH", "MEDIUM", or "LOW"
    2. "reasoning": A brief explanation of why you chose this level.
    3. "dispatch_action": "DISPATCH_PRIVATE_SECURITY" or "IGNORE"
    
    If there is any indication of violence, a weapon, screaming, or stalking, threat_level must be HIGH.
    """
    
    try:
        # Call the local Llama 3 model (Make sure Ollama is running in the background!)
        response = ollama.chat(model='llama3', messages=[
            {'role': 'user', 'content': prompt},
        ])
        
        ai_text = response['message']['content']
        
        # Clean up the text in case the AI adds markdown formatting
        if "```json" in ai_text:
            ai_text = ai_text.split("```json")[1].split("```")[0]
        elif "```" in ai_text:
            ai_text = ai_text.split("```")[1].split("```")[0]
            
        # Extract JSON using regex just in case
        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            ai_text = json_match.group(0)
            
        result = json.loads(ai_text.strip())
        
        print("\n--- 🚨 AI RESPONSE ---")
        print(f"Threat Level: {result.get('threat_level', 'UNKNOWN')}")
        print(f"Reasoning:    {result.get('reasoning', 'N/A')}")
        print(f"Action:       {result.get('dispatch_action', 'UNKNOWN')}")
        print("----------------------\n")
        
    except Exception as e:
        print(f"❌ AI Error: {e}")

# ==========================================
# 3. THE LISTENING FUNCTION
# ==========================================
def listen_for_help():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening for 4 seconds... Speak now!")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)
            print("Transcribing...")
            text = recognizer.recognize_google(audio)
            return text
        except sr.WaitTimeoutError:
            return "No speech detected, only panic button pressed."
        except sr.UnknownValueError:
            return "Audio unclear, screaming or distress sounds detected."
        except Exception as e:
            return f"Audio error: {str(e)}"

# ==========================================
# 4. TEST MODE (Run this first!)
# ==========================================
print("🛡️ Solvity AI System Starting...")

# This simulates the button being pressed and the mic hearing this text
test_text = "Please help me, a man is following me and he has a knife!"
print(f"📝 Simulated Transcript: '{test_text}'")
analyze_with_ai(test_text)


# ==========================================
# 5. HARDWARE MODE (Uncomment this when your Arduino is ready)
# ==========================================
"""
print("Connecting to Arduino...")
try:
    arduino = serial.Serial(port=ARDUINO_PORT, baudrate=BAUD_RATE, timeout=1)
    time.sleep(2) 
    print("✅ Solvity Hardware Armed. Waiting for Panic Button...\n")
    
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            
            if line == "TRIGGER":
                print("\n🚨 HARDWARE TRIGGER DETECTED 🚨")
                
                user_speech = listen_for_help()
                print(f"📝 Transcript: '{user_speech}'")
                
                analyze_with_ai(user_speech)
                
                print("🛡️ Re-arming Solvity. Waiting for next trigger...\n")
                
except Exception as e:
    print(f"❌ Failed to connect to Arduino. Error: {e}")
"""