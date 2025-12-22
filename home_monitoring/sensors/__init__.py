from typing import Dict

from home_monitoring.measurement_logger import SensorPublisher

from .bme280_sensor import BME280Publisher
from .bme680_sensor import BME680Publisher
from .system_usage import SystemUsagePublisher
from .teleinfo import TeleinfoPublisher

SENSORS: dict[str, SensorPublisher] = {
    "bme280": BME280Logger,
    "bme680": BME680Logger,
    "system_usage": SystemUsageLogger,
    "teleinfo": TeleinfoLogger,
}
