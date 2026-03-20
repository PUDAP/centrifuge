from __future__ import annotations

import time

from centrifuge import Centrifuge

WS_URL = "ws://192.168.5.111:81"


def run_sequence(device: str) -> None:
    centri = Centrifuge(ws_url=WS_URL)

    try:
        print("startup:", centri.startup())
        print("mac:", centri.get_mac_address())
        print("position:", centri.get_position())

        print("open_lid:", centri.open_lid(device))
        print("close_lid:", centri.close_lid(device))

        print(f"spin device {device}")
        centri.spin(device)
        time.sleep(3)

        print(f"stop device {device}")
        centri.stop(device)
    finally:
        centri.close()


if __name__ == "__main__":
    run_sequence("1")
    # Uncomment if you also want to run device 2:
    # run_sequence("2")
