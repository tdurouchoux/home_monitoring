from typing import Dict
import logging
from datetime import timedelta

from smbus import SMBus
from bme280 import BME280
import reactivex as rx
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring.utils import logger_factory, handle_errors_observable
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector


MEASUREMENT_NAME = "bme280"


bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)


print(f"Temperature : {bme280.get_temperature()}")
print(f"Humidity : {bme280.get_humidity()}")

LOG_KEYS = [
    "temperature",
    "pressure",
    "humidity",
]


def get_sensor_measures(sensor: BME280) -> Dict:
    sensor.update_sensor()

    return {
        "temperature": sensor.temperature,
        "pressure": sensor.pressure,
        "humidity": sensor.humidity,
    }


def monitor_sensor(
    influxdb_config: Dict,
    scheduler: ThreadPoolScheduler,
    period: int,
    nb_retry: int = 2,
    log_file: str = None,
    log_level=logging.INFO,
) -> None:
    if log_file is not None:
        logger = logger_factory("bme280", log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up bme280 sensor ...")

    bus = SMBus(1)
    sensor = BME280(i2c_dev=bus)

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    logger.info(f"Creating bme280 observable taking measurement every {period} seconds")

    sensor_obs = rx.interval(period=timedelta(seconds=period)).pipe(
        rx.operators.map(lambda i: get_sensor_measures(sensor)),
        rx.operators.subscribe_on(scheduler),
    )
    sensor_obs = handle_errors_observable(sensor_obs, nb_retry, logger=logger)

    influxdb_connector.write_observable(MEASUREMENT_NAME, sensor_obs)

    logger.info(f"Launching {MEASUREMENT_NAME} measures ...")
