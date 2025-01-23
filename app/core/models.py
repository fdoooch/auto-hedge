from pydantic import BaseModel

class Position(BaseModel):
    exchange: str
    symbol: str
    qty: float
    side: str
    unrealized_pnl: float | None = None


class SymbolReport(BaseModel):
    symbol: str
    long_qty: float
    short_qty: float
    long_pnl: float
    short_pnl: float


    @property
    def balance(self):
        return self.long_qty - self.short_qty