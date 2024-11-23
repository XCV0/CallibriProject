#ТУТ ИНТЕРФЕЙС НАШЕГО АДМИНА ДЛЯ ПРОСМОТРА ЗА СОТРУДНИКАМИ#

import requests
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.uic import loadUi

from callibri_controller import callibri_controller, ConnectionState, CallibriInfo


class MainScreen(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi("ui/AdminWindow.ui", self)

    def refresh(self):
      pass


app = QApplication(sys.argv)
window = MainScreen()
window.show()
app.exec()
callibri_controller.stop_all()
sys.exit()