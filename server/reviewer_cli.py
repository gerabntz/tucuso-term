"""Operator CLI (invite-only, M10): the ONLY way reviewers come to exist.

  python -m server.reviewer_cli invite  <handle> <db>
  python -m server.reviewer_cli link    <handle> <db>   # prints /mod/login/<token>
  python -m server.reviewer_cli disable <handle> <db>
"""
import argparse

from server.auth import invite_reviewer, issue_magic_link
from server.db import connect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["invite", "link", "disable"])
    p.add_argument("handle")
    p.add_argument("db")
    args = p.parse_args()
    conn = connect(args.db)
    if args.action == "invite":
        rid = invite_reviewer(conn, args.handle)
        print(f"reviewer #{rid} '{args.handle}' invited")
    elif args.action == "link":
        token = issue_magic_link(conn, args.handle)
        print(f"/mod/login/{token}   (single use, 15 min)")
    else:
        with conn:
            conn.execute("UPDATE reviewers SET active=0 WHERE handle=?", (args.handle,))
        print(f"'{args.handle}' disabled")
    conn.close()


if __name__ == "__main__":
    main()
