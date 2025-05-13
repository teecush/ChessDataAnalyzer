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
    
    print("=== Looking for Symmetrical Variation ===")
    for i, row in opening_df.iterrows():
        if "Symmetrical" in str(row.get('OpeningFull', '')):
            print(f"Found: {row['OpeningFull']}")
            print(f"Result: {row['Result']}")
            print(f"Side: {row['Side']}")
            print()
            
if __name__ == "__main__":
    main()