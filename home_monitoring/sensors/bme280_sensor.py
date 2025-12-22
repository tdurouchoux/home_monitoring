from bme280 import BME280
from smbus import SMBus

from home_monitoring import config
from home_monitoring.sensor_publisher import IntervalSensorPublisher

LOG_KEYS = [
    "temperature",
    "pressure",
    "humidity",
]


class BME280Publisher(IntervalSensorPublisher):
    def __init__(
        self,
        sensor_config: config.SensorConfig,
        mqtt_config: config.MQTTConfig,
    ) -> None:
        super().__init__(
            sensor_config,
            mqtt_config,
        )

        bus = SMBus(1)
        self.bme280_sensor = BME280(i2c_dev=bus)

    def get_measure(self) -> dict:
        self.bme280_sensor.update_sensor()

        return {key: getattr(self.bme280_sensor, key) for key in LOG_KEYS}
