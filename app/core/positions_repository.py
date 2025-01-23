import json
from app.core.models import Position

class PositionsRepository:
    def __init__(self, file_path: str):
        self.positions: dict[str, Position] = {}
        self.file_path = file_path

    def add_or_update_position(self, position: Position):
        key = f"{position.exchange.upper()}_{position.symbol.upper()}"
        self.positions[key] = position
        self.store_positions()

    def add_or_update_positions(self, positions: list[Position]):
        for position in positions:
            key = f"{position.exchange.upper()}_{position.symbol.upper()}"
            self.positions[key] = position
        self.store_positions()

    def get_positions(self) -> list[Position]:
        return list(self.positions.values())

    def get_position_by_exchange_and_symbol(self, exchange: str, symbol: str) -> Position | None:
        key = f"{exchange.upper()}_{symbol.upper()}"
        return self.positions.get(key)

    def clear_positions(self):
        self.positions = {}
        self.store_positions()

    def remove_position(self, position: Position):
        key = f"{position.exchange.upper()}_{position.symbol.upper()}"
        del self.positions[key]
        self.store_positions()

    def store_positions(self):
        positions_dict = [position.model_dump() for position in self.positions.values()]
        with open(self.file_path, 'w') as f:
            json.dump(positions_dict, f)
        

    def load_positions(self):
        try:
            with open(self.file_path, 'r') as f:
                positions_json = json.load(f)
                for position in positions_json:
                    self.add_or_update_position(Position(**position))
        except FileNotFoundError:
            self.positions = {}