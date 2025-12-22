import atexit
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import reactivex as rx

from home_monitoring import config
from home_monitoring.mqtt_connector import MQTTConnector

logger = logging.getLogger(__name__)


@dataclass
class SensorPublisher(ABC):
    def __init__(
        self,
        measurement_config: config.MeasurementConfig,
        mqtt_config: config.MQTTConfig,
    ) -> None:
        self.measurement_config = measurement_config
        self.mqtt_connector = MQTTConnector(mqtt_config)
        self.measure_obs: rx.Observable = None

    @abstractmethod
    def create_observable(self, scheduler) -> None:
        pass

    def start_monitoring(self) -> None:
        def catch_error(e, observable):
            logger.error(
                "Observable %s stopped after %s try.",
                self.measurement_config.name,
                self.measurement_config.nb_retry_measure,
            )

            return rx.empty()

        # Register cleanup on exit
        atexit.register(self.mqtt_connector.disconnect)

        logger.info("Launching %s measures ...", self.measurement_config.name)

        publish_pipeline = self.mqtt_connector.setup_publishing(
            self.measurement_config.name,
            self.measurement_config.location,
            self.measure_obs,
            qos=self.measurement_config.qos,
            retain=self.measurement_config.retain,
        )

        publish_pipeline = publish_pipeline.pipe(
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

        publish_pipeline.subscribe(
            on_error=lambda e: logger.error(
                f"Fatal error for {self.measurement_config.name}: {e}"
            )
        )


class IntervalSensorPublisher(SensorPublisher):
    @abstractmethod
    def get_measure(self) -> Any:
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
