import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.codewars.com"
CONFIG_FILE = "config.json"
OUTPUT_DIRECTORY = "output"
README_FILE = "README.md"


def run_git_command(directory: str, *args) -> None:
    subprocess.run(["git", "-C", directory] + list(args), check=True)


def get_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        logging.error("%s not found!", CONFIG_FILE)
        sys.exit(1)

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    if config.get("username") is None:
        logging.error("Key 'username' not found in %s", CONFIG_FILE)
        sys.exit(1)

    if config.get("_session_id") is None:
        logging.error("Key '_session_id' not found in %s", CONFIG_FILE)
        sys.exit(1)

    return config


def main():
    config = get_config()

    if os.path.exists(OUTPUT_DIRECTORY):
        logging.error("Output directory '%s' already exists", OUTPUT_DIRECTORY)
        sys.exit(1)

    cookies = {
        "_session_id": config.get("_session_id"),
    }

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                  AppleWebKit/537.36 (KHTML, like Gecko) \
                  Chrome/119.0.0.0 Safari/537.36"

    headers = {
        "user-agent": re.sub(r"\s+", " ", user_agent),
    }

    Path(OUTPUT_DIRECTORY).mkdir()

    run_git_command(OUTPUT_DIRECTORY, "init")

    page = 0
    kata_downloaded = 0
    solutions_downloaded = 0
    commits_created = 0

    while True:
        if page == 0:
            params = {}
        else:
            params = {
                "page": page,
            }

            headers["x-requested-with"] = "XMLHttpRequest"

        response = requests.get(
            f"https://www.codewars.com/users/{config.get('username')}/completed_solutions",
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=10,
        )

        if response.status_code != 200:
            logging.error("Status code: %s", response.status_code)
            sys.exit(1)

        soup = BeautifulSoup(response.text, "html.parser")

        if soup.find_all("div", class_="list-item-solutions"):
            logging.info("Page: %s", page)
        else:
            break

        for kata in soup.find_all("div", class_="list-item-solutions"):
            url = kata.find("div", class_="item-title").a.get("href")
            title = kata.find("div", class_="item-title").a.string.strip()
            solution_count = len(kata.find_all("code"))

            # Make sure the title is a valid directory name
            clean_title = re.sub(r"[^-\w ]", "", title)

            clean_title = re.sub(r"\s+", " ", clean_title)

            kata_path = os.path.join(OUTPUT_DIRECTORY, clean_title)
            Path(kata_path).mkdir()

            readme_path = os.path.join(kata_path, README_FILE)

            with open(readme_path, "w", encoding="utf-8") as file:
                file.write(f"# [{title}]({BASE_URL}{url})\n")

            for i in range(solution_count):
                timestamp = kata.find_all("time-ago")[i].get("datetime")
                language = kata.find_all("code")[i].get("data-language")
                code = kata.find_all("code")[i].string

                if solution_count > 1:
                    filename = f"Solution {i + 1}.{language}"
                else:
                    filename = f"Solution.{language}"

                with open(
                    os.path.join(kata_path, filename), "w", encoding="utf-8"
                ) as file:
                    file.write(f"{code}\n")

                run_git_command(
                    OUTPUT_DIRECTORY, "add", os.path.join(clean_title, filename)
                )

                run_git_command(
                    OUTPUT_DIRECTORY,
                    "commit",
                    "--date",
                    timestamp,
                    "--message",
                    f"Add {filename}\n\nKata name: {title}",
                )

                commits_created += 1
                solutions_downloaded += 1

            kata_downloaded += 1

        page += 1

    run_git_command(OUTPUT_DIRECTORY, "add", f"*{README_FILE}")

    run_git_command(
        OUTPUT_DIRECTORY,
        "commit",
        "--message",
        f"Add {README_FILE} files",
    )

    commits_created += 1

    logging.info(
        "Downloaded %s Kata with %s solutions in total and created %s commits",
        kata_downloaded,
        solutions_downloaded,
        commits_created,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    main()
