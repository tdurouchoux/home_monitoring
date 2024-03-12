import math
from typing import Dict

import bme680

from home_monitoring.measurement_logger import IntervalMeasurementLogger
from home_monitoring import config

LOG_KEYS = ["status", "heat_stable", "temperature", "pressure", "humidity", "aqi"]


class BME680Logger(IntervalMeasurementLogger):
    def __init__(
        self,
        measurement_config: config.MeasurementConfig,
        influxdb_config: config.InfluxDBConfig,
    ) -> None:
        super().__init__(
            measurement_config,
            influxdb_config,
        )

        self.bme680_sensor = bme680.BME680()
        self.setup_sensor()

    def setup_sensor(self) -> None:
        self.bme680_sensor.set_humidity_oversample(bme680.OS_2X)
        self.bme680_sensor.set_pressure_oversample(bme680.OS_4X)
        self.bme680_sensor.set_temperature_oversample(bme680.OS_8X)
        self.bme680_sensor.set_filter(bme680.FILTER_SIZE_3)

        self.bme680_sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.bme680_sensor.set_gas_heater_temperature(320)
        self.bme680_sensor.set_gas_heater_duration(150)
        self.bme680_sensor.select_gas_heater_profile(0)

    def get_measure(self) -> Dict:
        self.bme680_sensor.get_sensor_data()

        measure = self.bme680_sensor.data.__dict__.copy()

        measure["aqi"] = round(
            math.log(measure["gas_resistance"]) + 0.04 * measure["humidity"], 1
        )

        return {key: value for key, value in measure.items() if key in LOG_KEYS}
