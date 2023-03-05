from typing import Dict
import logging

from home_monitoring.utils import logger_factory
from home_monitoring.sensorhub.sensor_connector import SensorConnector
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector

MEASUREMENT_NAME = "sensorhub"


def monitor_sensors(
    influxdb_config: Dict,
    period: int,
    log_file: str = None,
    log_level=logging.INFO,
):
    if log_file is not None:
        logger = logger_factory("sensorhub", log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up sensorhub connection ...")

    sensor_connector = SensorConnector(logger=logger)

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    influxdb_connector.periodic_measures(
        MEASUREMENT_NAME, sensor_connector.get_all_sensors, period
    )

    logger.info(f"Launching {MEASUREMENT_NAME} measures ...")