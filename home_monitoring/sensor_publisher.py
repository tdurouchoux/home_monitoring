import atexit
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import reactivex as rx
from reactivex import operators as ops

from home_monitoring import config
from home_monitoring.mqtt_connector import MQTTConnector

logger = logging.getLogger(__name__)


@dataclass
class SensorPublisher(ABC):
    def __init__(
        self,
        sensor_config: config.SensorConfig,
        mqtt_config: config.MQTTConfig,
    ) -> None:
        self.sensor_config = sensor_config
        self.mqtt_connector = MQTTConnector(
            mqtt_config, client_id=f"{sensor_config.type}-{sensor_config.name}"
        )
        self.measure_obs: rx.Observable = None

    @abstractmethod
    def create_observable(self, scheduler) -> None:
        pass

    def start_monitoring(self) -> None:
        def catch_error(e, observable):
            logger.error(
                "Observable %s stopped after %s try.",
                self.sensor_config.name,
                self.sensor_config.nb_retry_measure,
            )

            return rx.empty()

        # Register cleanup on exit
        atexit.register(self.mqtt_connector.disconnect)

        logger.info("Launching %s measures ...", self.sensor_config.name)

        publish_pipeline = self.mqtt_connector.setup_publishing(
            self.sensor_config.name,
            self.sensor_config.location,
            self.measure_obs,
            qos=self.sensor_config.qos,
            retain=self.sensor_config.retain,
        )

        publish_pipeline = publish_pipeline.pipe(
            ops.do_action(
                on_error=lambda e: logger.warning(
                    "Observable %s got following error : %s",
                    self.sensor_config.name,
                    e,
                )
            ),
            ops.retry(self.sensor_config.nb_retry_measure),
            ops.catch(handler=catch_error),
        )

        publish_pipeline.subscribe(
            on_error=lambda e: logger.error(
                f"Fatal error for {self.sensor_config.name}: {e}"
            )
        )


class IntervalSensorPublisher(SensorPublisher):
    BUFFER_OPS = {
        "sum": sum,
        "avg": lambda x: sum(x) / len(x),
        "min": min,
        "max": max,
    }

    def __init__(
        self,
        sensor_config: config.SensorConfig,
        mqtt_config: config.MQTTConfig,
    ):
        super().__init__(sensor_config, mqtt_config)

        if self.sensor_config.period is None:
            raise ValueError("Missing 'period' parameter in sensor configuration")

        if self.sensor_config.buffer_time is not None:
            if self.sensor_config.buffer_op is None:
                logger.warning(
                    "No buffer operation specified for sensor %s defaulting to 'avg'",
                    self.sensor_config.name,
                )
                self.sensor_config.buffer_op = "avg"
            elif self.sensor_config.buffer_op not in self.BUFFER_OPS:
                raise ValueError(
                    f"Invalid buffer operation: {self.sensor_config.buffer_op}"
                )

    @abstractmethod
    def get_measure(self) -> Any:
        pass

    def _aggregate_buffer(self, buffer: list[Any]) -> Any:
        logger.debug("Aggregating buffer: %s", buffer)

        if len(buffer) == 0:
            return None

        if isinstance(buffer[0], dict):
            return {
                key: self.BUFFER_OPS[self.sensor_config.buffer_op](
                    [item[key] for item in buffer]
                )
                for key in buffer[0].keys()
            }

        return self.BUFFER_OPS[self.sensor_config.buffer_op](buffer)

    def create_observable(self, scheduler):
        logger.info(
            "Creating time observable for measurement %s "
            "taking measurement every %s seconds.",
            self.sensor_config.name,
            self.sensor_config.period,
        )

        self.measure_obs = rx.interval(
            period=timedelta(seconds=self.sensor_config.period)
        ).pipe(
            ops.map(lambda _: self.get_measure()),
            ops.observe_on(scheduler),
            ops.subscribe_on(scheduler),
        )

        if self.sensor_config.buffer_time is not None:
            self.measure_obs = self.measure_obs.pipe(
                ops.buffer_with_time(self.sensor_config.buffer_time),
                ops.map(self._aggregate_buffer),
            )
