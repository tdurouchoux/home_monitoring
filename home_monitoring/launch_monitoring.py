import logging
import logging.config
import os
import time
from pathlib import Path
from typing import Dict

import click
from dotenv import load_dotenv
from reactivex.scheduler import ThreadPoolScheduler

from home_monitoring import config
from home_monitoring.sensors import SENSORS

load_dotenv()


@click.command()
@click.argument("config_directory")
def main(config_directory: str) -> None:
    logger_config, monitoring_config = config.load_config(Path(config_directory))
    mqtt_config = monitoring_config.mqtt
    measurements_config = monitoring_config.measurements

    logging.config.dictConfig(logger_config)
    logger = logging.getLogger("main")

    logger.info("Starting monitoring:")
    logger.info(
        "MQTT configuration: %s",
        {
            "broker": mqtt_config.broker,
            "port": mqtt_config.port,
            "base_topic": mqtt_config.base_topic,
            "qos": mqtt_config.qos,
        },
    )

    logger.info("Setting up measurements ... ")

    scheduler = ThreadPoolScheduler(len(measurements_config))

    for measurement in measurements_config:
        logger.info("Setting up measurement %s ...", measurement.name)

        sensor_publisher = SENSORS[measurement.implement](measurement, mqtt_config)
        sensor_publisher.create_observable(scheduler)
        sensor_publisher.start_monitoring()

    while True:
        time.sleep(10_000)


if __name__ == "__main__":
    main()
