import json
import os
import sys

# Ensure resources/lib is in path
base_dir = os.path.dirname(__file__)
repo_dir = os.path.abspath(os.path.join(base_dir, ".."))
sys.path.append(os.path.join(repo_dir, "resources", "lib"))

from douban_agent import get_agent

def save_example_to_json(file_name, movie_data, tv_data):
    data = {
        "description": "Example",
        "movie": movie_data,
        "tv": tv_data
    }
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved example data to {file_name}")

def main():
    output_dir = os.path.join(repo_dir, "tests", "fixtures")
    os.makedirs(output_dir, exist_ok=True)

    # New Agent (DoubanMovieSearch)
    new_agent = get_agent(use_legacy=False)
    print("Fetching data for New Agent...")
    res_movie = new_agent.search("黑客帝国")
    res_tv = new_agent.search("绝命毒师")
    
    if res_movie and res_tv:
        target = os.path.join(output_dir, "douban_api_example.json")
        save_example_to_json(target, res_movie[0]['origin'], res_tv[0]['origin'])

    # Legacy Agent (DoubanSearch)
    legacy_agent = get_agent(use_legacy=True)
    print("Fetching data for Legacy Agent...")
    res_movie_leg = legacy_agent.search("黑客帝国")
    res_tv_leg = legacy_agent.search("绝命毒师")
    
    if res_movie_leg and res_tv_leg:
        target = os.path.join(output_dir, "douban_scraper_example.json")
        save_example_to_json(target, res_movie_leg[0]['origin'], res_tv_leg[0]['origin'])

if __name__ == "__main__":
    main()
