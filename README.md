# FPL Transfer Analyzer

A smart transfer recommendation tool for Fantasy Premier League that analyzes expected points (xP), fixture difficulty, and transfer costs to identify profitable moves.

## Features

- **Quick Transfer Analysis**: Find smart replacements for any player
- **Expected Points Calculation**: Estimates points for upcoming games based on form and fixtures
- **Transfer Cost Awareness**: Only recommends transfers that exceed the 4-point penalty
- **Player Comparison**: Compare two players side-by-side
- **Configurable Analysis**: Adjust games ahead, minimum gains, and other parameters

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501`

## Project Structure

- `config.py` - Configuration parameters (API URLs, thresholds, etc.)
- `models.py` - Data classes for Player, Transfer, Fixture
- `api_client.py` - FPL API integration
- `transfer_analyzer.py` - Smart transfer logic and recommendations
- `streamlit_app.py` - Interactive web interface

## How It Works

### Transfer Recommendation Logic

A transfer is recommended as **GOOD** if:
```
Expected Points Gain - Transfer Cost (4) >= 5 points
```

For example:
- If a replacement player is expected to gain 10 points over the next 8 games
- And your current player is expected to gain 2 points
- Net gain = 10 - 2 - 4 = 4 points (NEUTRAL to BAD)

### Expected Points Calculation

Currently based on:
- Player's recent form
- Number of games ahead
- Injury/availability status

Future enhancements:
- Fixture Difficulty Rating (FDR) integration
- Team strength analysis
- Home/away considerations
- Position-specific scoring models

## TODO

- [ ] User authentication (FPL login)
- [ ] Auto-load user's current squad
- [ ] Weekly transfer planner
- [ ] Predictive models for form
- [ ] Price change predictions
- [ ] Bench vs starting decision analysis
- [ ] Captain/vice-captain recommendations
