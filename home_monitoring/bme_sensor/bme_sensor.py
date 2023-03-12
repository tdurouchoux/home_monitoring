from typing import Dict
import logging

from datetime import timedelta
import reactivex as rx

from home_monitoring.utils import logger_factory, handle_errors_observable
from home_monitoring.bme_sensor import bme680
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector

MEASUREMENT_NAME = "bme688"

LOG_KEYS = [
    "status",
    "heat_stable",
    "temperature",
    "pressure",
    "humidity",
    "gas_resistance",
]


def set_up_sensor(sensor: bme680.BME680) -> None:
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)

    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)


def get_sensor_measures(sensor: bme680.BME680) -> Dict:
    sensor.get_sensor_data()

    data = sensor.data.__dict__

    return {key: value for key, value in data.items() if key in LOG_KEYS}


def monitor_sensor(
    influxdb_config: Dict,
    period: int,
    nb_retry: int = 2,
    log_file: str = None,
    log_level=logging.INFO,
) -> None:
    if log_file is not None:
        logger = logger_factory("bm688", log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up bme688 sensor ...")

    sensor = bme680.BME680()
    set_up_sensor(sensor)

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    logger.info(f"Creating bme688 observable taking measurement every {period} seconds")

    sensor_obs = rx.interval(period=timedelta(seconds=period)).pipe(
        rx.operators.map(lambda i: get_sensor_measures(sensor))
    )
    sensor_obs = handle_errors_observable(sensor_obs, nb_retry, logger=logger)

    influxdb_connector.write_observable(MEASUREMENT_NAME, sensor_obs)

    logger.info(f"Launching {MEASUREMENT_NAME} measures ...")
