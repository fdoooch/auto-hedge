from binance.error import ClientError
from app.utils.get_ip import get_external_ip
from binance.um_futures import UMFutures
import logging

from app.core.positions_repository import PositionsRepository
from app.core.config import settings
from app.core.models import Position, SymbolReport

logger = logging.getLogger(settings.LOGGER_NAME)


def fetch_positions_from_exchange(client: UMFutures) -> list[Position]:
    try:
        positions_data = client.get_position_risk(recvWindow=6000)
        logger.debug(positions_data)
        # positions_data = pos
        positions = [
            Position(
                exchange="binance_futures",
                symbol=positions_data["symbol"].upper(),
                qty=float(positions_data["positionAmt"]),
                side=positions_data["positionSide"],
                unrealized_pnl=positions_data["unRealizedProfit"],
            )
            for positions_data in positions_data
        ]
        return positions
    except ClientError as error:
        if error.error_code == -2015:
            ip = get_external_ip()
            logger.error(
                f"{error.error_code}: {error.error_message}. Add ip to the exchange white list: {ip}"
            )
            return []
        logger.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        return []

def cover_uncovered_positions(client: UMFutures, repo: PositionsRepository, hedge_pnl_threshold: float = 0.0) -> None:
    actual_positions = fetch_positions_from_exchange(client=client)
    logger.debug(f"Actual positions: {len(actual_positions)}")
    if len(actual_positions) == 0:
        repo.clear_positions()
        return None

    # print("\nActual positions:")
    # for position in actual_positions:
    #     print(position)

    symbols_reports = _calculate_symbols_reports(actual_positions)

    # print("\nNon-zero balances and pnls:")
    for symbol, report in symbols_reports.items():
        # print(f"BALANCE| {symbol}: {balance}")
        logger.debug(report)

        hedge_position = repo.get_position_by_exchange_and_symbol(exchange="binance_futures", symbol=symbol)
        logger.debug(f"hedge_position: {hedge_position}")

        if not hedge_position:
            if report.long_pnl + report.short_pnl < 0:
                open_hedge_position(repo=repo, client=client, symbol=symbol, balance=report.balance)
            continue

        if hedge_position.side == "LONG":
            if report.short_pnl >= 0:
                close_hedge_position(repo=repo, client=client, position=hedge_position)
                continue

            if report.balance == 0:
                continue

            elif report.balance > 0:
                close_hedge_position(repo=repo, client=client, position=hedge_position)
                continue

            elif report.balance < 0:
                logger.debug(f"RECOVER LONG: {report}")
                recover_hedge_position(repo=repo, client=client, position=hedge_position, balance=report.balance)
                continue


        if hedge_position.side == "SHORT":
            if report.long_pnl >= 0:
                close_hedge_position(repo=repo, client=client, position=hedge_position)
                continue

            if report.balance == 0:
                continue

            elif report.balance > 0:
                logger.debug(f"RECOVER SHORT: {report}")
                recover_hedge_position(repo=repo, client=client, position=hedge_position, balance=report.balance)
                continue

            elif report.balance < 0:
                close_hedge_position(repo=repo, client=client, position=hedge_position)
                continue


    # print(f"\nREPO: {repo.get_positions()}")


def open_hedge_position(repo: PositionsRepository, client: UMFutures, symbol: str, balance: float) -> bool:
    side = "SELL" if balance > 0 else "BUY"
    position_side = "SHORT" if balance > 0 else "LONG"
    qty = abs(balance)
    try:
        client.new_order(
            symbol=symbol.upper(),
            side=side,
            positionSide=position_side,
            type="MARKET",
            quantity=qty,
        )
        repo.add_or_update_position(
            Position(
                exchange="binance_futures",
                symbol=symbol.upper(),
                qty=qty,
                side=position_side,
                unrealized_pnl=None,
            )
        )
        logger.info(f"HEDGE OPENED for {symbol}, qty: {qty}, side: {position_side}")
        return True
    except ClientError as error:
        logger.error(
            f"HEDGE OPENING ERROR for {symbol}. status: {error.status_code}, error code: {error.error_code}, error message: {error.error_message}"
        )
        return False


def recover_hedge_position(repo: PositionsRepository, client: UMFutures, position: Position, balance: float) -> bool:
    logger.debug(f"Recovering position: {position}")
    side = "SELL" if balance > 0 else "BUY"
    position_side = "SHORT" if balance > 0 else "LONG"
    qty = abs(balance)
    try:
        client.new_order(
            symbol=position.symbol,
            side=side,
            positionSide=position_side,
            type="MARKET",
            quantity=qty,
        )
        repo.add_or_update_position(
            Position(
                exchange="binance_futures",
                symbol=position.symbol,
                qty=qty + position.qty,
                side=position_side,
                unrealized_pnl=None,
            )
        )
        logger.info(f"HEDGE RECOVERED for {position.symbol}, qty: {qty}, side: {position_side}")
        return True
    except ClientError as error:
        logger.error(
            f"HEDGE RECOVERING ERROR for {position.symbol}. status: {error.status_code}, error code: {error.error_code}, error message: {error.error_message}"
        )
        return False


def close_hedge_position(repo: PositionsRepository, client: UMFutures, position: Position) -> bool:
    try:
        client.new_order(
            symbol=position.symbol,
            side="SELL" if position.side == "LONG" else "BUY",
            positionSide=position.side,
            type="MARKET",
            quantity=abs(position.qty),
        )
        repo.remove_position(position)
        logger.info(f"HEDGE CLOSED for {position.symbol}")
        return True
    except ClientError as error:
        logger.error(
            f"HEDGE CLOSING ERROR for {position.symbol}. status: {error.status_code}, error code: {error.error_code}, error message: {error.error_message}"
        )
        return False


def _calculate_symbols_reports(actual_positions: list[Position]) -> dict[str, SymbolReport]:
    symbols_reports = {}
    for position in actual_positions:
        long_qty=position.qty if position.side == "LONG" else 0
        short_qty=position.qty if position.side == "SHORT" else 0
        long_pnl=position.unrealized_pnl if position.side == "LONG" else 0
        short_pnl=position.unrealized_pnl if position.side == "SHORT" else 0
        if position.symbol not in symbols_reports:
            symbols_reports[position.symbol] = SymbolReport(
                symbol=position.symbol,
                long_qty=long_qty,
                short_qty=-short_qty,
                long_pnl=long_pnl,
                short_pnl=short_pnl,
            )
        else:
            symbols_reports[position.symbol].long_qty += long_qty
            symbols_reports[position.symbol].short_qty -= short_qty
            symbols_reports[position.symbol].long_pnl += long_pnl
            symbols_reports[position.symbol].short_pnl += short_pnl

    return symbols_reports