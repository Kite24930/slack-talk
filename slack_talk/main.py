"""Entry point for slack-talk backend."""

import asyncio
import logging

from slack_talk.app import App

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("slack_talk")


def main() -> None:
    logger.info("slack-talk starting...")
    asyncio.run(_run())


async def _run() -> None:
    app = App(services=[])
    await app.start()
    logger.info("slack-talk finished")


if __name__ == "__main__":
    main()
