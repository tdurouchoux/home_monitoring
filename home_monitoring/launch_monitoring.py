import os
import logging
import time
from typing import Dict

import click
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring.measurements import MEASUREMENTS
from home_monitoring import config


@click.command()
@click.argument("config_directory")
def main(config_directory: str) -> None:
    logger_config, monitoring_config = config.load_config(config_directory)
    influxdb_config = monitoring_config.Influxdb
    measurements_config = monitoring_config.measurements

    logging.config.dictConfig(logger_config)
    logger = logger.getLogger("main")

    logger.info("Starting monitoring:")
    logger.info(
        "InfluxDB configuration : %s",
        {
            "database": influxdb_config.database,
            "host": influxdb_config.host,
            "port": influxdb_config.host,
        },
    )

    logger.info("Setting up measurements ... ")

    scheduler = ThreadPoolScheduler(len(measurements_config))

    for measurement in measurements_config:
        logger.info("Setting up measurement %s ...", measurement.name)

        measurement_logger = MEASUREMENTS[measurement.implement](
            measurement, influxdb_config
        )
        measurement_logger.create_observable(scheduler)
        measurement_logger.start_monitoring()

    while True:
        time.sleep(10_000)


if __name__ == "__main__":
    main()
