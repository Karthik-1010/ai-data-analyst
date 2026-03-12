import os
import google.generativeai as genai

genai.configure(api_key="AIzaSyClhZJ2Jz6egn1mIR7wPm71VzvBVr4ZHL4")

print("Available Models:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
