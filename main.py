import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def main():
    config_file = "config.json"
    output_directory = os.path.join("output", "repo")
    base_url = "https://www.codewars.com"

    if not os.path.exists(config_file):
        print(f"[Error] {config_file} not found!")
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as file:
        config = json.load(file)

    if config.get("username") is None:
        print(f"[Error] Key 'username' not found in {config_file}")
        sys.exit(1)

    if config.get("_session_id") is None:
        print(f"[Error] Key '_session_id' not found in {config_file}")
        sys.exit(1)

    if os.path.exists(output_directory):
        print(f"[Error] Output directory '{output_directory}' already exists")
        sys.exit(1)

    cookies = {
        "_session_id": config["_session_id"],
    }

    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    page = 0
    kata_downloaded = 0

    while True:
        if page == 0:
            params = {}
        else:
            params = {
                "page": page,
            }

        response = requests.get(
            f"https://www.codewars.com/users/{config['username']}/completed_solutions",
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=10,
        )

        soup = BeautifulSoup(response.text, "html.parser")

        if soup.find_all("div", class_="list-item-solutions"):
            print("Page:", page)
        else:
            print("Last page reached")
            break

        for solution in soup.find_all("div", class_="list-item-solutions"):
            url = solution.find("div", class_="item-title").a.get("href")
            title = solution.find("div", class_="item-title").a.string.strip()
            # timestamp = solution.find("time-ago").get("datetime")
            language = solution.find("code").get("data-language")
            code = solution.find("code").string

            clean_filename = re.sub(r"[^-\w ]", "", title)

            path = os.path.join(output_directory, clean_filename)

            Path(path).mkdir(parents=True)

            with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as file:
                file.write(f"# [{title}]({base_url}{url})\n")

            with open(
                os.path.join(path, f"Solution.{language}"), "w", encoding="utf-8"
            ) as file:
                file.write(f"{code}\n")

            kata_downloaded += 1

        page += 1

    print("Kata downloaded:", kata_downloaded)


if __name__ == "__main__":
    main()
