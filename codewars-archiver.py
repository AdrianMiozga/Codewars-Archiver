import argparse
import json
import logging
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
REQUESTS_TIMEOUT = 10


class Git:
    def __init__(self, no_git: bool) -> None:
        self.no_git = no_git

    def run_command(self, *args) -> None:
        """Run a git command in the output directory."""

        if self.no_git:
            return

        subprocess.run(["git", "-C", OUTPUT_DIRECTORY] + list(args), check=True)

    def check_output(self, *args) -> str:
        """Run a git command in the output directory and return stripped output."""

        if self.no_git:
            return ""

        return subprocess.check_output(
            ["git", "-C", OUTPUT_DIRECTORY] + list(args), encoding="utf-8"
        ).strip()


def get_configuration() -> dict[str, str]:
    if not Path(CONFIG_FILE).is_file():
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


def main(cmd_args) -> None:
    git = Git(cmd_args.no_git)
    config = get_configuration()

    if Path(OUTPUT_DIRECTORY).is_dir():
        logging.error("Output directory '%s' already exists", OUTPUT_DIRECTORY)
        sys.exit(1)

    params = {}

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

    git.run_command("init")

    current_page = 0
    kata_downloaded = 0
    solutions_downloaded = 0

    while True:
        if current_page > 0:
            params["page"] = current_page
            headers["x-requested-with"] = "XMLHttpRequest"

        response = requests.get(
            f"{BASE_URL}/users/{config.get('username')}/completed_solutions",
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=REQUESTS_TIMEOUT,
        )

        if response.status_code != 200:
            logging.error("Status code: %s", response.status_code)
            sys.exit(1)

        soup = BeautifulSoup(response.text, "html.parser")

        if soup.find_all("div", class_="list-item-solutions"):
            logging.info("Page: %s", current_page)
        else:
            # Scraped page doesn't contain any Kata
            break

        for kata in soup.find_all("div", class_="list-item-solutions"):
            url = kata.find("div", class_="item-title").a.get("href")
            title = kata.find("div", class_="item-title").a.string.strip()
            solution_count = len(kata.find_all("code"))

            # Make sure the title is a valid directory name
            clean_title = re.sub(r"[^-\w ]", "", title)

            clean_title = re.sub(r"\s+", " ", clean_title)

            kata_path = Path(OUTPUT_DIRECTORY, clean_title)
            Path(kata_path).mkdir()

            readme_path = Path(kata_path, README_FILE)

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

                with open(Path(kata_path, filename), "w", encoding="utf-8") as file:
                    file.write(f"{code}\n")

                git.run_command("add", Path(clean_title, filename))

                git.run_command(
                    "commit",
                    "--date",
                    timestamp,
                    "--message",
                    f"Add {filename}\n\nKata name: {title}",
                )

                solutions_downloaded += 1

            kata_downloaded += 1

        current_page += 1

    git.run_command("add", f"*{README_FILE}")

    git.run_command(
        "commit",
        "--message",
        f"Add {README_FILE} files",
    )

    commits_created = git.check_output("rev-list", "--count", "HEAD")

    first_part = f"Downloaded {kata_downloaded} Kata"
    first_part += f" with {solutions_downloaded} solutions in total"

    second_part = ""

    if commits_created != "":
        second_part = f" and created {commits_created} commits"

    logging.info("%s%s", first_part, second_part)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        prog="Codewars Archiver",
    )

    parser.add_argument(
        "--no-git", action="store_true", help="Don't create a git repository"
    )

    main(parser.parse_args())
