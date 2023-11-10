from datetime import datetime
import json
from typing import Dict, List
import pandas as pd
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from starlette import status
from starlette.middleware.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from nifty.repositories.base_repository import IRepository
from nifty.repositories.nifty_repository import NiftyRepository

nifty_repository:IRepository = None

async def price_data(request: Request) -> JSONResponse:
    """
    Return price data for the requested symbol
    """
    # 1) Return open, high, low & close prices for the requested symbol as json records
    # 2) Allow calling app to filter the data by year using an optional query parameter
        # Symbol data is stored in the file data/nifty50_all.csv
    # 3) Check if the symbol is valid.
    # 4) sort by date desc order
    symbol = request.path_params['symbol'].upper()
    year = request.query_params.get('year', None)
    if year is not None and not year.isdigit():
        return JSONResponse({"error": "Invalid year"}, status_code=status.HTTP_400_BAD_REQUEST)
    if not nifty_repository.symbol_exists(symbol) or symbol is None:
        return JSONResponse({"error": "Invalid symbol"}, status_code=status.HTTP_400_BAD_REQUEST)
    stock_prices = nifty_repository.filter(symbol, year)
    return JSONResponse(stock_prices)

async def add_price_data(request : Request) -> JSONResponse:
    symbol = request.path_params['symbol'].upper()
    try:
        stock_prices = await request.json()
    except json.JSONDecodeError:
        return JSONResponse({'error': 'Invalid json'}, status_code=status.HTTP_400_BAD_REQUEST)
    # Validate the JSON body
    if not isinstance(stock_prices, list):
        return JSONResponse({"error": "Invalid input, expected list"}, status_code=status.HTTP_400_BAD_REQUEST)

    # Create a list of PriceUpdate objects

    for stock_price in stock_prices:
        error = validate(symbol, stock_price)
        if error:
            return error
    #doing a separate for loop for inserts as we can
    #as we want to finish validate before doing part inserts
    try:
        for stock_price in stock_prices:
            nifty_repository.add(symbol, stock_price)
    except Exception as ex:
        return JSONResponse({"error": f"Failed to insert due to internal exception {str(ex)}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse({"result" : f"successfully added {len(stock_prices)} record(s)"}, status_code=status.HTTP_201_CREATED)

# URL routes
app = Starlette(debug=True, routes=[
    Route('/nifty/stocks/{symbol}', price_data, methods=['GET']),
    Route('/nifty/stocks/{symbol}', add_price_data, methods=['POST'])
])

def is_valid_date(string):
  try:
    date_tuple = datetime.strptime(string, '%d/%m/%Y').isocalendar()
    if date_tuple is not None:
      return True
    else:
      return False
  except ValueError:
    return False

def validate(symbol: str, stock_price:Dict)-> None:
    relevent_keys = set(key for key in stock_price.keys())
    if relevent_keys != set(['open', 'close', 'high', 'low', 'date']):
        return JSONResponse({"error": f"Expected only 'open', 'close', 'high', 'low', 'date' in body {stock_price}"}, status_code=status.HTTP_400_BAD_REQUEST) 
    if not is_valid_date(stock_price["date"]):
        return JSONResponse({"error": f"date not valid in {stock_price['date']}"}, status_code=status.HTTP_400_BAD_REQUEST)
    stock_price_date = datetime.strptime(stock_price["date"], "%d/%m/%Y").date()
    if nifty_repository.symbol_date_exists(symbol=symbol, dt=stock_price_date):
        return JSONResponse({"error": f"No update allowed, record already for {symbol} and {stock_price['date']}"}, status_code=status.HTTP_400_BAD_REQUEST)
    range = nifty_repository.range_check(symbol, stock_price_date, 50)
    keys = ['open', 'close', 'high', 'low']
    for key in keys:
        input = float(stock_price[key])
        max = range["max"][key]
        min = range["min"][key]
        if max is not None and min is not None and input <= max and input >= min:
            continue
        else:
            return JSONResponse({"error": f"standard deviation for {key} not in range as {stock_price[key]} is not between {max} and {min} (both inclusive)"}, status_code=status.HTTP_400_BAD_REQUEST)

@app.on_event('startup')
async def startup_event():
    global nifty_repository
    # Loading Nifty50 data from csv file at startup
    nifty_repository = NiftyRepository("data/nifty50_all.csv") 
                               

@app.on_event('shutdown')
async def shutdown_event():
    global nifty_repository   
    nifty_repository.backup("data/nifty50_all_backup.csv")

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content=str(exc.detail))


@app.exception_handler(Exception)
async def general_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": f"{base_error_message}. Detail: {str(err)}"},
    )


def main() -> None:
    """
    start the server
    """
    uvicorn.run(app, host='0.0.0.0', port=8888)

if __name__ == "__main__":
    # Entry point
    main()
