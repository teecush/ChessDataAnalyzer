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

        if len(df.columns) >= 12:
            # Keep first 12 columns
            df = df.iloc[:, :12]

            # Check if first row contains headers
            expected_headers = [
                'Performance Rating', 'New Rating', '#', 'Date',
                'Side', 'Result', 'sparkline data', 'Average Centipawn Loss (ACL)',
                'Accuracy %', 'Game Rating', 'Opponent Name', 'Opponent ELO'
            ]

            # Skip first row only if it matches headers, using string comparison
            if all(str(df.iloc[0][i]).strip().lower() == str(expected_headers[i]).strip().lower() 
                  for i in range(len(expected_headers))):
                df = df.iloc[1:]
                df = df.reset_index(drop=True)

            # Set column names
            df.columns = expected_headers

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