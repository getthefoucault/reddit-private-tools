import argparse
import arrow
import os
import requests
import time


API = "https://api.pushshift.io"
TYPE = "comment"


def main():
    parser = argparse.ArgumentParser(description="Automatically approves users to a subreddit.")
    parser.add_argument("subreddit", help="Subreddit to scan through")
    parser.add_argument("-b", "--before", help="Date to start from")
    parser.add_argument("-c", "--cooldown", help="Cooldown seconds", type=int, default=15)
    parser.add_argument("-C", "--clean", help="Don't add to existing userlist", action="store_true")
    parser.add_argument("-o", "--output", help="Output file", default="./users.txt")
    parser.add_argument("-p", "--pagesize", help="Number of results per page", type=int, default=500)
    args = parser.parse_args()
    users = set()
    if not args.clean and os.path.isfile(args.output):
        users = {l.strip() for l in open(args.output) if l.strip()}
        print(f"Loaded {len(users)} existing users")
    ts = arrow.get(args.before).timestamp if args.before else None
    while True:
        try:
            with open(args.output, "w") as fh:
                for user in users:
                    fh.write(user + "\n")
            url = (
                f"{API}/reddit/{TYPE}/search?fields=author,created_utc&subreddit={args.subreddit}&size={args.pagesize}"
            )
            if ts:
                url += f"&before={ts}"
            response = requests.get(url)
            try:
                response.raise_for_status()
            except Exception as e:
                print(f"Got exception: {e}\nSleeping for {args.cooldown} seconds...")
                time.sleep(args.cooldown)
                continue
            data = response.json()["data"]
            if not data:
                break
            for item in data:
                users.add(item["author"])
            ts = data[-1]["created_utc"]
            print(f"Batch ended on {arrow.get(ts).format('YYYY-MM-DD HH:mm:ss')} with {len(users)} total users")
            time.sleep(2)
        except KeyboardInterrupt:
            print("Stopping...")
            print(f"Use -b to resume at {arrow.get(ts).format('YYYY-MM-DD HH:mm:ss')}")
            break


if __name__ == "__main__":
    main()
