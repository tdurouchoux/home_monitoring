from bme280 import BME280
from smbus import SMBus

from home_monitoring import config
from home_monitoring.sensor_publisher import IntervalSensorPublisher


class BME280Publisher(IntervalSensorPublisher):
    MODEL: str = "BME280"
    MESSAGE_CONTENT: dict[str, dict] = {
        "temperature": {
            "name": "Temperature",
            "device_class": "temperature",
            "state_class": "measurement",
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.temperature }}",
        },
        "pressure": {
            "name": "Pressure",
            "device_class": "atmospheric_pressure",
            "state_class": "measurement",
            "unit_of_measurement": "hPa",
            "value_template": "{{ value_json.pressure }}",
        },
        "humidity": {
            "name": "Humidity",
            "device_class": "humidity",
            "state_class": "measurement",
            "unit_of_measurement": "%",
            "value_template": "{{ value_json.humidity }}",
        },
    }

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

        return {key: getattr(self.bme280_sensor, key) for key in self.MESSAGE_CONTENT}
