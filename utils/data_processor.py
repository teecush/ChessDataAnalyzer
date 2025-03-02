import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None

    try:
        # Convert date column
        df['Date'] = pd.to_datetime(df['Date'])

        # Determine player's rating based on color
        df['Rating'] = df.apply(lambda row: row['WhiteElo'] if row['White'] == 'Me' else row['BlackElo'], axis=1)
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')

        # Convert moves to numeric
        df['Moves'] = df['Moves'].str.extract('(\d+)').astype(float)

        # Map chess results to standard format
        df['Result'] = df['Result'].map({
            '1-0': 'Win' if df['White'].eq('Me').any() else 'Loss',
            '0-1': 'Loss' if df['White'].eq('Me').any() else 'Win',
            '1/2-1/2': 'Draw'
        })

        # Keep only the columns we need for visualization
        processed_df = df[['Date', 'Rating', 'Moves', 'Result', 'Opening']].copy()

        # Debug information
        #st.write("Processed data sample:", processed_df.head()) # Commented out as st is not defined in this context
        #st.write("Processed columns:", processed_df.columns.tolist()) # Commented out as st is not defined in this context

        return processed_df

    except Exception as e:
        #st.error(f"Error in process_chess_data: {str(e)}") # Commented out as st is not defined in this context
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
            'avg_moves': 0,
            'win_rate': 0
        }

    stats = {
        'total_games': len(df),
        'wins': len(df[df['Result'] == 'Win']),
        'losses': len(df[df['Result'] == 'Loss']),
        'draws': len(df[df['Result'] == 'Draw']),
        'avg_rating': df['Rating'].mean(),
        'max_rating': df['Rating'].max(),
        'min_rating': df['Rating'].min(),
        'avg_moves': df['Moves'].mean()
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