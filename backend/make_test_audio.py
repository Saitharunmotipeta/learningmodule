# make_test_audio.py
import pyttsx3

engine = pyttsx3.init()
# Adjust voice rate for clarity (slow)
rate = engine.getProperty('rate')
engine.setProperty('rate', 80)  # 120-180 is usually good; lower for clearer enunciation

# You can choose voice (male/female) if available
voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[0].id)

text = "hospital"  # choose the test word or a short phrase
filename = "test.wav"
engine.save_to_file(text, filename)
engine.runAndWait()
print("Saved:", filename)
