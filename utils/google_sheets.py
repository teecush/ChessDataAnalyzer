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

        # Debug: Print raw response
        st.write("Raw response received")

        # Read CSV with specific row settings
        # Skip first row which is hidden, row 2 shows averages, row 3 has titles
        df = pd.read_csv(io.StringIO(response.text), skiprows=[0, 1], header=0)

        if df.empty:
            st.error('No data found in the Google Sheet')
            return None

        # Debug: Print raw data information
        st.write("Raw data shape:", df.shape)
        st.write("Raw columns:", df.columns.tolist())
        st.write("First few rows before processing:", df.head())

        # Select and rename columns as specified
        if len(df.columns) >= 12:
            # Keep first 12 columns
            df = df.iloc[:, :12]

            # Give meaningful names to columns exactly as provided
            column_names = [
                'Performance Rating', 'New Rating', '#', 'Date',  # First four columns (unchanged)
                'White', 'Black', 'Result', 'Event',  # User-specified columns 4-7
                'WhiteElo', 'BlackElo', 'TimeControl', 'Opening'  # User-specified columns 8-11
            ]
            df.columns = column_names

            # Debug: Print processed data
            st.write("Processed columns:", df.columns.tolist())
            st.write("First few rows of processed data:", df.head())

        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Google Sheets: {str(e)}")
        return None
    except pd.errors.EmptyDataError:
        st.error("The Google Sheet appears to be empty")
        return None
    except Exception as e:
        st.error(f"Error processing the chess data: {str(e)}")
        st.write("Error details:", str(e))  # Additional error details
        return None