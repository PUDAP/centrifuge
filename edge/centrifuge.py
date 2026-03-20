"""Centrifuge websocket driver with automatic reconnection."""

from __future__ import annotations

from re import L
import time
import logging
from typing import Optional
import websocket

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
        """Connect to the centrifuge machine via websocket."""
        self._connect()
        logger.info("Centrifuge machine connected successfully")

    def close(self) -> None:
        """Close websocket connection if it exists."""
        if self._ws is not None:
            try:
                self._ws.close()
                logger.debug("Websocket disconnected")
            finally:
                self._ws = None

    def get_mac_address(self) -> str:
        """Return current device MAC address."""
        mac = self._command("@", response=True)
        logger.info("MAC address: %s", mac)
        return mac

    def get_position(self) -> str:
        """Return current lid position."""
        position = self._command("?", response=True)
        logger.info("Position: %s", position)
        return position
    
    def home(self) -> None:
        """Homes the centrifuge machine."""
        self.open_lid("1")
        self.open_lid("2")
        logger.info("Centrifuge machine homed successfully")

    def open_lid(self, device: str) -> None:
        """Open lid for centrifuge device
        
        Args:
            device: The device to open the lid of ("1" or "2")

        Raises:
            ValueError: If the device is not "1" or "2"
            Exception: If the lid cannot be opened
        """
        device = self._validate_device(device)
        try:
            self._command(
                f"H{device}",
                wait_for_success={"Ok", f"Homed{device}"},
                wait_for_failure={f"Timeout{device}"},
            )
            logger.info("Lid %s opened successfully", device)
        except Exception:
            logger.error("Failed to open lid %s", device)
            raise

    def close_lid(self, device: str) -> None:
        """Close lid for centrifuge device

        Args:
            device: The device to close the lid of ("1" or "2")

        Raises:
            ValueError: If the device is not "1" or "2"
            Exception: If the lid cannot be closed
        """
        device = self._validate_device(device)
        try:
            self._command(f"#{device}050", wait_for_success="Ok")
            logger.info("Lid %s closed successfully", device)
        except Exception:
            logger.error("Failed to close lid %s", device)
            raise

    def spin(self, device: str, duration: float) -> None:
        """Spin centrifuge device for the given duration in seconds.
        
        Args:
            device: The device to spin ("1" or "2")
            duration: The duration to spin the device for in seconds

        Raises:
            ValueError: If the device is not "1" or "2"
            Exception: If the device cannot be spun
        """
        device = self._validate_device(device)
        self._command(f"~{device}1")
        logger.info("Spin device %s for %.1fs", device, duration)
        time.sleep(duration)
        self._command(f"~{device}0")
        logger.info("Device %s stopped", device)

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
        return str(message).strip()

    def _with_retry(self, action):
        for attempt in range(1, self.max_retries + 1):
            try:
                return action()
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

    def _command(
        self,
        command: str,
        *,
        retry: bool = True,
        response: bool = False,
        wait_for_success: str | set[str] | None = None,
        wait_for_failure: str | set[str] | None = None,
    ) -> str:
        """Send a command and return the result.

        Args:
            retry: Reconnect and retry on connection failures.
            response: Command returns a response without echoing first.
            wait_for_success: Block until one of these success responses is received.
            wait_for_failure: If one of these is received instead, raise an error.
        """
        def action():
            self._send(command)
            if response:
                return self._recv()
            return self._recv()

        result = self._with_retry(action) if retry else action()

        if wait_for_success is not None:
            return self._wait_for(command, wait_for_success, wait_for_failure)
        return result

    def _wait_for(
        self,
        command: str,
        success: str | set[str],
        failure: str | set[str] | None = None,
        timeout_s: float = 30.0,
    ) -> str:
        """Read responses until a success or failure message is received."""
        success_targets = success if isinstance(success, set) else {success}
        failure_targets = failure if isinstance(failure, set) else {failure} if failure else set()
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            try:
                resp = self._recv()
            except websocket.WebSocketTimeoutException:
                logger.debug("Command %s still waiting...", command)
                continue
            if any(s in resp for s in success_targets):
                return resp
            if any(f in resp for f in failure_targets):
                raise RuntimeError(
                    f"Command {command} failed with: {resp}"
                )
            logger.debug("Command %s in progress: %s", command, resp)
        raise TimeoutError(
            f"Command {command} did not receive any of {success_targets!r} within {timeout_s}s"
        )