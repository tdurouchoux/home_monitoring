from typing import Dict, List, Callable

import atexit
import time
import reactivex as rx
from datetime import timedelta

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
    ) -> None:
        self.bucket = f"{database}/{retention_policy}"
        self.username = username
        self.password = password

        self.url = f"http://{host}:{port}"

        print(self.url)

        self.client = None
        self.write_api = None

    def _connect(self, write_options: idb.WriteOptions = SYNCHRONOUS) -> None:
        # self.client = idb.InfluxDBClient(
        #     url=self.url, username=self.username, password=self.password, org="-"
        # )
        self.client = idb.InfluxDBClient(
            url=self.url, token=f"{self.username}:{self.password}", org="-"
        )
        self.write_api = self.client.write_api(write_options=write_options)

        print("Successfully connected to Database")

    def close(self) -> None:
        self.write_api.close()
        self.client.close()

        self.write_api = None
        self.client = None

    def write_measure(
        self,
        measurement: str,
        data: Dict,
        time: int = None,
        measure_tags: Dict = None,
        time_precision: str = "ns",
    ) -> None:
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
                self._connect()

            self.write_api.write(bucket=self.bucket, record=point)

        except Exception as e:
            print(f"Failed to write data point: {e}")
            self.client = None

    def write_batch_measures(
        self,
        measurement: str,
        data_points: List[Dict],
        time_points: List[int],
        measure_tags: Dict = None,
        time_precision: str = "ns",
        max_retries: int = 5,
        retry_interval: float = 0.01,
    ) -> None:
        for data, time in zip(data_points, time_points):
            for i in range(max_retries):
                self.write_measure(
                    measurement,
                    data,
                    time=time,
                    measure_tags=measure_tags,
                    time_precision=time_precision,
                )

                if self.client is not None:
                    break

                time.sleep(retry_interval)

    def periodic_measures(
        self,
        measurement: str,
        get_measurement: Callable,
        time_interval: int,
        measure_tags: Dict = None,
    ) -> None:
        measure_info = {"measurement": measurement}

        if measure_tags is not None:
            measure_info["tags"] = measure_tags

        def format_measure() -> Dict:
            measure = {"fields": get_measurement()}
            measure.update(measure_info)
            return measure

        readings = rx.interval(period=timedelta(seconds=time_interval)).pipe(
            rx.operators.map(lambda i: format_measure())
        )

        if self.client is not None:
            self.close()

        self._connect(write_options=idb.WriteOptions(batch_size=1))

        self.write_api.write(bucket=self.bucket, record=readings)

        atexit.register(self.close)

        input()
