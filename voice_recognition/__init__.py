# Reference: https://pypi.org/project/SpeechRecognition/
# Reference: https://www.geeksforgeeks.org/speech-recognition-in-python-using-
#            google-speech-api/

import speech_recognition as sr
import subprocess


class VoiceRecognition():
    def start_voice_recog(self):
        # obtain audio from the audio file
        r = sr.Recognizer()
        audio = 'voice_recognition/BMW.wav'

        with sr.AudioFile(audio) as source:
            # clear console of errors
            subprocess.run("clear")

            # wait for a second to let the recognizer adjust the
            # energy threshold based on the surrounding noise level
            r.adjust_for_ambient_noise(source)

            print("Converting the audio into text!")
            audio = r.record(source)

        # recognize speech using Google Speech Recognition
        try:
            # for testing purposes, we're just using the default API key
            # to use another API key, use
            # `r.recognize_google(audio,
            #                     key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
            # instead of `r.recognize_google(audio)`
            print("Google Speech Recognition thinks you said '{}'".format(
                r.recognize_google(audio)))
            return r.recognize_google(audio)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print(
                'Google Speech Recognition service unavailable; {0}'.format(e))
