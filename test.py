#ТУТ КЛИЕНТ ДЛЯ ПЕРЕДАЧИ ДАННЫХ НАШЕГО СОТРУДНИКА НА СЕРВАК#

import sys

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.uic import loadUi

from callibri_controller import callibri_controller, ConnectionState, CallibriInfo


class MainScreen(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("ui/MainWindow.ui", self)
        self.startCalcButton.setVisible(False)
        self.stopCalcButton.setVisible(False)
        self.label_3.setVisible(False)
        self.hasRR.setVisible(False)
        self.label_4.setVisible(False)
        self.hrValue.setVisible(False)

        self.searchButton.clicked.connect(self.start_search)
        self.startCalcButton.clicked.connect(self.start_calc)
        self.stopCalcButton.clicked.connect(self.stop_calc)
        self.foundedListWidget.itemClicked.connect(self.connect_to_device)
        self.__founded_sensors=list[CallibriInfo]

    def start_search(self):
        self.foundedListWidget.clear()
        self.searchButton.setText("Поиск...")
        self.searchButton.setEnabled(False)

        def on_device_founded(sensors: list[CallibriInfo]):
            self.__founded_sensors=sensors
            self.foundedListWidget.addItems([sens.Name + ' (' + sens.Address + ')' for sens in sensors])
            self.searchButton.setText("Искать заново...")
            self.searchButton.setEnabled(True)
            callibri_controller.foundedDevices.disconnect(on_device_founded)

        callibri_controller.foundedDevices.connect(on_device_founded)
        callibri_controller.search_with_result(5, [])

    def connect_to_device(self, item):
        item_number = self.foundedListWidget.row(item)
        item_info=self.__founded_sensors[item_number]

        def on_device_connection_state_changed(address, state):
            item.setText(item_info.Name + ' (' + item_info.Address + '): ' + state.name)
            if address==item_info.Address and state==ConnectionState.Connected:
                self.startCalcButton.setVisible(True)
                self.stopCalcButton.setVisible(True)
                self.label_3.setVisible(True)
                self.hasRR.setVisible(True)
                self.label_4.setVisible(True)
                self.hrValue.setVisible(True)

        callibri_controller.connectionStateChanged.connect(on_device_connection_state_changed)
        callibri_controller.connect_to(info=item_info, need_reconnect=True)

    def start_calc(self):
        current_device=callibri_controller.connected_devices[0]
        def hr_values_updated(address: str, hr: float):
            if address == current_device:
                self.hrValue.setText("%.2f" % hr)


        def has_rr_picks(address: str, has_picks: bool):
            if address == current_device:
                self.hasRR.setText("Есть" if has_picks else "Нет")


        callibri_controller.hrValuesUpdated.connect(hr_values_updated)
        callibri_controller.hasRRPicks.connect(has_rr_picks)
        callibri_controller.start_calculations(current_device)

    def stop_calc(self):
        try:
            callibri_controller.hrValuesUpdated.disconnect()
            callibri_controller.hasRRPicks.disconnect()
        except Exception as err:
            print(err)
        callibri_controller.stop_calculations(callibri_controller.connected_devices[0])

app = QApplication(sys.argv)
window = MainScreen()
window.show()
app.exec()
callibri_controller.stop_all()
sys.exit()