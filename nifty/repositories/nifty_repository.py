from abc import ABCMeta
from datetime import date, datetime
import sys
from typing import Dict, List
import pandas as pd

from nifty.repositories.base_repository import IRepository


class NiftyRepositorySingletonMeta(ABCMeta):
    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance
    
class NiftyRepository(IRepository, metaclass=NiftyRepositorySingletonMeta):
    
    def __init__(self, path) -> None:
        self.date_format="%Y-%m-%d"
        # TODO:
        # 1. Move the path of csv, schema to env file so that it is configurable
        # 2. Move nifty repository to be in AWS S3 or Datalake and query using pyspark
        self.nifty_records = pd.read_csv(path, 
                               dtype={"Symbol": str, "Close": float, "Open": float, "High": float, "Low": float}, 
                               parse_dates=["Date"], date_format=self.date_format)
        # add calculated column year so that i can use it for faster query later
        self.nifty_records['Year'] = self.nifty_records["Date"].apply(lambda date: date.year)
        # lets cleanup if there is a duplicate record and kee the last one
        self.nifty_records.drop_duplicates(subset=["Date", "Symbol"], keep="last", inplace=True)
        # also lets sort well in advance because when select queries will be fired the data 
        # is pre sorted
        self.nifty_records.sort_values(by=["Date", "Symbol"], ascending=False, inplace=True)        

    def symbol_exists(self, symbol:str)->bool:
        return symbol in self.nifty_records["Symbol"].unique()

    def symbol_date_exists(self, symbol:str, dt:date)->bool:
        date_in_format = datetime(dt.year, dt.month, dt.day)
        query_string = f"Symbol == '{symbol}' and Date == '{pd.to_datetime(date_in_format)}'"  
        return len(self.nifty_records.query(query_string)) > 0

    def add(self, symbol:str, record:Dict)->bool:
        dt = datetime.strptime(record["date"], "%d/%m/%Y")
        new_row = {
                    "Symbol": symbol, 
                    "Date" : pd.to_datetime(dt),
                    "Open" : record["open"],
                    "Close": record["close"],
                    "High": record["high"],
                    "Low": record["low"],
                    "Year" : dt.year # this is important as this was calculated field
                }
        location = len(self.nifty_records)
        self.nifty_records.loc[location] = new_row
        self.nifty_records.sort_values(by=["Date"], ascending=False, inplace=True)
        return True

    def filter(self, symbol:str, year:int = None) -> List:
        query_string = f"Symbol == '{symbol}'"
        if year is not None:
            query_string += f" and Year == {year}"        
        records = self.nifty_records.query(query_string).copy()
        if records is not None:
            records.sort_values(by=["Date"], ascending=False, inplace=True)
            records["Date"] = pd.to_datetime(records["Date"]).dt.strftime('%d/%m/%Y')
            records.drop(columns=["Year", "Symbol"], inplace=True)
            records.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Date" : "date"}, inplace=True)
            return records.to_dict(orient="records")
        return []
    
    def range_check(self, symbol:str, dt: date, take:int):
        date_in_format = datetime(dt.year, dt.month, dt.day)
        query_string = f"Symbol == '{symbol}' and Date < '{pd.to_datetime(date_in_format)}'"       
        records = self.nifty_records.query(query_string).copy()
        if records is not None:
            records.sort_values(by=["Date"], ascending=False, inplace=True)
            records["Date"] = pd.to_datetime(records["Date"]).dt.strftime('%d/%m/%Y')
            records.drop(columns=["Year", "Symbol"], inplace=True)
            records.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Date" : "date"}, inplace=True)
            qualified =  records.iloc[0:take]
            if qualified is not None and len(qualified) != 0:
                min_range = { "open" : qualified["open"].mean() - qualified["open"].std(), 
                            "close" : qualified["close"].mean() - qualified["close"].std(), 
                            "high" : qualified["high"].mean() - qualified["high"].std(), 
                            "low" : qualified["low"].mean() - qualified["low"].std() }
                max_range = { "open" : qualified["open"].mean() + qualified["open"].std(), 
                            "close" : qualified["close"].mean() + qualified["close"].std(), 
                            "high" : qualified["high"].mean() + qualified["high"].std(), 
                            "low" : qualified["low"].mean() + qualified["low"].std() }
                return { "max": max_range, "min" : min_range }          
        return { 
                "max": { "open" : None, "close" : None, "high" : None, "low" : None }, 
                "min" : { "open" : None, "close" : None, "high" : None, "low" : None } 
               }

    
    def backup(self, path):
        # Save the updated Nifty50 data to CSV file.
        # Not saving to original file so that for test completeness,
        # we can do file diff and see if we have extra records
        self.nifty_records.drop(columns=["Year"], inplace=True)
        self.nifty_records.to_csv(path, index=False)