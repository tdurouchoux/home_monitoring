import atexit
from datetime import datetime
import logging
from typing import Dict

import influxdb_client as idb
from influxdb_client.client.write_api import SYNCHRONOUS
import reactivex as rx

logger = logging.getLogger(__name__)


class InfluxDBConnector:
    def __init__(
        self,
        database: str,
        username: str,
        password: str,
        retention_policy="autogen",
        host="localhost",
        port=8086,
    ) -> None:
        self.bucket = f"{database}/{retention_policy}"
        self.username = username
        self.password = password

        self.url = f"http://{host}:{port}"

        self.client = None
        self.write_api = None

    # TODO configure max_retries and batch_size
    def _connect(self, write_options: idb.WriteOptions = SYNCHRONOUS) -> None:
        logger.info(
            f"Attempting connection to Influxdb database with url {self.url} ..."
        )

        self.client = idb.InfluxDBClient(
            url=self.url, token=f"{self.username}:{self.password}", org="-"
        )
        self.write_api = self.client.write_api(write_options=write_options)

        logger.info("Successfully connected to Database")

    def close(self) -> None:
        logger.info("Closing connection with Influxdb database.")

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
        **write_options,
    ) -> None:
        logger.debug("Writing measure into Influxdb database ...")

        point = idb.Point(measurement)

        if time is not None:
            point.time(time, write_precision=time_precision)

        if measure_tags is not None:
            for tag, value in measure_tags.items():
                point.tag(tag, value)

        for key, value in data.items():
            point.field(key, value)

        try:
            if self.client is None:
                self._connect(write_options=idb.WriteOptions(**write_options))

            self.write_api.write(bucket=self.bucket, record=point)

            logger.debug("Successfully wrote datapoint into database.")

        except Exception as e:
            logger.warning(f"Failed to write data point with error: {e}")
            self.client = None

    def write_observable(
        self,
        measurement: str,
        measures_obs: rx.Observable,
        measure_tags: Dict = None,
        **write_options,
    ) -> None:
        logger.info("Setting up observable ...")

        measure_info = {"measurement": measurement}

        if measure_tags is not None:
            measure_info["tags"] = measure_tags

        def format_measures(measures: Dict) -> Dict:
            measure = {"fields": measures, "time": datetime.utcnow()}
            measure.update(measure_info)
            return measure

        measures_obs = measures_obs.pipe(rx.operators.map(format_measures))

        if self.client is not None:
            self.close()

        self._connect(write_options=idb.WriteOptions(**write_options))

        self.write_api.write(bucket=self.bucket, record=measures_obs)

        atexit.register(self.close)

        logger.info("Observable setted up.")
