import click

from home_monitoring.sensorhub.sensor_connector import SensorConnector
from home_monitoring.influxdb.influxdb_connector import InfluxDBConnector

INFLUX_DATABASE = "home_monitor"


@click.command()
@click.argument("period", default=60)
@click.option("--database", defautl)
def main():
    sensor_connector = SensorConnector()

    influxdb_connector = InfluxDBConnector("test", "admin", "dashmaster")

    influxdb_connector.periodic_measures(
        "test_sensorhub", sensor_connector.get_all_sensors, period
    )


if __name__ == "__main__":
    main()
