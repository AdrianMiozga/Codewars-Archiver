import os
from pathlib import Path

from bs4 import BeautifulSoup

BASE_URL = "https://www.codewars.com"

with open("output/output.html", "r", encoding="utf-8") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")

for solution in soup.find_all("div", class_="list-item-solutions"):
    url = solution.find("div", class_="item-title").a.get("href")
    title = solution.find("div", class_="item-title").a.string
    timestamp = solution.find("time-ago").get("datetime")
    language = solution.find("code").get("data-language")
    code = solution.find("code").string

    directory = os.path.join("output", "repo", title)
    Path(directory).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(directory, "README.md"), "w", encoding="utf-8") as file:
        file.write(f"# [{title}]({BASE_URL}{url})\n")

    with open(
        os.path.join(directory, f"Solution.{language}"), "w", encoding="utf-8"
    ) as file:
        file.write(f"{code}\n")
