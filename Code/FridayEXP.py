import playsound
from gtts import gTTS
import ollama
import os
import speech_recognition as sr
import pyaudio
import pvporcupine
import numpy as np
import threading
import wikipediaapi
import requests
import json
from datetime import datetime

client = ollama.Client()

def speak(text, index):
    tts = gTTS(text=text, lang='en-ie', slow=False)
    tts.save("speech.mp3")
    playsound.playsound('speech.mp3')
    os.remove("speech.mp3")

def send_to_Ollama(messages, model="deepseek-v3.1:671b-cloud"):
    response = client.chat(
        model=model,
        messages=messages,
    )
    message = response["message"]["content"]
    messages.append({"role": "assistant", "content": message})
    return message

def wikipedia_search(query):
    """Searches Wikipedia for the given query and returns the summary."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'extract' in data:
            return data['extract']
        else:
            return "Sorry, I couldn't find any information on that topic."
    else:
        return "Sorry, I couldn't find any information on that topic."
    
def summarize(text):
    text = "Summarize this into a short, concise couple sentences: " + text
    return send_to_Ollama([{"role": "user", "content": text}])

def add_event(name, date, time, location):
    event = {
        "name": name,
        "date": date,
        "time": time,
        "location": location
    }

    try:
        with open("calendar.json", "r") as file:
            content = file.read().strip()
            if content:
                events = json.loads(content)
            else:
                events = []
    except FileNotFoundError:
        events = []

    events.append(event)

    with open("calendar.json", "w") as file:
        json.dump(events, file, indent=4)
    
def list_events():
    try:
        with open("calendar.json", "r") as file:
            content = file.read().strip()
            if content:
                events = json.loads(content)
                return events
            else:
                return []
    except FileNotFoundError:
        return []
    
def get_date():
    return datetime.now().strftime("%Y-%m-%d")

    
def get_time():
    return datetime.now().strftime("%I:%M:%S %p")

def check_for_weather_warnings(city_name):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={'078592d101bf42d88987012ccb753efd'}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'weather' in data:
            warnings = [weather['description'] for weather in data['weather']]
            return warnings
        else:
            return []
    else:
        return ["Failed to retrieve weather warnings."]

def get_current_temperature(city_name):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={'078592d101bf42d88987012ccb753efd'}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'main' in data:
            temperature_kelvin = data['main']['temp']
            temperature_fahrenheit = (temperature_kelvin - 273.15) * 9/5 + 32
            return temperature_fahrenheit
        else:
            return "Failed to retrieve temperature."
    else:
        return "Failed to retrieve temperature."

def listen_to_user():
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source, timeout=20, phrase_time_limit=60)
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                print("Sorry, I could not understand the audio.")
                return ""
            except sr.RequestError:
                print("Could not request results; check your network connection.")
                return ""
        return ""
    except sr.WaitTimeoutError:
        print("No response received. Going back to waiting for wake word.")
        return ""
    
def remove_think_tags(text):
    """
    Removes the <think> tags and all the text in between them.
    """
    result = ""
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>") + len("</think>")
        result += text[:start]
        text = text[end:]
    result += text  # Append any remaining text after the last </think> tag
    print(f"Cleaned response: {result}")  # Debugging line
    return result

def main():
    while True:
        user_input = listen_to_user()
        if user_input:
            user_input += "You are an ai running inside of a computer program, the following information is provided by the program and the user does not know it, this information is based on current and actual information, use this information to answer the user's question effectively. Try to keep your answers short and to the point, also try to avoid using unnecessary characters such as asterisks or hastags. "
            if "weather" in user_input:
                user_input += "The weather in Pleasant Prairie is currently " + str(check_for_weather_warnings("Pleasant Prairie")) + " with a temperature of " + str(get_current_temperature("Pleasant Prairie")) + " degrees fahrenheit. "
            if "date" in user_input or "time" in user_input:
                user_input += "Todays date is " + str(get_date()) + " and the time is " + str(get_time()) + ". "
            response = send_to_Ollama([{"role": "user", "content": user_input}])
            print("Friday:", response)
            response_to_speak = remove_think_tags(response)
            if response_to_speak.strip():  # Check if there is text to speak
                speak(response_to_speak, 0)
            else:
                print("No text to speak after removing </think> tags.")


def detected_callback(keyword_index):
    speak("Yes boss?", 0)
    print(f"Wake word detected! Keyword index: {keyword_index}")
    main()


recognizer = sr.Recognizer()
with sr.Microphone() as source:
    print("Listening for wake word...")
    while True:
        try:
            audio = recognizer.listen(source, timeout=.1, phrase_time_limit=5)
            try:
                text = recognizer.recognize_google(audio)
                if "friday" in text.lower():
                    detected_callback(0)
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                print("Could not request results; check your network connection.")
        except sr.WaitTimeoutError:
            count = count + 1 if 'count' in locals() else 1  # Initialize count if not already done