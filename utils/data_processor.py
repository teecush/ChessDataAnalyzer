import pandas as pd
import numpy as np

def process_chess_data(df):
    """Process the raw chess data for analysis"""
    if df is None:
        return None
    
    # Convert date column
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Convert rating to numeric
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    
    # Calculate game duration in moves
    df['Moves'] = df['Moves'].astype(int)
    
    # Calculate win/loss ratio
    df['Result'] = df['Result'].map({'1-0': 'Win', '0-1': 'Loss', '1/2-1/2': 'Draw'})
    
    return df

def calculate_statistics(df):
    """Calculate various chess statistics"""
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
    stats['win_rate'] = (stats['wins'] / stats['total_games']) * 100
    
    return stats

def get_opening_stats(df):
    """Calculate opening statistics"""
    opening_stats = df['Opening'].value_counts().head(10)
    return opening_stats
