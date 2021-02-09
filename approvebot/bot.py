import argparse
import json
import logging
import os
import praw
import time
from praw.exceptions import RedditAPIException
from praw.models import Message


def checkpoint_user(user, subreddit, filename):
    checkpoint = {}
    if os.path.isfile(filename):
        checkpoint = json.load(open(filename))
    if subreddit not in checkpoint:
        checkpoint[subreddit] = []
    # Normally this is done with sets, but stick to lists because it needs to be serialized to JSON anyway
    if user not in checkpoint[subreddit]:
        checkpoint[subreddit].append(user)
    with open(filename, "w") as fh:
        json.dump(checkpoint, fh)


def user_in_checkpoint(user, subreddit, filename):
    if not os.path.isfile(filename):
        return False
    checkpoint = json.load(open(filename))
    return user in checkpoint.get(subreddit, [])


def check_pms(r, subreddit, checkpoint, cooldown=90 * 60):
    logger = logging.getLogger("pmapprovebot.pms")
    subcon = r.subreddit(subreddit).contributor

    for item in r.inbox.unread(limit=None):
        retry = False
        if not isinstance(item, Message) or not item.author:
            r.inbox.mark_read([item])
            continue
        try:
            user = item.author.name
            logger.info(f"Got message from {user}")
            if user_in_checkpoint(user, subreddit, checkpoint):
                logger.info(f"Skipping {user}, already in checkpoint file")
                continue
            if list(r.subreddit(subreddit).contributor(user)):
                logger.info(f"Skipping {user}, already approved")
            else:
                subcon.add(user)
                logger.info(f"Approved {user}")
            checkpoint_user(user, subreddit, checkpoint)
            r.inbox.mark_read([item])
        except RedditAPIException as rae:
            if rae.items[0].error_type in {"USER_DOESNT_EXIST", "BANNED_FROM_SUBREDDIT"}:
                # These should just be considered added so there isn't another attempt
                checkpoint_user(user, subreddit, checkpoint)
            elif rae.items[0].error_type == "SUBREDDIT_RATELIMIT":
                logger.error("Rate limit reached, sleeping {cooldown / 60:.2f} mins...")
                retry = True
                time.sleep(cooldown)
            else:
                logger.error(f"Error approving {user}: {rae}")
        except Exception as e:
            logger.error(f'Error processing item "{item}": {e}')
        finally:
            if not retry:
                r.inbox.mark_read([item])


def main():
    parser = argparse.ArgumentParser(description="Approves users when they message the bot")
    parser.add_argument("subreddit", help="Subreddit to approve them for")
    parser.add_argument("-c", "--checkpoint", help="Checkpoint file", default="./checkpoint")
    parser.add_argument("-d", "--delay", help="Seconds between each inbox check", default=15, type=int)
    parser.add_argument("-u", "--user", help="User section in praw.ini", default="default")
    args = parser.parse_args()

    root_logger = logging.getLogger("pmapprovebot")
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s:%(asctime)s.%(msecs)03d:%(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)
    logger = logging.getLogger("pmapprovebot.main")

    r = praw.Reddit(args.user, user_agent="python:pmapprovebot:1.0.0")
    logger.info(f"Logged into reddit as {r.user.me()}")

    while True:
        try:
            check_pms(r, args.subreddit, args.checkpoint)
            time.sleep(args.delay)
        except KeyboardInterrupt:
            logger.info("Stopping")
            break


if __name__ == "__main__":
    main()
