import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

NAME = "Codewars Archiver"
VERSION = "0.1.0"
BASE_URL = "https://www.codewars.com"
CONFIG_FILE = "config.json"
LANGUAGES_FILE = "languages.json"
OUTPUT_DIRECTORY = "output"
README_FILE = "README.md"
REQUESTS_TIMEOUT = 10


class Solution:
    def __init__(self, timestamp: str, language: str, code: str) -> None:
        self.timestamp = timestamp
        self.language = language
        self.code = code

    def __eq__(self, other):
        if isinstance(other, Solution):
            return self.code == other.code

        return False


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
        logging.error("Key ‘username’ not found in %s", CONFIG_FILE)
        sys.exit(1)

    if config.get("_session_id") is None:
        logging.error("Key ‘_session_id’ not found in %s", CONFIG_FILE)
        sys.exit(1)

    return config


def get_languages() -> dict[str, str]:
    if not Path(CONFIG_FILE).is_file():
        logging.error("%s not found!", CONFIG_FILE)
        sys.exit(1)

    with open(LANGUAGES_FILE, "r", encoding="utf-8") as file:
        languages = json.load(file)

    return languages


def main(cmd_args) -> None:
    git = Git(cmd_args.no_git)
    config = get_configuration()
    languages = get_languages()

    if Path(OUTPUT_DIRECTORY).is_dir():
        logging.error("Output directory ‘%s’ already exists", OUTPUT_DIRECTORY)
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
        katas = soup.find_all("div", class_="list-item-solutions")

        if katas:
            logging.info("Page: %s", current_page)
        else:
            # Scraped page doesn't contain any Kata

            if current_page == 0:
                logging.error(
                    "Session cookie is invalid or the user ‘%s’ has no completed Kata",
                    config.get("username"),
                )

                sys.exit(1)
            else:
                break

        for kata in katas:
            url = kata.find("div", class_="item-title").a.get("href")
            title = kata.find("div", class_="item-title").a.string.strip()
            code_list = kata.find_all("code")
            timestamps = kata.find_all("time-ago")

            unique_solutions = []

            for index, code in enumerate(code_list):
                solution = Solution(
                    timestamps[index].get("datetime"),
                    code.get("data-language"),
                    code.string,
                )

                if solution not in unique_solutions:
                    unique_solutions.append(solution)

            # Make sure the title is a valid directory name
            clean_title = re.sub(r"[^-\w ]", "", title)

            clean_title = re.sub(r"\s+", " ", clean_title)

            kata_path = Path(OUTPUT_DIRECTORY, clean_title)
            Path(kata_path).mkdir()

            readme_path = Path(kata_path, README_FILE)

            with open(readme_path, "w", encoding="utf-8") as file:
                file.write(f"# [{title}]({BASE_URL}{url})\n")

            for index, solution in enumerate(unique_solutions):
                extension = languages.get(solution.language)

                if extension is None:
                    extension = solution.language

                    logging.warning(
                        "Unknown language: %s. Using ‘.%s’ as file extension",
                        solution.language,
                        solution.language,
                    )

                filename = "Solution"

                if len(unique_solutions) > 1:
                    filename += f" {index + 1}"

                filename += f".{extension}"

                with open(Path(kata_path, filename), "w", encoding="utf-8") as file:
                    file.write(solution.code)

                git.run_command("add", Path(clean_title, filename))

                git.run_command(
                    "commit",
                    "--date",
                    solution.timestamp,
                    "--message",
                    f"Add {filename}\n\nKata name: {title}",
                )

                solutions_downloaded += 1

            if len(unique_solutions) != len(code_list):
                message = f"Skipped {len(code_list) - len(unique_solutions)} duplicate solution"

                if len(code_list) - len(unique_solutions) != 1:
                    message += "s"

                message += f" for ‘{title}’"

                logging.info(message)

            kata_downloaded += 1

        current_page += 1

    git.run_command("add", f"*{README_FILE}")

    git.run_command(
        "commit",
        "--message",
        f"Add {README_FILE} files",
    )

    message = (
        f"Downloaded {kata_downloaded} Kata"
        f" with {solutions_downloaded} solutions in total"
    )

    if not git.no_git:
        commits_created = git.check_output("rev-list", "--count", "HEAD")
        message += f" and created {commits_created} commits"

    logging.info(message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(prog=NAME, add_help=False)

    options = parser.add_argument_group("Options")

    options.add_argument(
        "-h",
        "--help",
        action="help",
        help="Print this help message and exit",
    )

    options.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION,
        help="Print program version and exit",
    )

    options.add_argument(
        "--no-git",
        action="store_true",
        help="Don’t create a git repository",
    )

    main(parser.parse_args())
