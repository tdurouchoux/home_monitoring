from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing_extensions import Dict

import reactivex as rx

from home_monitoring import config
from home_monitoring.influxdb_connector import InfluxDBConnector

logger = logging.getLogger(__name__)


@dataclass
class MeasurementLogger(ABC):
    def __init__(
        self,
        measurement_config: config.MeasurementConfig,
        influxdb_config: config.InfluxDBConfig,
    ) -> None:
        self.measurement_config = measurement_config

        self.influxdb_connector = InfluxDBConnector(**influxdb_config.__dict__)

        self.measure_obs: rx.Observable = None

    @abstractmethod
    def create_observable(self, scheduler) -> None:
        pass

    def handle_errors_observable(self) -> None:
        def catch_error(e, observable):
            logger.error(
                "Observable %s stopped after %s try.",
                self.measurement_config.name,
                self.measurement_config.nb_retry_measure,
            )

            return rx.empty()

        self.measure_obs = self.measure_obs.pipe(
            rx.operators.do_action(
                on_error=lambda e: logger.warning(
                    "Observable %s got following error : %s",
                    self.measurement_config.name,
                    e,
                )
            ),
            rx.operators.retry(self.measurement_config.nb_retry_measure),
            rx.operators.catch(handler=catch_error),
        )

    def start_monitoring(self) -> None:
        self.handle_errors_observable()

        logger.info("Launching %s measures ...", self.measurement_config.name)

        self.influxdb_connector.write_observable(
            self.measurement_config.name,
            self.measure_obs,
            **self.measurement_config.write_options.__dict__,
        )


class IntervalMeasurementLogger(MeasurementLogger):
    @abstractmethod
    def get_measure(self) -> Dict:
        pass

    def create_observable(self, scheduler):
        logger.info(
            "Creating time observable for measurement %s "
            "taking measurement every %s seconds.",
            self.measurement_config.name,
            self.measurement_config.period,
        )

        self.measure_obs = rx.interval(
            period=timedelta(seconds=self.measurement_config.period)
        ).pipe(
            rx.operators.map(lambda _: self.get_measure()),
            rx.operators.subscribe_on(scheduler),
        )
