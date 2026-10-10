"""Rebuild the projects table in README.md from your latest GitHub repos."""
import html
import json
import os
import re
import sys
import urllib.request

USER = "abduIwahid"
LIMIT = 6                       # how many projects to show
PIN_TOPIC = "pin"               # optional: repos with this topic always show first
EXCLUDE = {USER, "certificates"}  # repo names to never show (add more here)
README = "README.md"
START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"

# Optional display-name overrides: repo name -> title shown on the profile
NAMES = {
    "Customer-Churn-Prediction": "Churnex",
    "fa24-bai": "Study Hubb",
}


def api(url):
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        return json.load(r)


def badge(text):
    safe = text.replace("-", "--").replace("_", "__").replace(" ", "_")
    return (
        f'<img src="https://img.shields.io/badge/{safe}-21262D?style=flat-square" '
        f'alt="{html.escape(text)}"/>'
    )


def row(repo):
    name = NAMES.get(repo["name"], repo["name"].replace("-", " ").replace("_", " "))
    desc = html.escape(repo.get("description") or "")
    chips = " ".join(badge(t) for t in repo.get("topics", []) if t != PIN_TOPIC)
    links = f'<a href="{repo["html_url"]}">Repository</a>'
    if repo.get("homepage"):
        links += f' · <a href="{html.escape(repo["homepage"])}">Live Demo</a>'
    body = desc + ("<br/><br/>" + chips if chips else "") + "<br/><br/>" + links
    lang = repo.get("language")
    sub = f"<br/><sub>{html.escape(lang)}</sub>" if lang else ""
    return (
        "  <tr>\n"
        f'    <td width="24%" valign="top"><a href="{repo["html_url"]}">'
        f"<b>{html.escape(name)}</b></a>{sub}</td>\n"
        f'    <td valign="top">{body}</td>\n'
        "  </tr>"
    )


def main():
    repos = api(
        f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"
    )
    candidates = [
        r
        for r in repos
        if not r["fork"] and not r["archived"] and r["name"] not in EXCLUDE
    ]
    # API order is latest push first; sorted() is stable, so repos tagged with
    # the pin topic come first and everything else stays in latest-push order.
    featured = sorted(candidates, key=lambda r: PIN_TOPIC not in r.get("topics", []))[:LIMIT]
    if not featured:
        sys.exit("No eligible repos found; leaving README untouched.")

    table = "<table>\n" + "\n".join(row(r) for r in featured) + "\n</table>"

    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        sys.exit("PROJECTS markers not found in README.md")

    new = pattern.sub(lambda _: f"{START}\n{table}\n{END}", text)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"README updated with {len(featured)} projects")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
