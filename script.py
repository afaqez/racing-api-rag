from app.services.racing_api_client import RacingAPIClient
import json

client = RacingAPIClient()

# horse_name = "Shining Smile"

# data = client.search_horses(horse_name)


race_id = "rac_11570455"
data = client.result(race_id)
print(json.dumps(data, indent=4))


# racecards = data["racecards"]

# print("Got the data")

# for racecard in racecards:
#     runners = racecard["runners"]
#     print(f"For race {racecard["race_id"]}, there are {len(runners)} runners")

# print("Total racecards: ", len(racecards))

# open("data.json", "w").write(json.dumps(data, indent=4))

