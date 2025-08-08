# Chess Analytics Dashboard

## Overview

A comprehensive Streamlit-based chess analytics platform that transforms chess performance data into actionable insights. The application processes chess game data from Google Sheets, providing interactive visualizations for rating progression, opening analysis, game breakdowns, and performance predictions through machine learning models.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with responsive design
- **Component Structure**: Modular UI components organized by functionality:
  - Charts module for data visualizations using Plotly
  - Filters for data filtering and user controls
  - Game analyzer for individual PGN game analysis
  - Opening explorer for chess opening performance analysis
  - Opening tree for hierarchical opening visualization
- **Styling**: Custom CSS with chess-themed design and mobile-friendly responsive layout
- **Caching**: Streamlit's built-in caching for data with 10-minute TTL

### Backend Architecture
- **Data Processing Pipeline**: 
  - Raw data ingestion from Google Sheets
  - Data cleaning and type conversion
  - Statistical analysis and aggregation
  - Performance metrics calculation
- **Chess Analysis Engine**: 
  - PGN parsing using python-chess library
  - Opening classification and performance tracking
  - Game analysis with move-by-move breakdown
  - Player side detection and result tracking
- **Machine Learning Module**:
  - Feature extraction from game data (ACL, accuracy, ratings)
  - K-means clustering for performance analysis
  - Performance prediction and trend analysis
  - Standardized feature scaling for consistent analysis

### Data Storage Solutions
- **Primary Data Source**: Google Sheets integration via public CSV export
- **Data Structure**: Tabular format with columns for dates, ratings, results, PGN data, and performance metrics
- **Caching Strategy**: In-memory caching with automatic refresh every 10 minutes
- **Data Processing**: Real-time filtering and aggregation without persistent storage

### Authentication and Authorization
- **Access Model**: Public access via published Google Sheets (no authentication required)
- **Data Security**: Read-only access to publicly shared chess game data
- **User Sessions**: Streamlit's built-in session state management

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the dashboard interface
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive charting and visualization library
- **Scikit-learn**: Machine learning algorithms for performance analysis
- **Python-chess**: Chess game analysis and PGN parsing

### Data Integration
- **Google Sheets API**: Automated data synchronization via public CSV endpoints
- **Requests**: HTTP client for fetching Google Sheets data

### Additional Services
- **Chess Analysis**: 
  - Lichess Study integration for game studies
  - Chess.com Library for game collections
  - CFC (Chess Federation of Canada) ranking system integration
- **Web Scraping**: Trafilatura for content extraction (future enhancement)
- **Communication**: Twilio integration for potential notifications (future enhancement)

### Deployment Dependencies
- **Google Cloud Platform**: Potential hosting for Google API integration
- **Static Assets**: Custom CSS files for theming and responsive design