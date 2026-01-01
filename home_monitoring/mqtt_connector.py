import json
import logging
from typing import Any, Optional

import paho.mqtt.client as mqtt
import reactivex as rx
from reactivex import operators as ops
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from home_monitoring.config import MQTTConfig


class MQTTConnector:
    """
    MQTT connector for publishing sensor measurements.

    Supports flexible payload formats (JSON, raw strings, binary, etc.)
    and automatic reconnection with exponential backoff using tenacity.
    """

    def __init__(self, mqtt_config: MQTTConfig, topic_suffix: str) -> None:
        """
        Initialize the MQTT connector.

        Args:
            mqtt_config (MQTTConfig): MQTT configuration.
            topic_suffix (str): Topic suffix for publishing messages.
        """
        self.mqtt_config = mqtt_config
        self.client_id = topic_suffix.replace("/", "-")
        self.topic = f"{self.mqtt_config.base_topic}/{topic_suffix}"

        self.logger = logging.getLogger(self.client_id)

        # Connection state
        self.client: Optional[mqtt.Client] = None
        self.connected = False

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connection is established"""
        if rc == 0:
            self.connected = True
            self.logger.info(
                f"Successfully connected to MQTT broker at {self.mqtt_config.broker}:{self.mqtt_config.port}"
            )
        else:
            self.connected = False
            self.logger.error(f"Failed to connect to MQTT broker: {rc.name}")
            raise ConnectionError(rc.name)

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected"""
        self.connected = False
        if rc != 0:
            self.logger.warning(
                f"Unexpected disconnection from MQTT broker (code {rc})"
            )
        else:
            self.logger.info("Disconnected from MQTT broker")

    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        self.logger.debug(f"Message {mid} published successfully")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=120),
        retry=retry_if_exception_type((ConnectionError, OSError, TimeoutError)),
        # before_sleep=before_sleep_log(self.logger, logging.WARNING),
        reraise=True,
    )
    def connect(self) -> None:
        """
        Establish connection to MQTT broker with automatic retry.

        Uses tenacity for exponential backoff:
        - Retries up to 10 times
        - Wait time: 1s, 2s, 4s, 8s, 16s, 32s, 64s, 120s, 120s, 120s
        - Only retries on connection errors
        """
        self.logger.info(
            f"Attempting connection to MQTT broker at {self.mqtt_config.broker}:{self.mqtt_config.port}..."
        )

        # ! MISSING client id

        # Create MQTT client (using v3.1.1 for better compatibility)
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish

        # Set authentication if provided
        if (
            self.mqtt_config.username is not None
            and self.mqtt_config.password is not None
        ):
            self.client.username_pw_set(
                self.mqtt_config.username, self.mqtt_config.password
            )

        # Set TLS if enabled
        # if self.use_tls:
        #     if self.ca_certs:
        #         self.client.tls_set(ca_certs=self.ca_certs)
        #     else:
        #         self.client.tls_set()  # Use default CA certificates

        # Connect to broker
        self.client.connect(
            self.mqtt_config.broker, self.mqtt_config.port, keepalive=60
        )
        self.client.loop_start()
        self.connected = True

    def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        if self.client is not None:
            self.logger.info("Disconnecting from MQTT broker...")
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            self.connected = False

    @staticmethod
    def serialize_payload(data: Any) -> str | bytes | bytearray | None:
        """
        Serialize payload to bytes (used as RxPY operator).

        Args:
            data: Data to serialize (dict, str, int, float, bytes, etc.)

        Returns:
            Serialized payload as bytes
        """

        if data is None:
            return None

        if isinstance(data, (bytes, bytearray)):
            return data

        if isinstance(data, (dict, list)):
            # Convert bytearray to bytes
            return json.dumps(data).encode("utf-8")

        # Convert to string then bytes
        return str(data).encode("utf-8")

    def publish_message(
        self,
        data: str | bytes | bytearray | None,
        qos: int,
        retain: bool,
    ) -> None:
        """
        Publish a single measurement to MQTT.

        Args:
            measurement: Measurement name (used in topic if no template)
            data: Data to publish (dict, str, int, float, bytes, etc.)
            qos: Quality of service level (MQTT)
            retain: Retain flag
        """

        self.logger.debug(
            "Publishing message %s to MQTT broker for %s ...", data, self.topic
        )

        # Ensure connected
        if self.client is None or not self.connected:
            self.connect()

        # Publish message
        try:
            result = self.client.publish(
                topic=self.topic, payload=data, qos=qos, retain=retain
            )

        # ? Create publish error

        except Exception as e:
            self.logger.warning(f"Failed to publish data point with error: {e}")
            self.connected = False
            raise e
            # Check if publish was successful

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            self.logger.error(
                "Failed to publish message to %s, rc=%s", self.topic, result.rc.name
            )
            raise Exception(
                f"Failed to publish message to {self.topic}, rc={result.rc.name}"
            )

    def setup_publishing(
        self,
        measures_obs: rx.Observable,
        qos: int = 1,
        retain: bool = False,
    ) -> rx.Observable:
        """
        Subscribe to an observable and publish measurements to MQTT.

        Args:
            measures_obs: Observable emitting measurement data
            qos: Quality of service level for MQTT messages
            retain: Retain flag for MQTT messages

        Returns:
            Observable with serialization and publishing operations added
        """
        self.logger.info(f"Setting up observable for %s ...", self.client_id)

        # Ensure connection
        if self.client is None or not self.connected:
            self.connect()

        # Build the reactive pipeline
        publish_pipeline = measures_obs.pipe(
            # Step 1: Serialize data to bytes
            ops.map(self.serialize_payload),
            # Step 2: Publish to MQTT (side effect),
            ops.do_action(on_next=lambda data: self.publish_message(data, qos, retain)),
        )

        return publish_pipeline
