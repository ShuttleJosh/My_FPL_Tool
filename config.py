# Configuration settings for FPL Transfer Analyzer

# FPL API Base URL
FPL_API_BASE_URL = "https://fantasy.premierleague.com/api"

# Transfer analysis parameters
DEFAULT_GAMES_AHEAD = 8  # Number of games to look ahead for xP calculation
MIN_POINT_GAIN = 5  # Minimum point gain needed to justify a transfer (accounts for transfer cost)
TRANSFER_COST = 4  # Points deducted for a transfer

# Cache settings (in seconds)
CACHE_DURATION = 3600  # 1 hour

# API rate limiting
API_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
