#!/usr/bin/env python3
"""A very small todo list tool."""
import argparse
import json
import os
import sys


def load(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save(path, tasks):
    with open(path, "w") as f:
        json.dump(tasks, f, indent=2)


def cmd_add(args, tasks):
    task = {"id": max([t["id"] for t in tasks], default=0) + 1, "text": args.text, "done": False}
    tasks.append(task)
    save(args.file, tasks)
    if args.json:
        print(json.dumps(task))
    else:
        print(f"added #{task['id']}: {task['text']}")


def cmd_list(args, tasks):
    if args.json:
        print(json.dumps(tasks))
        return
    if not tasks:
        print("no tasks")
        return
    for t in tasks:
        mark = "x" if t["done"] else " "
        print(f"[{mark}] #{t['id']} {t['text']}")


def cmd_done(args, tasks):
    for t in tasks:
        if t["id"] == args.id:
            t["done"] = True
            save(args.file, tasks)
            if args.json:
                print(json.dumps(t))
            else:
                print(f"completed #{t['id']}: {t['text']}")
            return
    print(f"no task #{args.id}", file=sys.stderr)
    sys.exit(1)


def cmd_stats(args, tasks):
    total = len(tasks)
    done = sum(1 for t in tasks if t["done"])
    open_ = total - done
    if args.json:
        print(json.dumps({"total": total, "done": done, "open": open_}))
    else:
        print(f"{total} tasks, {done} done, {open_} open")


def main(argv=None):
    p = argparse.ArgumentParser(prog="todo")
    p.add_argument("--file", default="todo.json")
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    # SUPPRESS keeps the subparser from clobbering a --json given before the
    # subcommand name with its own default.
    def add_common(sp):
        sp.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        sp.add_argument("--file", default=argparse.SUPPRESS)
        return sp

    a = add_common(sub.add_parser("add"))
    a.add_argument("text")
    a.set_defaults(func=cmd_add)

    add_common(sub.add_parser("list")).set_defaults(func=cmd_list)

    d = add_common(sub.add_parser("done"))
    d.add_argument("id", type=int)
    d.set_defaults(func=cmd_done)

    add_common(sub.add_parser("stats")).set_defaults(func=cmd_stats)

    args = p.parse_args(argv)
    tasks = load(args.file)
    args.func(args, tasks)


if __name__ == "__main__":
    main()
