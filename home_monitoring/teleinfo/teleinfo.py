from typing import Dict
import logging

import reactivex as rx
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring.utils import logger_factory, handle_errors_observable
from home_monitoring.teleinfo.teleinfo_connector import TeleinfoConnector
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector

MEASUREMENT_NAME = "teleinfo"


def monitor_teleinfo(
    influxdb_config: Dict,
    scheduler: ThreadPoolScheduler,
    serial_port: str,
    nb_retry: int = 3,
    log_file: str = None,
    log_level=logging.INFO,
) -> None:
    if log_file is not None:
        logger = logger_factory("teleinfo", log_file, log_level=log_level)
    else:
        logger = logging

    logger.info("Setting up teleinfo monitoring ...")

    teleinfo_connector = TeleinfoConnector(serial_port, logger=logger)

    logger.info("Setting up influxdb connection ...")

    influxdb_connector = InfluxDBConnector(
        influxdb_config["database"],
        influxdb_config["username"],
        influxdb_config["password"],
        logger=logger,
    )

    logger.info(f"Creating teleinfo observable ... ")

    teleinfo_obs = teleinfo_connector.create_observable()
    teleinfo_obs = teleinfo_obs.pipe(rx.operators.subscribe_on(scheduler))
    teleinfo_obs = handle_errors_observable(teleinfo_obs, nb_retry, logger=logger)

    logger.info("Observable setted up.")

    influxdb_connector.write_observable(MEASUREMENT_NAME, teleinfo_obs)

    logger.info(f"Launching {MEASUREMENT_NAME} measures ...")
