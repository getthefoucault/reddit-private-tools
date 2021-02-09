import argparse
import gzip
import os
import praw
import time
from collections import defaultdict
from praw.exceptions import RedditAPIException
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(description="Automatically approves users to a subreddit.")
    parser.add_argument("userlist", help="List of users to approve")
    parser.add_argument("subreddit", help="Subreddit to approve them for")
    parser.add_argument("-c", "--checkpoint", help="Checkpoint file", default="./checkpoint.csv")
    parser.add_argument("-d", "--delay", help="Seconds between each approval", default=70, type=int)
    parser.add_argument("-u", "--user", help="User section in praw.ini", default="default")
    args = parser.parse_args()

    r = praw.Reddit(args.user, user_agent="python:autoapprove:1.0.0")
    subcon = r.subreddit(args.subreddit).contributor
    print(f"Logged into reddit as {r.user.me()}")

    if os.path.isfile(args.checkpoint):
        checkpoint = {line.strip() for line in open(args.checkpoint) if line.strip()}
    else:
        checkpoint = set()
    print(f"Loaded {len(checkpoint)} of users already approved.")

    rawusers = [line.strip() for line in open(args.userlist, "rt") if line.strip()]
    users = [u for u in set(rawusers) - set(checkpoint) if u != "[deleted]" and u != "AutoModerator"]
    print(f"{len(users)} new users to approve.")

    try:
        for user in tqdm(users):
            try:
                if user in checkpoint:
                    continue
                subcon.add(user)
                checkpoint.add(user)
                time.sleep(args.delay)
            except KeyboardInterrupt:
                print("Stopping...")
                break
            except RedditAPIException as rae:
                if rae.items[0].error_type in {"USER_DOESNT_EXIST", "BANNED_FROM_SUBREDDIT"}:
                    # These should just be considered added so there isn't another attempt
                    checkpoint.add(user)
                elif rae.items[0].error_type == "SUBREDDIT_RATELIMIT":
                    print("!!! Rate limit reached, sleeping 15 mins...")
                    time.sleep(15 * 60)
                else:
                    print(f'Error approving user "{user}": {rae}')
            except Exception as e:
                print(f'Error approving user "{user}": {e}')
    finally:
        with open(args.checkpoint, "w") as fh:
            for user in checkpoint:
                fh.write(user + "\n")
        print(f"Saved {len(checkpoint)} users to {args.checkpoint}")


if __name__ == "__main__":
    main()
