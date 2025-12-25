import logging
import math

import bme680

from home_monitoring import config
from home_monitoring.sensor_publisher import IntervalSensorPublisher

logger = logging.getLogger(__name__)


class BME680Publisher(IntervalSensorPublisher):
    def __init__(
        self,
        sensor_config: config.SensorConfig,
        mqtt_config: config.MQTTConfig,
    ) -> None:
        super().__init__(
            sensor_config,
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

        if not self.sensor.data.heat_stable:
            logger.info("%s sensor is not yet ready", self.sensor_config.name)

        aqi = round(
            math.log(self.sensor.data.gas_resistance)
            + 0.04 * self.sensor.data.humidity,
            1,
        )

        return {
            "temperature": self.sensor.data.temperature,
            "pressure": self.sensor.data.pressure,
            "humidity": self.sensor.data.humidity,
            "aqi": aqi,
        }
