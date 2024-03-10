from typing import

from home_monitoring.measurement_logger import MeasurementLogger

from .bme280_sensor import BME280Logger
from .bme680_sensor import BME680Logger
from .openweather import OpenWeatherLogger
from .sensorhub import SensorHubLogger
from .system_usage import SystemUsageLogger
from .teleinfo import TeleinfoLogger


MEASUREMENTS: Dict[str, MeasurementLogger] = {
    "bme280": BME280Logger,
    "bme680": BME680Logger,
    "openweather": OpenWeatherLogger,
    "sensorhub": SensorHubLogger,
    "system_usage": SystemUsageLogger,
    "teleinfo": TeleinfoLogger,
}
