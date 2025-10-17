import os
import fnmatch
import json
import argparse


parser = argparse.ArgumentParser(description="run the neighborhood in standalone mode")
parser.add_argument("folder", type=str, default="houses", help="folder to search for house files",required=False)
parser.add_argument("--pattern", type=str, default="*_house.py", help="pattern to match house files")
parser.add_argument("--profile", type=str, default="profile1", help="type of load profile to use: flat, spike, dspike, random, profile1, profile_solar")

args = parser.parse_args()
    
houses_dir = args.folder
pattern = args.pattern

# Scan the directory for matching files
house_files = [f for f in os.listdir(houses_dir) if fnmatch.fnmatch(f, pattern)]

# Create a JSON object
runner = {"name": "house_evaluation","broker":"false"}
runner["federates"]=[]

for house_file in house_files:
    federate={"directory":houses_dir,
              "host":"localhost",
              "name":house_file[:-9],
              "exec":f"python -u {house_file}"
              }
    runner["federates"].append(federate)



script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
# Print or use the JSON object

federate = {
    "directory": script_directory,
    "host": "localhost", 
    "name": "market_maker",
    "exec": f"python -u market_maker.py --autobroker --auto --profile {args.profile}"}

runner["federates"].append(federate)

with open("houses.json", "w") as f:
    json.dump(runner, f, indent=3)
    

