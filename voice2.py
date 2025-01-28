from vosk import Model, KaldiRecognizer  # оффлайн-распознавание от Vosk
import speech_recognition  # распознавание пользовательской речи (Speech-To-Text)
import wave  # создание и чтение аудиофайлов формата wav
import json  # работа с json-файлами и json-строками
import os  # работа с файловой системой

from gtts import gTTS
from playsound import playsound

import subprocess
import requests
import sys

lesson = ["Древние люди и их стоянки. Древнейшие люди начали заселять территорию России около 700 тысяч лет назад. Археологические открытия последних десятилетий уточнили датировку до 500 тысяч - 1 миллиона лет. Древние люди жили присваивающим хозяйством, охотились и собирали плоды.",  "Каменный век. Люди умели поддерживать огонь, но не добывать его. Орудия труда делались из дерева, кости и кремня. Каменный век делится на палеолит, мезолит и неолит.", "Древнейшие стоянки. Значительная часть территории России была заселена в глубокой древности. В Костенках под Воронежем найдены стоянки возрастом 35-45 тысяч лет. В Сунгири под Владимиром найдены стоянки возрастом 25 тысяч лет.", "Искусство и охота. Древние люди отражали свою жизнь в искусстве, изображая животных. В Каповой пещере на Урале найдены рисунки мамонтов и других животных. В Денисовой пещере на Алтае найдены стоянки денисовцев, живших около 50 тысяч лет назад.", "Зарождение родового строя. Около 80 тысяч лет назад условия жизни изменились, начался ледниковый период. Люди приспособились к новым условиям, охотясь на мамонтов и других животных. Охота стала загонной, что обеспечивало людей пищей и другими ресурсами.", "Развитие орудий труда. Люди научились добывать огонь и готовить пищу на огне. Техника обработки камня стала более совершенной. Появились иглы с ушками для шитья одежды.", "Родовой строй. Формировалось разделение труда между мужчинами и женщинами. Около 40 тысяч лет назад сформировался человек современного типа. Родовая община включала кровных родственников, имущество было общим.", "Мезолит и расселение. Около 12-14 тысяч лет назад закончился ледниковый период, наступил мезолит. Люди стали больше заниматься собирательством и рыболовством. Появились новые орудия труда и средства передвижения, что позволило людям расселиться дальше на север.", "Итоги. Древние люди на территории России прошли тот же путь развития, что и жители других территорий."]

def record_and_recognize_audio(*args: tuple):
    """
    Запись и распознавание аудио
    """
    with microphone:
        recognized_data = ""

        # регулирование уровня окружающего шума
        recognizer.adjust_for_ambient_noise(microphone, duration=2)

        try:
            print("Listening...")
            audio = recognizer.listen(microphone, 5, 15)

            with open("microphone-results.wav", "wb") as file:
                file.write(audio.get_wav_data())

        except speech_recognition.WaitTimeoutError:
            print("Can you check if your microphone is on, please?")
            return

        # использование online-распознавания через Google 
        try:
            print("Started recognition...")
            recognized_data = recognizer.recognize_google(audio, language="ru").lower()

        except speech_recognition.UnknownValueError:
            pass

        # в случае проблем с доступом в Интернет происходит попытка 
        # использовать offline-распознавание через Vosk
        except speech_recognition.RequestError:
            print("Trying to use offline recognition...")
            recognized_data = use_offline_recognition()

        return recognized_data

def use_offline_recognition():
    """
    Переключение на оффлайн-распознавание речи
    :return: распознанная фраза
    """
    recognized_data = ""
    try:
        # проверка наличия модели на нужном языке в каталоге приложения
        if not os.path.exists("models/vosk-model-small-ru-0.4"):
            print("Please download the model from:\n"
                  "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
            exit(1)

        # анализ записанного в микрофон аудио (чтобы избежать повторов фразы)
        wave_audio_file = wave.open("microphone-results.wav", "rb")
        model = Model("models/vosk-model-small-ru-0.4")
        offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())

        data = wave_audio_file.readframes(wave_audio_file.getnframes())
        if len(data) > 0:
            if offline_recognizer.AcceptWaveform(data):
                recognized_data = offline_recognizer.Result()

                # получение данных распознанного текста из JSON-строки
                # (чтобы можно было выдать по ней ответ)
                recognized_data = json.loads(recognized_data)
                recognized_data = recognized_data["text"]
    except:
        print("Sorry, speech service is unavailable. Try again later")

    return recognized_data

def removeNestedParentheses(s):
    ret = ''
    skip = 0
    for i in s:
        if i == '<':
            skip += 1
        elif i == '>'and skip > 0:
            skip -= 1
        elif skip == 0:
            ret += i
    return ret

def dialogueAI(prompt):
    headers = {"Content-Type": "application/json"}
    data = {"model": "llama3.2:latest", "prompt": prompt, "stream": False}
    r = requests.post("http://localhost:11434/api/generate", headers=headers, data=json.dumps(data))
    resp = json.loads(r.text)
    return resp["response"]

def say2User(answer):
    if answer != '':
        tts = gTTS(answer, lang='ru')
        tts.save("output.mp3")
        # Воспроизведение аудиофайла
        audio_file = os.path.dirname(__file__) + '\output.mp3'
        playsound(audio_file)

def listenUser():
    is_listen = True
    s = ''
    while is_listen:
        voice_input = record_and_recognize_audio()
        s += ' '+voice_input
        if s != '' and voice_input == '':
            is_listen = False
    return s

print(__name__)

if __name__ == "__main__":

    # инициализация инструментов распознавания и ввода речи
    recognizer = speech_recognition.Recognizer()
    microphone = speech_recognition.Microphone()

    #для каждой темы
    for one_lesson in lesson:
        #подготовить запрос для ученика на основе темы
        ask_prompt = 'Вы - учитель истории, задайте вопрос, используя данный текст: "'+one_lesson+'". Выделите вопрос разметкой <question>.'
        answer = dialogueAI(ask_prompt)
        p0 = answer.find('<question>')
        p1 = answer.find('</question>')
        answer = answer[p0+10:p1]

        print(answer)
        say2User(answer)

        #сказать это ученику для отладки закомментим
        #say2User(answer)

        #ждем ответа ученика
        #вариант 1 текст это для отладки
        #voice_input = input("Введите ответ: ")
        #вариант 2 голос
        voice_input = listenUser()
        print("voice_input: "+voice_input)

        #отдать ответ ученика на проверку искину
        check_prompt = 'Вы - учитель истории, задали вопрос по теме: "'+one_lesson+'". Ученик ответил: "'+voice_input+'". Правильный ли ответ, сформулируй да или нет? Выдели ответ разметкой <resume>'
        #print(check_prompt)
        answer = dialogueAI(check_prompt)
        #выделим оценку ответа от искина
        p0 = answer.find('<resume>')
        p1 = answer.find('</resume>')
        answer = answer[p0+8:p1]
        print(answer)
        while "Нет" in answer:
            #здесь будем учить пока не дойдет!
            err_prompt = 'Вы - учитель истории, задали вопрос по теме: "'+one_lesson+'". Ученик ответил не правильно: "'+voice_input+'". Объясни ученику ошибку. Выдели объяснение разметкой <explanation>'
            #print(err_prompt)
            answer = dialogueAI(err_prompt)
            p0 = answer.find('<explanation>')
            p1 = answer.find('</explanation>')
            answer = answer[p0+13:p1]
            print(answer)
            say2User(answer)

            #ЖДЕМ ПРАИвильного ответа
            #voice_input = input("Введите правильный ответ: ")
            voice_input = listenUser()
            print("voice_input: "+voice_input)

            #отдать ответ ученика на проверку искину
            check_prompt = 'Вы - учитель истории, задали вопрос по теме: "'+one_lesson+'". Ученик ответил: "'+voice_input+'". Правильный ли ответ, сформулируй да или нет? Выдели ответ разметкой <resume>'
            #print(check_prompt)
            answer = dialogueAI(check_prompt)
            #выделим оценку ответа от искина
            p0 = answer.find('<resume>')
            p1 = answer.find('</resume>')
            answer = answer[p0+8:p1]

        #ответ верный, надо похвалить и переходим к следующей теме
        praise_prompt = 'Вы - учитель истории, задали вопрос по теме: "'+one_lesson+'". Ученик ответил правильно: "'+voice_input+'". Похвали ученика. Выдели похвалу разметкой <praise>'
        answer = dialogueAI(praise_prompt)
        #выделим оценку ответа от искина
        p0 = answer.find('<praise>')
        p1 = answer.find('</praise>')
        answer = answer[p0+8:p1]
        print(answer)
        say2User(answer)


