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

        # Determine player's rating based on color
        df['Rating'] = df.apply(lambda row: row['WhiteElo'] if row['White'] == 'Me' else row['BlackElo'], axis=1)
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')

        # Convert game number to numeric
        df['#'] = pd.to_numeric(df['#'], errors='coerce')

        # Map chess results to standard format
        df['Result'] = df['Result'].map({
            '1-0': 'Win' if df['White'].eq('Me').any() else 'Loss',
            '0-1': 'Loss' if df['White'].eq('Me').any() else 'Win',
            '1/2-1/2': 'Draw'
        })

        # Keep only the columns we need for visualization
        processed_df = df[['Date', 'Rating', '#', 'Result', 'Opening', 'Performance Rating', 'New Rating']].copy()

        return processed_df

    except Exception as e:
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