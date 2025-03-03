import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None

    try:
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])

        # Process tournament ratings (keeping NaN values for between-tournament periods)
        df['Performance Rating'] = pd.to_numeric(df['Performance Rating'], errors='coerce')
        df['New Rating'] = pd.to_numeric(df['New Rating'], errors='coerce')

        # Convert game number to numeric
        df['#'] = pd.to_numeric(df['#'], errors='coerce')

        # Process ELO ratings
        df['WhiteElo'] = pd.to_numeric(df['WhiteElo'], errors='coerce')
        df['BlackElo'] = pd.to_numeric(df['BlackElo'], errors='coerce')

        # Determine player's rating based on color
        df['Rating'] = df.apply(
            lambda row: row['WhiteElo'] if row['White'] == 'Me' else row['BlackElo'],
            axis=1
        )

        # Keep only the columns we need for visualization
        processed_df = df[['Date', '#', 'Performance Rating', 'New Rating', 
                          'White', 'Black', 'Result', 'Event',
                          'WhiteElo', 'BlackElo', 'TimeControl', 'Opening']].copy()

        # Debug information
        print("Processed data shape:", processed_df.shape)
        print("Sample of processed data:", processed_df.head())
        print("Rating range:", processed_df['Performance Rating'].min(), "-", processed_df['Performance Rating'].max())

        return processed_df

    except Exception as e:
        print(f"Error in process_chess_data: {str(e)}")
        return None

def calculate_statistics(df):
    """Calculate various chess statistics"""
    if df is None:
        return {
            'total_games': 0,
            'avg_rating': 0,
            'max_rating': 0,
            'min_rating': 0,
            'tournament_performance': 0
        }

    stats = {
        'total_games': len(df),
        'avg_rating': df['New Rating'].mean(),
        'max_rating': df['New Rating'].max(),
        'min_rating': df['New Rating'].min(),
        'tournament_performance': df['Performance Rating'].mean()  # Average tournament performance
    }

    return stats

def get_opening_stats(df):
    """Calculate opening statistics"""
    if 'Opening' in df.columns:
        return df['Opening'].value_counts().head(10)
    return pd.Series()