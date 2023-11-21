import os
from pathlib import Path

from bs4 import BeautifulSoup

BASE_URL = "https://www.codewars.com"

with open("output/output.html", "r", encoding="utf-8") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")

for element in soup.find_all("div", class_="item-title"):
    kata_link = element.find("a")["href"]
    kata_title = element.find("a").string

    directory = os.path.join("output", "repo", kata_title)
    Path(directory).mkdir(parents=True, exist_ok=True)

    with open(os.path.join(directory, "README.md"), "w", encoding="utf-8") as file:
        file.write(f"# [{kata_title}]({BASE_URL}{kata_link})\n")

    print(f"{kata_link} {kata_title}")
