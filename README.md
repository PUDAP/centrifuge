# centrifuge

Edge service for the Centrifuge machine.

## What It Does

- Runs the centrifuge machine edge service.
- Connects to NATS and translates commands into machine actions.
- Communicates with the centrifuge device over the network (IP).

## Prerequisites

- Docker and Docker Compose installed
- Python 3.14+ and `uv` (for baremetal mode)
- centrifuge device reachable on the network

## Environment Setup

```bash
cp .env.example .env
```

Edit `.env` and configure:

- `MACHINE_ID`
- `NATS_SERVERS`
- `WS_URL`

## Run With Docker (Recommended)

Build and start:

```bash
docker compose up -d --build
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

## Run Baremetal (uv)

```bash
uv sync
uv run python main.py
```

## Build and Push Image (GHCR)

Login:

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

Build:

```bash
docker compose build
```

Push:

```bash
docker push ghcr.io/PUDAP/centrifuge-edge:latest
```

Or with Compose:

```bash
docker compose push
```
