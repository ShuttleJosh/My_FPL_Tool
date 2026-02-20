"""Debug script to test API calls"""
from api_client import FPLAPIClient

manager_id = 3546221

print("Testing FPL API...")
print(f"Manager ID: {manager_id}\n")

client = FPLAPIClient()

# Test 1: Get manager data
print("1. Fetching manager data...")
manager_data = client._get(f"/entry/{manager_id}/")
if manager_data:
    print(f"   ✓ Manager found: {manager_data.get('player_first_name')} {manager_data.get('player_last_name')}")
    print(f"   Current event: {manager_data.get('current_event')}")
else:
    print("   ✗ Failed to fetch manager data")

# Test 2: Get player IDs
print("\n2. Fetching team player IDs...")
player_ids = client.get_manager_team(manager_id)
if player_ids:
    print(f"   ✓ Found {len(player_ids)} players")
    print(f"   Player IDs: {player_ids[:5]}...")  # Show first 5
else:
    print("   ✗ Failed to fetch team")

# Test 3: Get all players and check IDs
print("\n3. Fetching all players from FPL...")
all_players = client.get_all_players()
print(f"   ✓ Fetched {len(all_players)} total players")

if player_ids and all_players:
    print("\n4. Matching team players...")
    matched = [p for p in all_players if p.id in player_ids]
    print(f"   ✓ Matched {len(matched)} players")
    if matched:
        print("\n   Your team:")
        for p in matched[:5]:
            print(f"      - {p.name} ({p.position}) - ID: {p.id}")
        if len(matched) > 5:
            print(f"      ... and {len(matched) - 5} more")

client.close()
