import pvporcupine
import pyaudio
import time
import struct
import sys
import os
import io
import wave
from google.cloud import speech
import google.cloud.texttospeech as tts
import google.generativeai as genai
import random


accessKey = 'uUDsCYJoJ7BBxiwvFBY+iaF9gIzEvdRHQurrActpbOyXA9YRE8JzfQ=='
FORMAT = pyaudio.paInt16
CHANNELS = 1
filename = "recording.wav"
folderpath = '/home/fabianmolina/VoiceAssistant/Gemini-AI-Voice-Assistant/'
words = ""
os.environ['GOOGLE_APPLICATION_CREDENTIALS']= folderpath + 'accessCreds.json'
voiceName = 'en-US-Casual-K'

def wake():
    
    porcupine = None
    audio = None
    stream = None
    print("Starting now:")
    try:

        porcupine = pvporcupine.create(
            access_key= accessKey,
            keyword_paths=['/home/fabianmolina/VoiceAssistant/Gemini-AI-Voice-Assistant/Lebron_en_raspberry-pi_v3_0_0.ppn', '/home/fabianmolina/VoiceAssistant/Gemini-AI-Voice-Assistant/Hey-jarvis_en_raspberry-pi_v3_0_0.ppn']
        )
        audio = pyaudio.PyAudio()
        stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=porcupine.sample_rate,
        input=True,
        frames_per_buffer=porcupine.frame_length
        )
        while True:
            
            data = stream.read(porcupine.frame_length)

            data = struct.unpack_from("h" * porcupine.frame_length, data)
            print("processing...")
            keyword_index = porcupine.process(data)
            print(keyword_index)
            if keyword_index == 0:
                print("Lebron Mode.")
                break
            elif keyword_index > 0:
                print("Jarvis activated...")
                break
        print("Found keyword")
    finally:
        if porcupine is not None:
            porcupine.delete()

def listen():
    filepath = folderpath
    os.path.join(filepath, filename)
    filepath += filename
    # set the chunk size of 1024 samples
    chunk = 1024
    # 44100 samples per second
    sample_rate = 44100
    duration = 5
    # initialize PyAudio object
    p = pyaudio.PyAudio()
    # open stream object as input & output
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=sample_rate,
                    input=True,
                    output=True,
                    frames_per_buffer=chunk)
    frames = []
    print("Recording...")
    for i in range(int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        # if you want to hear your voice while recording
        # stream.write(data)
        frames.append(data)
    print("Finished recording.")

    # stop and close stream
    stream.stop_stream()
    stream.close()
    # terminate pyaudio object
    p.terminate()
    # save audio file
    # open the file in 'write bytes' mode
    wf = wave.open(filepath, "wb")
    # set the channels
    wf.setnchannels(CHANNELS)
    # set the sample format
    wf.setsampwidth(p.get_sample_size(FORMAT))
    # set the sample rate
    wf.setframerate(sample_rate)
    # write the frames as bytes
    wf.writeframes(b"".join(frames))
    # close the file
    wf.close()

def analyzeSpeech():
    #setting Google credential
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']= folderpath + 'accessCreds.json'
    # create client instance 
    client = speech.SpeechClient()
    #the path of your audio file
    
    with io.open(folderpath + filename, "rb") as audio_file:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    enable_automatic_punctuation=True,
    audio_channel_count=1,
    language_code="en-US",
    )
    # Sends the request to google to transcribe the audio
    response = client.recognize(request={"config": config, "audio": audio})
    # Reads the response
    for result in response.results:
        words = result.alternatives[0].transcript
        print(words)
    os.remove(folderpath + filename)
    return words

def playMusic(song):
    return True

def turnOnLights():
    return True


def playFile(audioFile):
    # length of data to read.
    chunk = 1024

    '''
    ************************************************************************
        This is the start of the "minimum needed to read a wave"
    ************************************************************************
    '''
    # open the file for reading.
    wf = wave.open(audioFile, 'rb')

    # create an audio object
    p = pyaudio.PyAudio()

    # open stream based on the wave object which has been input.
    stream = p.open(format =
                    p.get_format_from_width(wf.getsampwidth()),
                    channels = wf.getnchannels(),
                    rate = wf.getframerate(),
                    output = True)

    # read data (based on the chunk size)
    data = wf.readframes(chunk)

    # play stream (looping from beginning of file to the end)
    while data:
        # writing to the stream is what *actually* plays the sound.
        stream.write(data)
        data = wf.readframes(chunk)


    # cleanup stuff.
    wf.close()
    stream.close()    
    p.terminate()

def text_to_wav(voice_name: str, text: str):
    language_code = "-".join(voice_name.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)
    voice_params = tts.VoiceSelectionParams(
        language_code=language_code, name=voice_name
    )
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    client = tts.TextToSpeechClient()
    response = client.synthesize_speech(
        input=text_input,
        voice=voice_params,
        audio_config=audio_config,
    )

    filename = folderpath + 'response.wav'
    with open(filename, "wb") as out:
        out.write(response.audio_content)
        print(f'Generated speech saved to "{filename}"')

def wakeResponse():
    case = random.randint(0,5)
    text = ""
    if case == 0:
        text = "Hey how can I help you?"
    elif case == 1:
        text = "Hey there!"
    elif case == 2:
        text = "What's up?"
    elif case == 3:
        text = "What can I do for you?" 
    elif case == 4:
        text = "Oh not again..."
    elif case == 5:
        text = "Ah! You woke me up man."   
    text_to_wav(voiceName, text)
    sound = folderpath + 'response.wav'
    playFile(sound)
    os.remove(folderpath + 'response.wav')

def generativeResponse(question):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(question)

    print("This is the ai response: " + response.text)
    text_to_wav(voiceName, response.text)
    playFile(folderpath + 'response.wav')
    os.remove(folderpath + 'response.wav')





while True:
    wake()
    wakeResponse()
    print("Going to start recording now:")
    listen()
    words = analyzeSpeech()
    print("This is last words:" + words)
    if "play" in words.lower():
        index = words.find("play")
        song = words[index + 4: ]
        playMusic(song)
    elif "turn on" in words.lower():
        turnOnLights()
    else:
        generativeResponse(words)
    break

