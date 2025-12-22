import logging
import math

import bme680

from home_monitoring import config
from home_monitoring.measurement_logger import IntervalSensorPublisher

LOG_KEYS = ["status", "heat_stable", "temperature", "pressure", "humidity", "aqi"]

logger = logging.getLogger(__name__)


class BME680Publisher(IntervalSensorPublisher):
    def __init__(
        self,
        measurement_config: config.MeasurementConfig,
        mqtt_config: config.MQTTConfig,
    ) -> None:
        super().__init__(
            measurement_config,
            mqtt_config,
        )

        self.sensor = bme680.BME680()
        self.setup_sensor()

    def setup_sensor(self) -> None:
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)

        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)

    def get_measure(self) -> dict | None:
        self.sensor.get_sensor_data()

        if not self.sensor.data.heat_stable():
            logger.info("%s sensor is not yet ready", self.__qualname__)

        measure["aqi"] = round(
            math.log(measure["gas_resistance"]) + 0.04 * measure["humidity"], 1
        )

        return {key: value for key, value in measure.items() if key in LOG_KEYS}
