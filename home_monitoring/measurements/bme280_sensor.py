from typing import Dict

from bme280 import BME280
from smbus import SMBus

from home_monitoring.measurement_logger import IntervalMeasurementLogger
from home_monitoring import config

LOG_KEYS = [
    "temperature",
    "pressure",
    "humidity",
]


class BME280Logger(IntervalMeasurementLogger):
    def __init__(
        self,
        measurement_config: config.MeasurementConfig,
        influxdb_config: config.InfluxDBConfig,
    ) -> None:
        super().__init__(
            measurement_config,
            influxdb_config,
        )

        bus = SMBus(1)
        self.bme280_sensor = BME280(i2c_dev=bus)

    def get_measure(self) -> Dict:
        self.bme280_sensor.update_sensor()

        return {key: getattr(self.bme280_sensor, key) for key in LOG_KEYS}
