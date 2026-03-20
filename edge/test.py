from __future__ import annotations

import time

from centrifuge import Centrifuge

WS_URL = "ws://192.168.5.111:81"


def run_sequence(device: str) -> None:
    centri = Centrifuge(ws_url=WS_URL)

    try:
        centri.startup()
        centri.get_mac_address()
        centri.get_position()

        centri.open_lid(device)
        centri.close_lid(device)

        centri.spin(device)
        time.sleep(3)

        centri.stop(device)
    finally:
        centri.close()


if __name__ == "__main__":
    run_sequence("1")
    # Uncomment if you also want to run device 2:
    # run_sequence("2")
