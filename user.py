#ТУТ КЛИЕНТ ДЛЯ ПЕРЕДАЧИ ДАННЫХ НАШЕГО СОТРУДНИКА НА СЕРВАК#

# import requests
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.uic import loadUi

from callibri_controller import callibri_controller, ConnectionState, CallibriInfo


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
        if str(self.nicknameEdit.text()) != "" or str(self.nicknameEdit.text()) != "введите никнейм":
            self.startConServBtn.setEnabled(False)
            self.stopConServBtn.setEnabled(True)
            current_device=callibri_controller.connected_devices[0]
            def hr_values_updated(address: str, hr: float):
                if address == current_device:
                    print("%.2f" % hr)

            def on_pressure_index_updated(address: str, pressure_index: float):
                print(f"Pressure Index for {address}: {pressure_index:.2f}")

    # Здесь ты можешь обновить отображение индекса стресса в интерфейсе


        # def has_rr_picks(address: str, has_picks: bool):            
        #     # if address == current_device:
        #     #     self.hasRR.setText("Есть" if has_picks else "Нет")
        #     pass


            callibri_controller.hrValuesUpdated.connect(hr_values_updated)
            callibri_controller.pressureIndexUpdated.connect(on_pressure_index_updated)
            # callibri_controller.hasRRPicks.connect(has_rr_picks)
            callibri_controller.start_calculations(current_device)

    def stop_calc(self):
        try:
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