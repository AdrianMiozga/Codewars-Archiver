import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def main():
    config_file = "config.json"
    output_directory = os.path.join("output")
    readme_file = "README.md"
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
        "_session_id": config.get("_session_id"),
    }

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                  AppleWebKit/537.36 (KHTML, like Gecko) \
                  Chrome/119.0.0.0 Safari/537.36"

    headers = {
        "user-agent": re.sub(r"\s+", " ", user_agent),
    }

    Path(output_directory).mkdir()

    subprocess.run(
        [
            "git",
            "-C",
            output_directory,
            "init",
        ],
        check=True,
    )

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
            print(f"[Error] Status code: {response.status_code}")
            sys.exit(1)

        soup = BeautifulSoup(response.text, "html.parser")

        if soup.find_all("div", class_="list-item-solutions"):
            print(f"Page: {page}")
        else:
            break

        for kata in soup.find_all("div", class_="list-item-solutions"):
            url = kata.find("div", class_="item-title").a.get("href")
            title = kata.find("div", class_="item-title").a.string.strip()
            solution_count = len(kata.find_all("code"))

            # Make sure the title is a valid directory name
            clean_title = re.sub(r"[^-\w ]", "", title)

            clean_title = re.sub(r"\s+", " ", clean_title)

            kata_path = os.path.join(output_directory, clean_title)
            Path(kata_path).mkdir()

            readme_path = os.path.join(kata_path, readme_file)

            with open(readme_path, "w", encoding="utf-8") as file:
                file.write(f"# [{title}]({base_url}{url})\n")

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

                subprocess.run(
                    [
                        "git",
                        "-C",
                        output_directory,
                        "add",
                        os.path.join(clean_title, filename),
                    ],
                    check=True,
                )

                subprocess.run(
                    [
                        "git",
                        "-C",
                        output_directory,
                        "commit",
                        "--date",
                        timestamp,
                        "--message",
                        f"Add {filename}\n\nKata name: {title}",
                    ],
                    check=True,
                )

                commits_created += 1
                solutions_downloaded += 1

            kata_downloaded += 1

        page += 1

    subprocess.run(
        [
            "git",
            "-C",
            output_directory,
            "add",
            f"*{readme_file}",
        ],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "-C",
            output_directory,
            "commit",
            "--message",
            f"Add {readme_file} files",
        ],
        check=True,
    )

    commits_created += 1

    print(
        f"Downloaded {kata_downloaded} Kata "
        f"with {solutions_downloaded} solutions in total "
        f"and created {commits_created} commits"
    )


if __name__ == "__main__":
    main()
