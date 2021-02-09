# Subreddit Privitizing Toolkit

So you want to privitize your subreddit, ya little lib? Fine. Here are two tools
that make it easy to do so as smoothly as possible.

## Setup

It's recommended that you create a virtualenv and run these things from it.
Install dependencies with `pip install -r requirements.txt`. Set up your
`praw.ini` file with a `[default]` section per praw's instructions. Have a copy
of it in both the root and `approvebot` folders.

## Listing Current Users

The `list_users.py` module uses pushshift to scan through comments in your
subreddit and build up a list of users. It's probably faster to use pushshift's
agg feature but oh well. It will run as long as you need it to run. Press
CTRL-C to stop it.

It will (unless a different one is set with `-o`) write to `users.txt`. Unless
the `-C` argument is given, it will load the existing users in this file each
time and continue to just add new ones.

If you use the before argument (`-b`), you can start working back from before a
given date. Use this to resume running at a later date. Example:

```
$ python list_users.py redscarepod
Batch ended on 2021-02-09 03:49:20 with 71 total users
Batch ended on 2021-02-09 03:19:44 with 127 total users
Batch ended on 2021-02-09 02:56:19 with 173 total users
Batch ended on 2021-02-09 02:32:59 with 225 total users
^CStopping...
Use -b to resume at 2021-02-09 02:32:59

$ python list_users.py redscarepod -b '2021-02-09 02:32:59'
Loaded 173 existing users
Batch ended on 2021-02-09 02:03:39 with 228 total users
Batch ended on 2021-02-09 01:38:44 with 262 total users
Batch ended on 2021-02-09 01:11:32 with 291 total users
...
```

This can take a while. Pushshift isn't fast.

## Approving Users

You thought that took a long time? Welcome to the pain of approving them.
Reddit limits approvals to approximately one user *per minute*, and that
applies to the subreddit as a whole. Plan for this to take a few days minimum.
The `approve_users.py` module can do this with the user list you generated
earlier. It creates a checkpoint file (`checkpoint.csv` by default) that keeps
track of who has already been successfully approved. By delay it delays 70
seconds between each approval to avoid triggering a cooldown.

## Auto-approving Users

Once you finally go private, plenty of stragglers will want in. It's good to
have a grace period in which they can still get in by PMing a bot. The
`approvebot` folder contains the code to handle this. It keeps a checkpoint of
who it has approved and polls its inbox every 15 seconds for new messages,
approving anyone who messages it. It is distributed here with a .conf file that
will run it with `supervisord`. This is highly recommended, as reddit/praw is a
huge piece of shit and crashes constantly with 500 errors.
