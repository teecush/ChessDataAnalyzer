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

        # Debug: Print raw response content
        st.write("Raw CSV content first 500 chars:", response.text[:500])
        st.write("Total content length:", len(response.text))

        # Read CSV with minimal preprocessing
        df = pd.read_csv(io.StringIO(response.text), header=0)

        # Debug: Print raw data information
        st.write("Initial data shape:", df.shape)
        st.write("Raw columns:", df.columns.tolist())
        st.write("First few rows before processing:", df.head())

        # Select and rename columns as specified
        if len(df.columns) >= 12:
            # Keep first 12 columns
            df = df.iloc[:, :12]

            # Skip the first row (row 0) which contains duplicate titles
            df = df.iloc[1:]

            # Reset index after dropping the row
            df = df.reset_index(drop=True)

            # Give meaningful names to columns exactly as provided
            column_names = [
                'Performance Rating', 'New Rating', '#', 'Date',  # First four columns
                'Side', 'Result', 'sparkline data', 'Average Centipawn Loss (ACL)',  # User-specified columns 4-7
                'Accuracy %', 'Game Rating', 'Opponent Name', 'Opponent ELO'  # User-specified columns 8-11
            ]
            df.columns = column_names

            # Debug: Print processed data
            st.write("Processed data shape:", df.shape)
            st.write("Processed columns:", df.columns.tolist())
            st.write("First few rows of processed data:", df.head())
            st.write("Total number of rows after processing:", len(df))

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