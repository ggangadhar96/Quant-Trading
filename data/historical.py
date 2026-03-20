import pandas as pd
import logging

logger = logging.getLogger(__name__)

class CSVLoader:
    """
    Loads OHLC standard CSV data for backtesting.
    """
    def __init__(self, csv_path):
        self.csv_path = csv_path
        
    def get_data(self) -> pd.DataFrame:
        logger.info(f"Loading historical data from {self.csv_path}...")
        df = pd.read_csv(self.csv_path)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.set_index('Timestamp', inplace=True)
        return df
