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

        # Process WhiteElo and BlackElo
        df['WhiteElo'] = pd.to_numeric(df['WhiteElo'], errors='coerce')
        df['BlackElo'] = pd.to_numeric(df['BlackElo'], errors='coerce')

        # Create Result mapping
        result_mapping = {
            '1-0': lambda row: 'Win' if row['White'] == 'Me' else 'Loss',
            '0-1': lambda row: 'Loss' if row['White'] == 'Me' else 'Win',
            '1/2-1/2': lambda row: 'Draw'
        }

        # Map results based on player color
        df['Result'] = df.apply(
            lambda row: result_mapping.get(row['Result'], lambda x: 'Unknown')(row),
            axis=1
        )

        # Determine player's rating based on color
        df['Rating'] = df.apply(
            lambda row: row['WhiteElo'] if row['White'] == 'Me' else row['BlackElo'],
            axis=1
        )

        # Keep only the columns we need for visualization
        processed_df = df[['Date', 'Rating', '#', 'Result', 'Opening', 'Performance Rating', 'New Rating']].copy()

        # Debug information
        print("Processed data shape:", processed_df.shape)
        print("Sample of processed data:", processed_df.head())
        print("Unique results:", processed_df['Result'].unique())
        print("Rating range:", processed_df['Rating'].min(), "-", processed_df['Rating'].max())

        return processed_df

    except Exception as e:
        print(f"Error in process_chess_data: {str(e)}")
        return None

def calculate_statistics(df):
    """Calculate various chess statistics"""
    if df is None:
        return {
            'total_games': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_rating': 0,
            'max_rating': 0,
            'min_rating': 0,
            'win_rate': 0,
            'tournament_performance': 0
        }

    stats = {
        'total_games': len(df),
        'wins': len(df[df['Result'] == 'Win']),
        'losses': len(df[df['Result'] == 'Loss']),
        'draws': len(df[df['Result'] == 'Draw']),
        'avg_rating': df['Rating'].mean(),
        'max_rating': df['Rating'].max(),
        'min_rating': df['Rating'].min(),
        'tournament_performance': df['Performance Rating'].mean()  # Average tournament performance
    }

    # Calculate win rate
    stats['win_rate'] = (stats['wins'] / stats['total_games']) * 100 if stats['total_games'] > 0 else 0

    return stats

def get_opening_stats(df):
    """Calculate opening statistics"""
    if 'Opening' in df.columns:
        opening_stats = df['Opening'].value_counts().head(10)
        return opening_stats
    return pd.Series()