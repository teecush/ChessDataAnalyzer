import pandas as pd
from utils.google_sheets import get_google_sheets_data
from utils.pgn_analyzer import get_opening_performance

def main():
    df = get_google_sheets_data()
    if df is None:
        print("Could not get data from Google Sheets")
        return
    
    opening_results = get_opening_performance(df)
    opening_df = opening_results['opening_df']
    opening_stats_main = opening_results['opening_stats_main']
    
    print("=== Games with English Opening ===")
    english_games = opening_df[opening_df['OpeningMain'] == 'English Opening']
    print(english_games[['OpeningFull', 'Result', 'Side']])
    
    print("\n=== Stats for English Opening ===")
    english_stats = opening_stats_main[opening_stats_main['OpeningMain'] == 'English Opening']
    if not english_stats.empty:
        row = english_stats.iloc[0]
        print(f"Total games: {row['total']}")
        print(f"Wins: {row['wins']}")
        print(f"Draws: {row['draws']}")
        print(f"Losses: {row['losses']}")
        print(f"Win %: {row['win_pct']}")
        print(f"Score with draws as 0.5: {((row['wins'] + 0.5 * row['draws']) / row['total'] * 100):.1f}%")
    else:
        print("No stats found for English Opening")
            
if __name__ == "__main__":
    main()