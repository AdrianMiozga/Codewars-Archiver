import os
from pathlib import Path

from bs4 import BeautifulSoup

with open("output/output.html", "r", encoding="utf-8") as file:
    html = file.read()

soup = BeautifulSoup(html, "html.parser")

index = 0

for element in soup.find_all("code", class_="mb-5px"):
    language = element["data-language"]
    code = element.string

    directory = os.path.join("output", "repo")
    Path(directory).mkdir(parents=True, exist_ok=True)

    with open(
        os.path.join(directory, f"{index}.{language}"), "w", encoding="utf-8"
    ) as file:
        file.write(f"{code}\n")

    index += 1
