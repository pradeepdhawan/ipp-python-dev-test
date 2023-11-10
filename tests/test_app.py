import pytest
import json 
from datetime import datetime
from starlette.testclient import TestClient
from nifty.__main__ import app
from nifty.repositories.base_repository import IRepository
from nifty.repositories.nifty_repository import NiftyRepository

client = TestClient(app)

@pytest.fixture
def mock_repository(monkeypatch):
    # intentionally not mocking NiftyRepository so that we test 
    # both main and NiftyRepository
    patch_on = NiftyRepository("data/nifty50_all.csv")
    monkeypatch.setattr("nifty.__main__.nifty_repository", patch_on)

INVALID_YEAR="2003ABC"
@pytest.mark.parametrize("symbol, year, length, expected_status_code", [
    ('TATAMOTORS', None,4307, 200),
    (None, None, 1, 400), # becuase error is also json
    ('INVALID_SYMBOL', None,1, 400), # becuase error is also json
    ('TATAMOTORS', '2003',4, 200), # valid year
    ('TATAMOTORS', '2099',0, 200), # year with no records
    ('TATAMOTORS', INVALID_YEAR,1, 400), # invalid year with no records
])
def test_price_data(symbol, year, length, expected_status_code, mock_repository):
    suffix = f"/?year={year}" if year else ""
    response = client.get(f"/nifty/stocks/{symbol}" + suffix)
    assert response.status_code == expected_status_code
    if response.status_code == 200:
        assert isinstance(response.json(), list)
    assert len(json.loads(response.content.decode("utf-8"))) == length

@pytest.mark.parametrize("symbol, data, expected_status_code", [
    ('TATAMOTORS', [{"date": "11/08/2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}], 201),
    ('TATAMOTORS', [{"date": "11/08/2023", "open": 550, "high": 560, "low": 545, "close": 555}], 400),  # standard daviation > 1
    ('TATAMOTORS', [{"date": "2023/01/01", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}], 400),  # date not valid format. no 31st month
    ('TATAMOTORS', [{"date": "02/31/2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}], 400),  # date not valid format. should be dd/mm/yyyy
    ('TATAMOTORS', [{"date": "01-01-2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}], 400),  # date should be dd/mm/yyyy
    ('TATAMOTORS', [{"date": "01-01-2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}], 400),  # date should be dd/mm/yyyy  
    ('TATAMOTORS', [{"date": "01/01/2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6, "extra" : 333}], 400), # no extra other than OPEN, CLOSE, HIGH, LOW
     ('TATAMOTORS', [{"date": "26/12/2003", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}], 400) # update not allowed as "26/12/2003" already exists
])
def test_add_price_data(symbol, data, expected_status_code, mock_repository):
    response = client.post(f"/nifty/stocks/{symbol}", json=data)
    assert response.status_code == expected_status_code


def test_add_price_data_and_check_count_of_record(mock_repository):
    symbol = 'TATAMOTORS'

    initial_response = client.get(f"/nifty/stocks/{symbol}")
    initial_data = initial_response.json()
    initial_record_count = len(initial_data)

    new_data = {"date": "14/08/2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}

    add_response = client.post(f"/nifty/stocks/{symbol}", json=[new_data])

    assert add_response.status_code == 201

    # Query the data again
    final_response = client.get(f"/nifty/stocks/{symbol}")
    final_data = final_response.json()

    assert len(final_data) == initial_record_count + 1

def test_add_price_data_multiple_and_check_count_of_record(mock_repository):
    symbol = 'TATAMOTORS'

    initial_response = client.get(f"/nifty/stocks/{symbol}")
    initial_data = initial_response.json()
    initial_record_count = len(initial_data)

    new_data_1 = {"date": "14/09/2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}
    new_data_2 = {"date": "15/09/2023", "open": 312.0, "high": 330.45, "low": 311.1, "close": 323.6}
    add_response = client.post(f"/nifty/stocks/{symbol}", json=[new_data_1, new_data_2])

    assert add_response.status_code == 201

    # Query the data again
    final_response = client.get(f"/nifty/stocks/{symbol}")
    final_data = final_response.json()

    assert len(final_data) == initial_record_count + 2


def test_price_data_sorted_by_date_desc(mock_repository):
    symbol = 'TATAMOTORS'
    response = client.get(f"/nifty/stocks/{symbol}")

    assert response.status_code == 200

    data = response.json()
    assert data

    dates = [datetime.strptime(entry['date'], "%d/%m/%Y") for entry in data]

    # Check if the dates are sorted in descending order
    assert all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1))
