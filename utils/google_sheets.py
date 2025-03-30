import pandas as pd
import requests
import streamlit as st
import io

def get_google_sheets_data():
    """
    Fetch data from Google Sheets using public access
    """
    try:
        # Google Sheets published to the web URL format
        SHEET_ID = "1Z1zFDzVF0_zxEuH3AwBNy8or2SYmpulRnKn2OYvSo5Q"
        # Use Query Language to get all data
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid=0"

        # Fetch the CSV data
        response = requests.get(URL)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Read CSV data with all columns as string type
        df = pd.read_csv(io.StringIO(response.text), dtype=str)

        # Debug information before processing
        st.sidebar.write("Raw data rows:", len(df))

        # Check if the dataframe contains columns we need
        if len(df.columns) >= 13:  # Now checking for 13 columns including PGN
            # Check if first row contains headers (partial check)
            expected_core_headers = [
                'Performance Rating', 'New Rating', '#', 'Date',
                'Side', 'Result', 'sparkline data', 'Average Centipawn Loss (ACL)',
                'Accuracy %', 'Game Rating', 'Opponent Name', 'Opponent ELO'
            ]
            
            # Add PGN to expected headers
            expected_headers = expected_core_headers.copy()
            expected_headers.append('PGN')  # Add PGN as the 13th column
            
            # Check if first row matches headers (focusing on the first 12)
            header_match = True
            for i in range(min(len(expected_core_headers), len(df.columns))):
                if i < len(df.columns) and i < len(expected_core_headers):
                    header_val = str(df.iloc[0][i]).strip().lower()
                    expected_val = str(expected_core_headers[i]).strip().lower()
                    if header_val != expected_val:
                        header_match = False
                        break
            
            # Skip first row only if it matches headers
            if header_match:
                df = df.iloc[1:]
                df = df.reset_index(drop=True)
            
            # Check if we have the PGN column (should be the 13th column)
            if len(df.columns) >= 13:
                actual_cols = list(df.columns)
                # Assign expected column names to the dataframe, keeping any extra columns
                new_cols = expected_headers.copy()
                # Add any extra columns with original names
                if len(actual_cols) > len(new_cols):
                    for i in range(len(new_cols), len(actual_cols)):
                        new_cols.append(actual_cols[i])
                df.columns = new_cols
            else:
                # If PGN column doesn't exist, use the first 12 columns and add a blank PGN column
                df = df.iloc[:, :12]
                df.columns = expected_core_headers
                df['PGN'] = ''  # Add empty PGN column

            # Debug information after processing
            st.sidebar.write("Processed data rows:", len(df))
            st.sidebar.write("Column types:", df.dtypes.to_dict())

            return df

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Google Sheets: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing the chess data: {str(e)}")
        st.write("Error details:", str(e))
        return None