from home_monitoring.sensor_publisher import SensorPublisher

from .bme280_sensor import BME280Publisher
from .bme680_sensor import BME680Publisher
from .system_usage import SystemUsagePublisher
from .teleinfo import TeleinfoPublisher

SENSORS: dict[str, SensorPublisher] = {
    "bme280": BME280Publisher,
    "bme680": BME680Publisher,
    "system_usage": SystemUsagePublisher,
    "teleinfo": TeleinfoPublisher,
}
