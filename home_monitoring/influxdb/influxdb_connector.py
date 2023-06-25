from typing import Dict, List, Callable

import atexit
import time
import reactivex as rx
import logging


import influxdb_client as idb
from influxdb_client.client.write_api import SYNCHRONOUS


class InfluxDBConnector:
    def __init__(
        self,
        database: str,
        username: str,
        password: str,
        retention_policy="autogen",
        host="localhost",
        port=8086,
        logger=logging,
    ) -> None:
        self.bucket = f"{database}/{retention_policy}"
        self.username = username
        self.password = password

        self.url = f"http://{host}:{port}"

        self.client = None
        self.write_api = None

        self.logger = logger

    def _connect(self, write_options: idb.WriteOptions = SYNCHRONOUS) -> None:
        self.logger.info(
            f"Attempting connection to Influxdb database with url {self.url} ..."
        )

        self.client = idb.InfluxDBClient(
            url=self.url, token=f"{self.username}:{self.password}", org="-"
        )
        self.write_api = self.client.write_api(write_options=write_options)

        self.logger.info("Successfully connected to Database")

    def close(self) -> None:
        self.logger.info("Closing connection with Influxdb database.")

        self.write_api.close()
        self.client.close()

        self.write_api = None
        self.client = None

    # batch size
    def write_measure(
        self,
        measurement: str,
        data: Dict,
        time: int = None,
        measure_tags: Dict = None,
        time_precision: str = "ns",
        batch_size: int = 1,
    ) -> None:
        self.logger.debug("Writing measure into Influxdb database ...")

        point = idb.Point(measurement)

        if time is not None:
            point.time(time, write_precision=time_precision)

        if measure_tags is not None:
            for tag, value in measure_tags.items():
                point.tag(tag, value)

        for key, value in data.items():
            point.field(key, value)

        print(point.to_line_protocol())

        try:
            if self.client is None:
                self._connect(write_options=idb.WriteOptions(batch_size=batch_size))

            self.write_api.write(bucket=self.bucket, record=point)

            self.logger.debug("Successfully wrote datapoint into database.")

        except Exception as e:
            self.logger.warning(f"Failed to write data point: {e}")
            self.client = None

    def write_observable(
        self, measurement: str, measures_obs: rx.Observable, measure_tags: Dict = None
    ) -> None:
        self.logger.info("Setting up observable ...")

        measure_info = {"measurement": measurement}

        if measure_tags is not None:
            measure_info["tags"] = measure_tags

        def format_measures(measures: Dict) -> Dict:
            measure = {"fields": measures}
            measure.update(measure_info)
            return measure

        measures_obs = measures_obs.pipe(rx.operators.map(format_measures))

        if self.client is not None:
            self.close()

        self._connect(write_options=idb.WriteOptions(batch_size=1))

        self.write_api.write(bucket=self.bucket, record=measures_obs)

        atexit.register(self.close)

        self.logger.info("Observable setted up.")
