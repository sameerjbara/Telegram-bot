import requests
from flask import Flask, Response, request
import connect_to_moovit as cm
import find_time

app = Flask(__name__)

TOKEN = '5641544389:AAGJ9Oz0fdH59ROJdffLNUCTQ2QxqMbmDGo'
ADDRESS = 'https://247b-2a0d-6fc7-330-2de1-99d4-be06-2fac-69be.eu.ngrok.io'
TELEGRAM_INIT_WEBHOOK_URL = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={ADDRESS}/message"
requests.get(TELEGRAM_INIT_WEBHOOK_URL)
stations = []
my_list = []
city = ""


@app.route('/message', methods=["POST"])
def handle_message():
    global stations
    global city
    global my_list
    bus_line = 0

    print("got msg")
    chat_id = request.get_json()['message']['chat']['id']
    if request.get_json()['message']['text']:
        msg = request.get_json()['message']['text'].split(',')
        command = msg[0]

        if command == "/choseLine":
            all_buses = cm.connect_mooivt((msg[1]))
            city = msg[2]
            for index, i in enumerate(all_buses):
                str = i.getText().replace('\n', "")[2:]
                res = requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"
                                   .format(TOKEN, chat_id, f"{index}--{str}"))

        if command == "/specificLine":
            line_index = msg[1]
            stations = cm.specific_line(line_index)
            for index, i in enumerate(stations):
                str = i.getText().replace('\n', "")
                res = requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"
                                   .format(TOKEN, chat_id, f"{index}--{str}"))

        if command == "/plan":

            start = int(msg[1])
            end = int(msg[2])
            for index, i in enumerate(stations[start:end]):
                str = i.getText().replace('\n', "")
                res = requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"
                                   .format(TOKEN, chat_id, f"{index}--{str}"))
                my_list.append([str, city])

        if command == "/estimatedTime":
            time = find_time.calc_rout_path(my_list)

            res = requests.get("https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"
                               .format(TOKEN, chat_id, f"the estimated time is : {round(time)}"))

    return Response("success")


if __name__ == '__main__':
    app.run(port=5002)
