import pandas as pd
from utils.google_sheets import get_google_sheets_data
from utils.pgn_analyzer import extract_opening_info

def main():
    df = get_google_sheets_data()
    if df is None:
        print("Could not get data from Google Sheets")
        return
    
    print("Games with Queen's Pawn Game:")
    for i, row in df.iterrows():
        pgn = row.get('PGN', '')
        info = extract_opening_info(pgn)
        if "Queen's Pawn Game" in str(info.get('opening_main', '')):
            print(f"Game {i}: Opening='{info['opening_main']}', Full='{info['opening_full']}'")
            print(f"  Row info: Date={row.get('Date', 'NA')}, Result={row.get('Result', 'NA')}, Side={row.get('Side', 'NA')}")
            
if __name__ == "__main__":
    main()