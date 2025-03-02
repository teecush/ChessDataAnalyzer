import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None

    # Debug: Print column names
    #st.write("Available columns:", df.columns.tolist()) # Commented out as st is not defined in this context

    # Convert date column (assuming it might be named differently)
    date_column = next((col for col in df.columns if 'date' in col.lower()), None)
    if date_column:
        df[date_column] = pd.to_datetime(df[date_column])
        # Rename to standardized column name
        df = df.rename(columns={date_column: 'Date'})
    else:
        #st.error("Date column not found in the data") # Commented out as st is not defined in this context
        return None

    # Convert rating to numeric (handle potential column name variations)
    rating_column = next((col for col in df.columns if 'rating' in col.lower() or 'elo' in col.lower()), None)
    if rating_column:
        df[rating_column] = pd.to_numeric(df[rating_column], errors='coerce')
        df = df.rename(columns={rating_column: 'Rating'})

    # Calculate game duration in moves
    moves_column = next((col for col in df.columns if 'move' in col.lower()), None)
    if moves_column:
        df[moves_column] = pd.to_numeric(df[moves_column], errors='coerce')
        df = df.rename(columns={moves_column: 'Moves'})

    # Map result values (handle potential variations)
    result_column = next((col for col in df.columns if 'result' in col.lower()), None)
    if result_column:
        df[result_column] = df[result_column].map({
            '1-0': 'Win', 
            '0-1': 'Loss', 
            '1/2-1/2': 'Draw',
            'win': 'Win',
            'loss': 'Loss',
            'draw': 'Draw'
        })
        df = df.rename(columns={result_column: 'Result'})

    # Keep only processed columns
    required_columns = ['Date', 'Rating', 'Moves', 'Result']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        #st.error(f"Missing required columns: {', '.join(missing_columns)}") # Commented out as st is not defined in this context
        return None

    return df

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
    opening_column = next((col for col in df.columns if 'opening' in col.lower()), None)
    if opening_column:
        opening_stats = df[opening_column].value_counts().head(10)
        return opening_stats
    return pd.Series()