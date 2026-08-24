import pytest
import pandas as pd
import numpy as np
from src.indicators import calculate_true_range, calculate_average_true_range, calculate_adx

@pytest.fixture
def sample_market_data():
    data ={

        'high':  [105.0, 107.0, 106.0, 110.0, 109.0, 112.0, 115.0, 114.0, 118.0, 120.0,
                  119.0, 122.0, 125.0, 124.0, 128.0, 130.0, 129.0, 132.0, 135.0, 134.0],

        'low':   [95.0,  98.0,  97.0,  101.0, 100.0, 103.0, 105.0, 104.0, 108.0, 110.0,
                  109.0, 112.0, 114.0, 113.0, 117.0, 119.0, 118.0, 121.0, 124.0, 123.0],

        'close': [100.0, 102.0, 101.0, 105.0, 104.0, 108.0, 110.0, 109.0, 115.0, 117.0,
                  114.0, 119.0, 121.0, 120.0, 125.0, 127.0, 124.0, 130.0, 132.0, 131.0]
    }
    return pd.DataFrame(data)

def test_calculate_true_range(sample_market_data):
    true_range = calculate_true_range(sample_market_data)

    assert isinstance(true_range, pd.Series)
    assert len(true_range) == len(sample_market_data)
    assert true_range.iloc[0] == 10.0

def test_calculate_average_true_range(sample_market_data):
    average_true_range = calculate_average_true_range(sample_market_data)

    assert isinstance(average_true_range, pd.Series)
    assert len(average_true_range) == len(sample_market_data)
    assert not np.isnan(average_true_range.iloc[-1])

def test_calculate_adx_success(sample_market_data):
    average_directional_index = calculate_adx(sample_market_data, period= 5)

    assert isinstance(average_directional_index, pd.Series)
    assert len(average_directional_index) == len(sample_market_data)
    assert not np.isnan(average_directional_index.iloc[-1])

def test_calculate_adx_missing_columns():
    df_malformed = pd.DataFrame({
        'high': [100, 105],
        'low': [90, 95]
        #there's not close
    })

    with pytest.raises(KeyError, match="Missing mandatory columns"):
        calculate_adx(df_malformed, period = 5)