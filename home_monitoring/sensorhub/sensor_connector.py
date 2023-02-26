import smbus
import time

import logging

DEVICE_BUS = 1
DEVICE_ADDR = 0x17

TEMP_REG = 0x01
LIGHT_REG_L = 0x02
LIGHT_REG_H = 0x03
STATUS_REG = 0x04
ON_BOARD_TEMP_REG = 0x05
ON_BOARD_HUMIDITY_REG = 0x06
ON_BOARD_SENSOR_ERROR = 0x07
BMP280_TEMP_REG = 0x08
BMP280_PRESSURE_REG_L = 0x09
BMP280_PRESSURE_REG_M = 0x0A
BMP280_PRESSURE_REG_H = 0x0B
BMP280_STATUS = 0x0C
HUMAN_DETECT = 0x0D


class SensorConnector:
    def __init__(self):
        self.bus = smbus.SMBus(DEVICE_BUS)

    def _get_off_chip_temp(self, sensors_status):
        if sensors_status & 0x01:
            logging.warning("Off-chip temperature sensor overrange !")
            return None
        elif sensors_status & 0x02:
            logging.error("No external temperature sensor !")
            return None
        else:
            return self.bus.read_byte_data(DEVICE_ADDR, TEMP_REG)

    def _get_brightness(self, sensors_status):
        if sensors_status & 0x04:
            logging.warning("Onboard brightness sensor overrange !")
            return 0
        elif sensors_status & 0x08:
            logging.error("Onboard brightness sensor failure !")
            return 0
        else:
            return self.bus.read_byte_data(
                DEVICE_ADDR, LIGHT_REG_H
            ) << 8 | self.bus.read_byte_data(DEVICE_ADDR, LIGHT_REG_L)

    def _get_on_chip_hum_sensor(self):
        if self.bus.read_byte_data(DEVICE_ADDR, ON_BOARD_SENSOR_ERROR) != 0:
            logging.warning(
                "Onboard temperature and humidity sensor data may not be up to date !"
            )

        temp_on_chip = self.bus.read_byte_data(DEVICE_ADDR, ON_BOARD_TEMP_REG)
        humidity = self.bus.read_byte_data(DEVICE_ADDR, ON_BOARD_HUMIDITY_REG)

        return temp_on_chip, humidity

    def _get_pressure_sensor(self):
        if self.bus.read_byte_data(DEVICE_ADDR, BMP280_STATUS) != 0:
            logging.error("Onboard barometer works abnormally!")

        temp_barometer = self.bus.read_byte_data(DEVICE_ADDR, BMP280_TEMP_REG)
        pressure = (
            self.bus.read_byte_data(DEVICE_ADDR, BMP280_PRESSURE_REG_L)
            | self.bus.read_byte_data(DEVICE_ADDR, BMP280_PRESSURE_REG_M) << 8
            | self.bus.read_byte_data(DEVICE_ADDR, BMP280_PRESSURE_REG_H) << 16
        )
        pressure /= 100000

        return temp_barometer, pressure

    def _get_movement_detection(self):
        return bool(self.bus.read_byte_data(DEVICE_ADDR, HUMAN_DETECT))

    def get_all_sensors(self):
        logging.debug("Starting sensors data aquisition")

        sensors_dict = {}

        sensors_status = self.bus.read_byte_data(DEVICE_ADDR, STATUS_REG)

        sensors_dict["TempOffchip"] = self._get_off_chip_temp(sensors_status)

        sensors_dict["Brightness"] = self._get_brightness(sensors_status)

        (
            sensors_dict["TempOnChip"],
            sensors_dict["Humidity"],
        ) = self._get_on_chip_hum_sensor()

        (
            sensors_dict["TempBaromter"],
            sensors_dict["Pressure"],
        ) = self._get_pressure_sensor()

        sensors_dict["HumanDetected"] = self._get_movement_detection()

        logging.debug("Sensors Data aquisition finished")

        return sensors_dict
