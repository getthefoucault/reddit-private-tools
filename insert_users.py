import sqlite3


def main():
    db = "../redditsource/output/acidmarxism.sqlite3"
    users = [l.strip() for l in open("./users.txt") if l.strip()]
    rows = [(user, "AcidMarxism") for user in users]

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.executemany("INSERT INTO users (username, subreddit) VALUES (?, ?) ON CONFLICT DO NOTHING", rows)
    conn.commit()


if __name__ == "__main__":
    main()
