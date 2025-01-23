from binance.um_futures import UMFutures

import logging
import time

from app.core.config import settings
from app.core.positions_repository import PositionsRepository
from app.core.hedge_manager import cover_uncovered_positions

logger = logging.getLogger(settings.LOGGER_NAME)


def main() -> None:
    logger.info("Starting auto-hedge")
    positions_repo = PositionsRepository(f"{settings.TMP_DIR}/hedged_positions.json")
    positions_repo.load_positions()

    um_futures_client = UMFutures(
        key=settings.binance.API_KEY,
        secret=settings.binance.API_SECRET,
        base_url="https://fapi.binance.com",
    )
    
    while True:
        try:
            cover_uncovered_positions(
                client=um_futures_client,
                repo=positions_repo,
            )
            time.sleep(1)



        except KeyboardInterrupt:
            break

    logger.info("Auto-hedge stopped")



if __name__ == "__main__":
    main()
