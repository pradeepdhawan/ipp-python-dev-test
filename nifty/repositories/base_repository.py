from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List

class IRepository(ABC):

    @abstractmethod
    def symbol_exists(self, symbol:str) -> bool:
        pass

    @abstractmethod
    def symbol_date_exists(self, symbol:str, dt:date) -> bool:
        pass

    @abstractmethod
    def add(self, symbol:str, record:Dict) -> bool:
        pass

    @abstractmethod
    def filter(self, symbol:str, year:int) -> List:
        pass

    @abstractmethod
    def range_check(self, symbol:str, dt:date, take:int) -> bool:
        pass
