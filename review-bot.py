from review_bot import test_pull_request
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pr-url', required=True)
    parser.add_argument('--base-sha', required=True)
    parser.add_argument('--token', required=True, help='The GITHUB token for fetching package data')
    args = parser.parse_args()
    res = test_pull_request(args.pr_url, args.base_sha, args.token)
    if res['result'] == 'error':
        raise Exception(res['message'])


if __name__ == '__main__':
    main()
