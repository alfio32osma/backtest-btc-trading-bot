import pytest
import pandas as pd
from pathlib import Path
from src.data_loader import load_and_clean_data, resample_data

@pytest.fixture
def sample_csv_path(tmp_path):
    #Create a new csv file temporally with standard data just for proofs.
    d = tmp_path / "sub"
    d.mkdir()
    file_path = d / "test_btc.csv"

    # proof data with column names in uppercase with spaces to proof the cleaning process
    data = """<OPEN>,<HIGH>,<LOW>,<CLOSE>,<TIMESTAMP>
    100.0,105.0,95.0,100.0,1722470400000
    101.0,106.0,96.0,102.0,1722474000000
    102.0,107.0,97.0,101.0,1722477600000
    103.0,108.0,98.0,105.0,1722481200000
    """
    file_path.write_text(data)
    return str(file_path)

def test_file_not_found():
    #Checking that throws FileNotFoundError if the file doesn't exist
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_and_clean_data("non_existent_file.csv")

def test_load_and_clean_data_success(sample_csv_path):
    #Verify loaded success and cleaned columns and also the convertion from timestamp to date format.
    df = load_and_clean_data(sample_csv_path)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    #checking if the columns were cleaned
    assert list(df.columns) == ['open', 'high', 'low', 'close', 'date']
    #checking date parsing to datetime
    assert pd.api.types.is_datetime64_any_dtype(df['date'])
    
def test_resample_data_success(sample_csv_path):
    #verify if the resampled is correct and the candles it represents what actually is happenig
    df_clean = load_and_clean_data(sample_csv_path)
    df_resampled = resample_data(df_clean, timeframe="2h")

    assert isinstance(df_resampled, pd.DataFrame)
    assert list(df_resampled.columns) == ['open', 'high', 'low', 'close']
    #In fact when is indexed by date, the first element should be datetime
    assert isinstance(df_resampled.index, pd.DatetimeIndex)

def test_resample_missing_columns(tmp_path):
    #verify that resample_date throws a ValueError if indeed there is any essential column missig "OHLC"
    d = tmp_path / "bad.csv"
    d.write_text("open,close\n100,102\n")
    df_bad = pd.read_csv(d)

    with pytest.raises(ValueError, match="Error loading data Open, High, Low, Close"):
        resample_data(df_bad)
    
