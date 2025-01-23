from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import logging


from app.core.config import settings



def main():
    config_logging(logging, logging.DEBUG)
    try:
        client = UMFutures(
            key=settings.binance.API_KEY,
            secret=settings.binance.API_SECRET,
            base_url="https://fapi.binance.com",
        )
        client.new_order(
            symbol="TWTUSDT".upper(),
            side="SELL",
            positionSide="LONG",
            type="MARKET",
            quantity=25,
        )
        
    except ClientError as error:
        logging.error(error)
        return


if __name__ == "__main__":
    main()  