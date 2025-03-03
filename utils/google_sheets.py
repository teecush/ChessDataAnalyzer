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
        URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

        # Fetch the CSV data
        response = requests.get(URL)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Convert to DataFrame using io.StringIO
        df = pd.read_csv(io.StringIO(response.text))

        if df.empty:
            st.error('No data found in the Google Sheet')
            return None

        # Select and rename columns as specified
        if len(df.columns) >= 12:
            # Select columns 0-5 and 7-11 (skipping column 6)
            df = pd.concat([df.iloc[:, :6], df.iloc[:, 7:12]], axis=1)

            # Give meaningful names to columns
            column_names = [
                'Performance Rating', 'New Rating', '#',  # First three columns
                'Date', 'White', 'Black',  # Columns 3-5
                'Result', 'WhiteElo', 'BlackElo', 'TimeControl',  # Columns 7-10
                'Opening'  # Column 11
            ]
            df.columns = column_names


        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Google Sheets: {str(e)}")
        return None
    except pd.errors.EmptyDataError:
        st.error("The Google Sheet appears to be empty")
        return None
    except Exception as e:
        st.error(f"Error processing the chess data: {str(e)}")
        return None