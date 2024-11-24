import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidgetItem
from PyQt6.uic import loadUi
import sys
from PyQt6.QtGui import QColor
import requests
import matplotlib.pyplot as plt
from datetime import datetime


def parse_data(data):
    timestamps = []
    values = []
    for record in data.split(')'):
        if not record.strip():
            continue
        parts = record.split('-')
        try:
            timestamp = datetime.strptime('-'.join(parts[:5]), "%d-%m-%H-%M-%S")
            value = float(parts[5])
            timestamps.append(timestamp)
            values.append(value)
        except (ValueError, IndexError):
            print(f"Ошибка обработки записи: {record}")
    return timestamps, values


def get_last_pulse(pulsedata):
    pulse_records = pulsedata.split(')')
    if pulse_records[-1] == '':
        pulse_records.pop()
    last_record = pulse_records[-1]
    last_pulse = last_record.split('-')[-1]
    return last_pulse


def get_last_emotions(emotionsdata):
    emotions_records = emotionsdata.split(')')
    if emotions_records[-1] == '':
        emotions_records.pop()
    last_record = emotions_records[-1]
    last_emotions = last_record.split('-')[-1]
    return last_emotions


def sort_by_stress(users):
    def extract_stress(user):
        try:
            return float(get_last_emotions(user['emotions_data']))
        except ValueError:
            return 0.0

    return sorted(users, key=extract_stress, reverse=True)


def get_stress_color(stress):
    if stress <= 100:
        return QColor("green")
    elif 101 <= stress <= 400:
        return QColor("yellow")
    elif 401 <= stress <= 1000:
        return QColor("red")
    else:
        return QColor("darkred")


class MainScreen(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("ui/AdminWindow.ui", self)
        self.data = []
        self.resetBtn.clicked.connect(self.refresh)
        self.listWidgets.itemClicked.connect(self.handle_item_clicked)

    def refresh(self):
        json_data = requests.get("http://25.8.42.226:8080/get_online").text
        self.data = json.loads(json_data)
        self.listWidgets.clear()
        sorted_data = sort_by_stress(self.data)

        for user in sorted_data:
            name = user['nickname']
            pulsedata = user['pulse_data']
            emotionsdata = user['emotions_data']
            last_emotion = get_last_emotions(emotionsdata)
            last_pulse = get_last_pulse(pulsedata)

            if str(last_emotion) == "0.00":
                last_emotion = "датчик пока не сообщил информацию"
                stress_value = 0.0
            else:
                stress_value = float(last_emotion)

            item = QListWidgetItem(f"Никнейм: {name}, Последний пульс: {last_pulse}, Индекс стресса: {last_emotion}")

            item.setForeground(get_stress_color(stress_value))

            self.listWidgets.addItem(item)

    def handle_item_clicked(self, item):
        if not self.data:
            print("Данные отсутствуют. Сначала обновите список.")
            return

        name = item.text().split(",")[0].split(":")[1].strip()
        for user in sort_by_stress(self.data):
            if user['nickname'] == name:
                self.plot_data(user['pulse_data'], user['emotions_data'])
                break

    def plot_data(self, pulse_data, stress_data):
        pulse_timestamps, pulse_values = parse_data(pulse_data)
        stress_timestamps, stress_values = parse_data(stress_data)

        plt.figure(figsize=(12, 6))

        plt.subplot(2, 1, 1)
        plt.plot(pulse_timestamps, pulse_values, label="Пульс", color="blue", marker="o")
        plt.title("График пульса")
        plt.xlabel("Время")
        plt.ylabel("Пульс")
        plt.grid(True)
        plt.legend()

        plt.subplot(2, 1, 2)
        plt.plot(stress_timestamps, stress_values, label="Стресс", color="red", marker="o")
        plt.title("График стресса")
        plt.xlabel("Время")
        plt.ylabel("Стресс")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.show()


app = QApplication(sys.argv)
window = MainScreen()
window.show()
app.exec()
