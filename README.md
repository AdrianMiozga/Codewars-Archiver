# Codewars Archiver

> [!WARNING]
> This software uses HTML parsing and it might break in the future.

Codewars Archiver is a command-line program that downloads solutions from the [Codewars](https://www.codewars.com/) website for a specific user. It works by parsing the HTML of the website by using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).

Besides downloading source code it also creates a Git repository and creates a commit for each solution file. Every commit has changed `AuthorDate` to a submit date from the Codewars website. This preserves when the code was actually written. `README.md` files created for each Kata are commited all at once without changing the date. Creation of a repository can be disabled with the `--no-git` option.

![Preview](assets/recording.gif)

It creates the following file structure. Repository created by this program can be found at [AdrianMiozga/Codewars](https://github.com/AdrianMiozga/Codewars).

```
└───output
    ├───5 kyu
    │   └───Kata name #1
    │           README.md
    │           Solution 1.java
    │           Solution 2.java
    │
    ├───6 kyu
    │   ├───Kata name #1
    │   │       README.md
    │   │       Solution.py
    │   │
    │   └───Kata name #2
    │           README.md
    │           Solution.kt
    │
    └───...
```

`README.md` files contain Kata title and link.

Kata can have multiple solutions that have identical code. This program skips duplicates and downloads only the oldest solution.

It has been tested on Windows and Linux.

## Dependencies

- [Python](https://www.python.org/) 3.9+
  - [requests](https://requests.readthedocs.io/en/latest/)
  - [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- (Optional) [Git](https://git-scm.com/) 2.9+

## Usage

```
Usage: codewars-archiver.py [-h] [-v] [--no-git]

Options:
  -h, --help     Print this help message and exit
  -v, --version  Print program version and exit
  --no-git       Don’t create a git repository
```

Create a `config.json` file in the same directory as `codewars_archiver.py` from the following template. Replace values of `username` and `_session_id` with your Codewars username and `_session_id` cookie.

```json
{
  "username": "<Codewars username>",
  "_session_id": "<_session_id cookie from Codewars>"
}
```

## Configuration

### languages.json

The `languages.json` file is used to map names of programming languages to file extensions. If the language that you are trying to download isn’t there the output file will have full language name as an extension e.g. `Solution.kotlin`.

It has the following format:

```json
{
  "language": "file_extension"
}
```

Where language is the value of the `data-language` attribute from HTML.
