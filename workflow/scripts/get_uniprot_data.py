import argparse
import re
import requests
from requests.adapters import HTTPAdapter, Retry

url = "https://rest.uniprot.org/uniprotkb/search?fields=accession%2Cid%2Cprotein_name%2Cgene_names%2Creviewed&format=tsv&query=%28human%29%20AND%20%28reviewed%3Atrue%29&size=500"

re_next_link = re.compile(r'<(.+)>; rel="next"')
retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retries))

def get_next_link(headers):
    if "Link" in headers:
        match = re_next_link.match(headers["Link"])
        if match:
            return match.group(1)

def get_batch(batch_url):
    while batch_url:
        response = session.get(batch_url)
        response.raise_for_status()
        total = response.headers["x-total-results"]
        yield response, total
        batch_url = get_next_link(response.headers)


def get_parser():
    parser = argparse.ArgumentParser(prog="get_uniprot_data.py", description='Uniprot to tsv: download Uniprot tsv file')
    parser.add_argument('-o','--output', default="uniprot", help="Output file.")
    return parser


def main():

    parser = get_parser()
    args = parser.parse_args()
    progress = 0
    with open(args.output, 'w') as f:
        for batch, total in get_batch(url):
            lines = batch.text.splitlines()
            if not progress:
                print(lines[0], file=f)
            for line in lines[1:]:
                print(line, file=f)
            progress += len(lines[1:])
            print(f'{progress} / {total}')


if __name__ == '__main__':
    main()

