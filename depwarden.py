import concurrent.futures
import json
import requests
import argparse
import urllib3
from prettytable import PrettyTable


def check_dependency(args):
    name, version = args
    if name.startswith("@"):
        org_name = name[1:].split("/")[0]
        url = f"https://www.npmjs.com/org/{org_name}"
    else:
        url = f"https://registry.npmjs.org/{name}"

    with requests.get(url, verify=False) as response:
        if response.status_code == 404:
            return (name, version, "X")
    return (name, version, "")


def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    parser = argparse.ArgumentParser(
        description="Search for vulnerable dependencies in a package.json file"
    )
    parser.add_argument("url", type=str, help="URL of the package.json file")
    args = parser.parse_args()

    with requests.Session() as session:
        try:
            with session.get(args.url, timeout=5, verify=False) as response:
                response.raise_for_status()
                data = json.loads(response.content)
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Error: {e}")
            return

        dependencies = data.get("dependencies", {})
        dependencies.update(data.get("devDependencies", {}))
        if dependencies:
            table = PrettyTable()
            table.field_names = ["Dependency", "Version", "Vulnerable"]
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                rows = executor.map(check_dependency, dependencies.items())
                for result in rows:
                    if result:
                        table.add_row(result)
            print(table)
        else:
            print("No dependencies found")


if __name__ == "__main__":
    main()
