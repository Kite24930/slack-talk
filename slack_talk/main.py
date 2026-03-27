"""Entry point for slack-talk backend."""

import argparse
import asyncio
import logging

from slack_talk.app import App, create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("slack_talk")


def main() -> None:
    parser = argparse.ArgumentParser(description="slack-talk backend")
    parser.add_argument(
        "--db",
        default="slack_talk.db",
        help="SQLiteデータベースパス",
    )
    parser.add_argument(
        "--ws-port",
        type=int,
        default=9321,
        help="WebSocketポート",
    )
    args = parser.parse_args()

    logger.info("slack-talk starting...")
    asyncio.run(_run(args.db, args.ws_port))


async def _run(db_path: str, ws_port: int) -> None:
    app = await create_app(db_path=db_path, ws_port=ws_port)
    await app.start()
    logger.info("slack-talk finished")


if __name__ == "__main__":
    main()
