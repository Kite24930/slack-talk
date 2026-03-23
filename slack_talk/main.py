"""Entry point for slack-talk backend."""

import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("slack_talk")


def main() -> None:
    logger.info("slack-talk starting...")
    asyncio.run(_run())


async def _run() -> None:
    # App クラスは Task 4 で実装
    logger.info("slack-talk running (no services registered yet)")


if __name__ == "__main__":
    main()
