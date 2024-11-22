import queue
from threading import Thread
from typing import List

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from neurosdk.callibri_sensor import CallibriSensor
from neurosdk.scanner import Scanner
from neurosdk.sensor import Sensor
from neurosdk.cmn_types import *
from callibri_ecg.callibri_ecg_lib import CallibriMath


class ConnectionState(Enum):
    Connection = 0
    Connected = 1
    Disconnection = 2
    Disconnected = 3
    Error = 4


@dataclass
class CallibriInfo:
    Name: str
    Address: str
    sensor_info: SensorInfo


class CallibriAdditional:
    def __init__(self, need_reconnect: bool, sensor: CallibriSensor):
        self.need_reconnect: bool = need_reconnect
        self.is_signal=False
        self.callibri: CallibriSensor = sensor
        self.ecg_math: CallibriMath = CallibriMath(1000, int(500), 30)
        self.ecg_math.init_filter()
        self.buf_size = int(1000 / 10)
        self.signal_data = queue.Queue()


class Worker(QObject):
    finished = pyqtSignal()

    def __init__(self, work):
        super().__init__()
        self.work = work

    def run(self):
        self.work()
        self.finished.emit()


class CallibriController(QObject):
    connectionStateChanged = pyqtSignal(str, ConnectionState)
    batteryChanged = pyqtSignal(str, int)
    hrValuesUpdated = pyqtSignal(str, float)
    hasRRPicks = pyqtSignal(str, bool)
    foundedDevices = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.__scanner = Scanner([SensorFamily.LECallibri, SensorFamily.LEKolibri])
        self.__connected_devices = {}
        self.__disconnected_devices = list()
        self.connected_devices = list()
        self.thread = None
        self.worker = None

    def search_with_result(self, seconds: int, addresses: List[str]):
        def __device_scan():
            self.__scanner.start()
            QThread.sleep(seconds)
            self.__scanner.stop()
            founded = self.__scanner.sensors()
            filtered_sensors = []
            for si in founded:
                if len(addresses) < 1 or si.Address in addresses:
                    filtered_sensors.append(CallibriInfo(Name=si.Name,
                                                         Address=si.Address,
                                                         sensor_info=si))
            self.foundedDevices.emit(filtered_sensors)

        self.thread = QThread()
        self.worker = Worker(__device_scan)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def connect_to(self, info: CallibriInfo, need_reconnect: bool = False):
        self.connectionStateChanged.emit(info.Address, ConnectionState.Connection)

        def __device_connection():
            sensor = None
            try:
                sensor = self.__scanner.create_sensor(info.sensor_info)
            except Exception as err:
                print(err)
            try:
                if sensor is not None:
                    sensor.signal_type=CallibriSignalType.ECG
                    sensor.sampling_frequency = SensorSamplingFrequency.FrequencyHz1000
                    sensor.hardware_filters = [SensorFilter.HPFBwhLvl1CutoffFreq1Hz,
                                               SensorFilter.BSFBwhLvl2CutoffFreq45_55Hz,
                                               SensorFilter.BSFBwhLvl2CutoffFreq55_65Hz]
                    sensor.sensorStateChanged = self.__connection_state_changed
                    sensor.batteryChanged = self.__battery_changed
                    self.__connected_devices.update({info.Address: CallibriAdditional(need_reconnect, sensor)})
                    self.connected_devices.append(info.Address)
                    self.connectionStateChanged.emit(info.Address, ConnectionState.Connected)
                else:
                    self.connectionStateChanged.emit(info.Address, ConnectionState.Error)
            except Exception as err:
                print(err)

        self.thread = QThread()
        self.worker = Worker(__device_connection)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.thread.start()

    def __event_sensor_founded(self, scanner: Scanner, sensors: List[SensorInfo]):
        scanner.stop()
        for si in sensors:
            if si.Address in self.__disconnected_devices:
                self.__connected_devices[si.Address].callibri.connect()
                if self.__connected_devices[si.Address].callibri.state != SensorState.StateInRange:
                    scanner.start()
                else:
                    if self.__connected_devices[si.Address].is_signal:
                        self.__execute_command(self.__connected_devices[si.Address].bb, SensorCommand.StartSignal)
                    self.__disconnected_devices.remove(si.Address)
                return
        if len(self.__disconnected_devices) > 0:
            scanner.start()

    def __connection_state_changed(self, sensor: Sensor, state: SensorState):
        self.connectionStateChanged.emit(sensor.address,
                                         ConnectionState.Connected if state == SensorState.StateInRange else ConnectionState.Disconnected)
        if state == SensorState.StateOutOfRange and sensor.address in self.__connected_devices.keys() and self.__connected_devices[
            sensor.address].need_reconnect:
            self.__disconnected_devices.append(sensor.address)
            self.__scanner.sensorsChanged = self.__event_sensor_founded
            self.__scanner.start()

    def __battery_changed(self, sensor: Sensor, battery: int):
        self.batteryChanged.emit(sensor.address, battery)

    def disconnect_from(self, address: str):
        self.connectionStateChanged.emit(address, ConnectionState.Disconnection)
        if address in self.__disconnected_devices:
            self.__disconnected_devices.remove(address)
            if len(self.__disconnected_devices) < 1:
                self.__scanner.stop()
        sens = self.__connected_devices[address]
        self.__connected_devices.pop(address)
        self.connected_devices.remove(address)
        sens.callibri.disconnect()
        sens.callibri = None

    def start_calculations(self, address: str):
        def on_signal_received(sensor: Sensor, data: List[CallibriSignalData]):
            try:
                math = self.__connected_devices[address].ecg_math
                buf_size = self.__connected_devices[address].buf_size
                buffer = self.__connected_devices[address].signal_data

                for sample in data:
                    for value in sample.Samples:
                        buffer.put(value)
                if buffer.qsize() > buf_size:
                    raw_data = [buffer.get() for _ in range(buf_size)]
                    math.push_data(raw_data)
                    math.process_data_arr()
                    rr_detected = math.rr_detected()
                    self.hasRRPicks.emit(sensor.address, rr_detected)
                    if rr_detected:
                        hr = math.get_hr()
                        self.hrValuesUpdated.emit(sensor.address, hr)
            except Exception as err:
                print(err)

        self.__connected_devices[address].callibri.signalDataReceived = on_signal_received
        self.__execute_command(self.__connected_devices[address].callibri, SensorCommand.StartSignal)
        self.__connected_devices[address].is_signal = True

    def stop_calculations(self, address: str):
        self.__connected_devices[address].callibri.signalDataReceived = None
        self.__execute_command(self.__connected_devices[address].callibri, SensorCommand.StopSignal)
        self.__connected_devices[address].is_signal = False

    def __execute_command(self, sensor: Sensor, command: SensorCommand):
        def execute_command():
            try:
                sensor.exec_command(command)
            except Exception as err:
                print(err)

        thread = Thread(target=execute_command)
        thread.start()

    def stop_all(self):
        self.__scanner.stop()
        self.__scanner.sensorsChanged = None
        self.__scanner = None

        for device in self.__connected_devices.values():
            device.callibri.disconnect()
            device.callibri.sensorStateChanged = None
            device.callibri.batteryChanged = None
            device.callibri = None
        self.__connected_devices.clear()
        self.connected_devices.clear()
        self.__disconnected_devices.clear()

callibri_controller = CallibriController()