"""Centrifuge websocket driver with automatic reconnection."""

from __future__ import annotations

import time
from typing import Optional
import websocket
import logging

logger = logging.getLogger(__name__)


class Centrifuge:
    """Driver for communicating with the centrifuge over websocket."""

    def __init__(
        self,
        ws_url: str,
        *,
        connect_timeout_s: float = 5.0,
        max_retries: int = 3,
        retry_delay_s: float = 1.0,
    ) -> None:
        self.ws_url = ws_url
        self.connect_timeout_s = connect_timeout_s
        self.max_retries = max_retries
        self.retry_delay_s = retry_delay_s
        self._ws: Optional[websocket.WebSocket] = None

    def startup(self) -> str:
        """Open websocket connection and return device greeting."""
        self._connect()
        return self._recv()

    def close(self) -> None:
        """Close websocket connection if it exists."""
        if self._ws is not None:
            try:
                self._ws.close()
            finally:
                self._ws = None

    def get_mac_address(self) -> str:
        """Return current device MAC address data."""
        _, data = self._request("@", wait_for_response=True)
        logger.info("MAC address: %s", data)
        return data or "no data received"

    def get_position(self) -> str:
        """Return current lid position data."""
        _, data = self._request("?", wait_for_response=True)
        logger.info("Position: %s", data)
        return data or "no data received"

    def open_lid(self, device: str) -> str:
        """
        Open lid for centrifuge device
        
        params:
          - device: str - the device to open the lid of ("1" or "2")
        """
        device = self._validate_device(device)
        _, status = self._request(f"H{device}", wait_for_completion=True)
        
        if status == "Ok":
            logger.info("Lid %s opened successfully", device)
        else:
            logger.error("Failed to open lid %s, status: %s", device, status)
            raise RuntimeError(f"Failed to open lid for device {device}: status={status!r}")

    def close_lid(self, device: str) -> str:
        """
        Close lid for centrifuge device 1 or 2.

        Returns status response (expected "Ok" when movement is done).
        """
        device = self._validate_device(device)
        _, status = self._request(f"#{device}050", wait_for_completion=True)
        
        if status == "Ok":
            logger.info("Lid %s closed successfully", device)
        else:
            logger.error("Failed to close lid %s, status: %s", device, status)
            raise RuntimeError(f"Failed to close lid for device {device}: status={status!r}")

    def spin(self, device: str):
        """Start spinning centrifuge device 1 or 2 and return echo."""
        device = self._validate_device(device)
        self._request(f"~{device}1")

    def stop(self, device: str) -> str:
        """
        Stop spinning centrifuge
        
        params:
          - device: str - the device to stop ("1" or "2")
        """
        device = self._validate_device(device)
        self._request(f"~{device}0")
      

    # Private methods

    def _validate_device(self, device: str) -> str:
        if device in {"1", "2"}:
            return device
        raise ValueError("device must be '1' or '2'")

    def _connect(self) -> None:
        self.close()
        ws = websocket.WebSocket()
        ws.connect(self.ws_url, timeout=self.connect_timeout_s)
        self._ws = ws

    def _ensure_connected(self) -> None:
        if self._ws is None:
            self._connect()

    def _send(self, command: str) -> None:
        self._ensure_connected()
        assert self._ws is not None
        self._ws.send(command)

    def _recv(self) -> str:
        self._ensure_connected()
        assert self._ws is not None
        message = self._ws.recv()
        return str(message)

    def _request(
        self,
        command: str,
        wait_for_response: bool = False,
        wait_for_completion: bool = False,
    ) -> tuple[str, Optional[str]]:
        for attempt in range(1, self.max_retries + 1):
            try:
                self._send(command)
                echo = self._recv()
                response = self._recv() if (wait_for_response or wait_for_completion) else None
                if wait_for_completion:
                    while response and response.startswith("Homing"):
                        logger.info("Command %s in progress: %s; waiting...", command, response)
                        time.sleep(self.retry_delay_s)
                        response = self._recv()
                return echo, response
            except (
                websocket.WebSocketConnectionClosedException,
                websocket.WebSocketTimeoutException,
                websocket.WebSocketException,
                OSError,
            ):
                if attempt >= self.max_retries:
                    raise
                self._connect()
                time.sleep(self.retry_delay_s)

        raise RuntimeError("unreachable")