import os
import click
import yaml
import logging

from home_monitoring.sensorhub import sensorhub


@click.command()
@click.argument("config_file")
def main(config_file: str) -> None:
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    influxdb_config = config["influxdb"]
    log_directory = config["log_directory"]

    for measurement, m_config in config["measurements"].items():
        if "log_file" in m_config:
            log_file = log_file = os.path.join(log_directory, m_config["log_file"])

            if "log_level" in m_config:
                log_level = getattr(logging, m_config["log_level"].upper())
            else:
                log_level = logging.INFO

        else:
            log_file = None
            log_level = None

        if measurement == "sensorhub":
            sensorhub.monitor_sensors(
                influxdb_config,
                m_config["period"],
                log_file=log_file,
                log_level=log_level,
            )

    input()


if __name__ == "__main__":
    main()
