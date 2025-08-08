# Chess Analytics Dashboard

A comprehensive Streamlit-based chess analytics platform that transforms chess performance data into actionable insights and personalized improvement strategies.

## Features

- **Interactive Dashboard**: Real-time chess performance visualization
- **Opening Analysis**: Hierarchical opening tree with performance statistics
- **PGN Game Analysis**: Detailed game breakdowns with AI-powered insights
- **Machine Learning**: Performance prediction and trend analysis
- **Google Sheets Integration**: Automatic data synchronization
- **Mobile-Friendly**: Responsive design optimized for all devices

## Project Structure

```
├── app.py                 # Main Streamlit application
├── components/            # UI components
│   ├── charts.py         # Chart visualizations
│   ├── filters.py        # Data filtering components
│   ├── game_analyzer.py  # Game analysis interface
│   ├── opening_explorer.py # Opening performance explorer
│   └── opening_tree.py   # Interactive opening tree visualization
├── utils/                 # Utility modules
│   ├── data_processor.py # Data processing and filtering
│   ├── google_sheets.py  # Google Sheets API integration
│   ├── ml_analysis.py    # Machine learning analysis
│   └── pgn_analyzer.py   # PGN parsing and chess analysis
├── assets/               # Static assets
│   └── chess_style.css   # Custom CSS styling
├── dependencies.txt     # Python dependencies
└── README.md            # This file
```

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd chess-analytics-dashboard
```

2. Install dependencies:
```bash
pip install -r dependencies.txt
```

3. Set up your Google Sheets data source:
   - Create a Google Sheet with your chess game data
   - Make it publicly accessible
   - Update the SHEET_ID in `utils/google_sheets.py`

4. Run the application:
```bash
streamlit run app.py
```

## Data Format

Your Google Sheets should include the following columns:
- Date
- Side (W/B for White/Black)
- Result (WIN/LOSS/DRAW)
- Average Centipawn Loss (ACL)
- Accuracy %
- Opponent Name
- Opponent ELO
- PGN (complete game notation)

## Configuration

The application uses the following color scheme for performance visualization:
- **Deep Red** (≤20%): Poor performance
- **Pink** (20-35%): Below average
- **Yellow** (35-65%): Average performance
- **Light Green** (65-80%): Good performance
- **Dark Green** (80-95%): Excellent performance
- **Blue** (>95%): Outstanding performance

## Features in Detail

### Opening Analysis
- Interactive treemap and sunburst visualizations
- Performance statistics by opening and variation
- YouTube tutorial links for each opening
- Color-coded performance indicators

### Game Analysis
- PGN parsing and move analysis
- Mistake detection and classification
- Personalized insights and recommendations
- Phase-specific performance breakdown

### Machine Learning
- Performance trend prediction
- Opening recommendation system
- Skill progression analysis
- Comparative performance metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For questions or issues, please open a GitHub issue or contact the development team.