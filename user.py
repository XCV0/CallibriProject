#ТУТ КЛИЕНТ ДЛЯ ПЕРЕДАЧИ ДАННЫХ НАШЕГО СОТРУДНИКА НА СЕРВАК#

import requests
import datetime

import sys
from PyQt6.QtCore import QTimer


from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.uic import loadUi

from callibri_controller import callibri_controller, ConnectionState, CallibriInfo


server_ip = '25.8.42.226'
server_port = '8080'

last_time = 0
pulse = 0
emotions = 0

def check_time(time_str):
        time_obj = datetime.datetime.strptime(time_str, '%d-%m-%H-%M-%S')
        return (datetime.datetime.now() - time_obj) > datetime.timedelta(seconds=5)

def write_pulse_to_server(nickname, pulsedata):
    global last_time
    try:
        now = datetime.datetime.now()
        print(now.strftime("%d-%m-%H-%M-%S"))
        if last_time == 0:
            last_time = now.strftime("%d-%m-%H-%M-%S")
            pulsedata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{pulsedata}"
        else:
            if check_time(last_time):
                last_time = now.strftime("%d-%m-%H-%M-%S")
                pulsedata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{pulsedata}"

                requests.get(f"http://{server_ip}:{server_port}/write_pulse?name={nickname}&datapulse={pulsedata}")
        print(server_ip)

    except Exception as e:
        print(e)
        sys.exit()

def write_emotions_to_server(nickname, emotionsdata):
    global last_time
    try:
        now = datetime.datetime.now()
        print(now.strftime("%d-%m-%H-%M-%S"))
        if last_time == 0:
            last_time = now.strftime("%d-%m-%H-%M-%S")
            emotionsdata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{emotionsdata}"
        else:
            if check_time(last_time):
                last_time = now.strftime("%d-%m-%H-%M-%S")
                emotionsdata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{emotionsdata}"

                requests.get(f"http://{server_ip}:{server_port}/write_emotions?name={nickname}&emotions={emotionsdata}")
    except Exception as e:
        print(e)
        sys.exit()

# def write_data_to_server(nickname, pulsedata, emotionsdata):
#     try:
#         now = datetime.datetime.now()
#         print(now.strftime("%d-%m-%H-%M-%S"))
#         if last_time == 0:
#             last_time = now
#             pulsedata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{pulsedata}" 
#             emotionsdata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{emotionsdata}"
#         else:
#             if check_time(last_time):
#                 last_time = now
#                 pulsedata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{pulsedata}"
#                 emotionsdata = str(now.strftime("%d-%m-%H-%M-%S")) + f"-{emotionsdata}"

#         requests.get(f"http://{server_ip}:{server_port}/writedata?name={nickname}&datapulse={pulsedata}&emotions={emotionsdata}")
#     except Exception as e:
#         print(e)

def write_status_to_server(nickname, status):
    print("func")
    try:
        requests.get(f"http://{server_ip}:{server_port}/write_status?name={nickname}&status={status}")
    except Exception as e:
        print(e)

class MainScreen(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("ui/MainWindow.ui", self)

        self.findDeviceBtn.clicked.connect(self.start_search)
        self.startConServBtn.clicked.connect(self.start_calc)
        self.stopConServBtn.clicked.connect(self.stop_calc)

        self.foundedListWidget.itemClicked.connect(self.connect_to_device)
        self.__founded_sensors=list[CallibriInfo]

    def start_search(self):
        self.foundedListWidget.clear()
        self.findDeviceBtn.setText("Поиск...")
        self.findDeviceBtn.setEnabled(False)

        def on_device_founded(sensors: list[CallibriInfo]):
            self.__founded_sensors=sensors
            self.foundedListWidget.addItems([sens.Name + ' (' + sens.Address + ')' for sens in sensors])
            self.findDeviceBtn.setText("Искать заново...")
            self.findDeviceBtn.setEnabled(True)
            callibri_controller.foundedDevices.disconnect(on_device_founded)

        callibri_controller.foundedDevices.connect(on_device_founded)
        callibri_controller.search_with_result(5, [])



    def connect_to_device(self, item):
        item_number = self.foundedListWidget.row(item)
        item_info=self.__founded_sensors[item_number]

        def on_device_connection_state_changed(address, state):
            item.setText(item_info.Name + ' (' + item_info.Address + '): ' + state.name)
            if address==item_info.Address and state==ConnectionState.Connected:
                self.startConServBtn.setEnabled(True)

        callibri_controller.connectionStateChanged.connect(on_device_connection_state_changed)
        callibri_controller.connect_to(info=item_info, need_reconnect=True)

    def start_calc(self):
        if str(self.nicknameEdit.text()) != "":
            self.startConServBtn.setEnabled(False)
            self.stopConServBtn.setEnabled(True)
            current_device=callibri_controller.connected_devices[0]
            def hr_values_updated(address: str, hr: float):
                global pulse
                
                if address == current_device:
                    # print("%.2f" % hr)
                    pulse = "%.2f" % hr
                    # write_pulse_to_server(nickname=str(self.nicknameEdit.text()), pulsedata=pulse)
                    

            def on_pressure_index_updated(address: str, pressure_index: float):
                global emotions
                print(f"Pressure Index for {address}: {pressure_index:.2f}")
                emotions = f"{pressure_index:.2f}"
                # write_emotions_to_server(nickname=str(self.nicknameEdit.text()), emotionsdata=emotions)
    

            # write_status_to_server(nickname=str(self.nicknameEdit.text()), status="online")
            

    # Здесь ты можешь обновить отображение индекса стресса в интерфейсе


        # def has_rr_picks(address: str, has_picks: bool):            
        #     # if address == current_device:
        #     #     self.hasRR.setText("Есть" if has_picks else "Нет")
        #     pass



        # Задержка перед началом вычислений

            callibri_controller.hrValuesUpdated.connect(hr_values_updated)
            callibri_controller.pressureIndexUpdated.connect(on_pressure_index_updated)
            callibri_controller.start_calculations(current_device)

        else:
            print("Введите никнейм")

    def stop_calc(self):
        try:
            write_status_to_server(nickname=str(self.nicknameEdit.text()), status="offline")
            callibri_controller.hrValuesUpdated.disconnect()
            callibri_controller.hasRRPicks.disconnect()
            callibri_controller.pressureIndexUpdated.disconnect()

            self.startConServBtn.setEnabled(True)
            self.stopConServBtn.setEnabled(False)
        except Exception as err:
            print(err)
        callibri_controller.stop_calculations(callibri_controller.connected_devices[0])

app = QApplication(sys.argv)
window = MainScreen()
window.show()
app.exec()
callibri_controller.stop_all()
sys.exit()