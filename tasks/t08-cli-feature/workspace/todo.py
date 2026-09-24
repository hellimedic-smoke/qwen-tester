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
    print(f"added #{task['id']}: {task['text']}")


def cmd_list(args, tasks):
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
            print(f"completed #{t['id']}: {t['text']}")
            return
    print(f"no task #{args.id}", file=sys.stderr)
    sys.exit(1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="todo")
    p.add_argument("--file", default="todo.json")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("text")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list")
    l.set_defaults(func=cmd_list)

    d = sub.add_parser("done")
    d.add_argument("id", type=int)
    d.set_defaults(func=cmd_done)

    args = p.parse_args(argv)
    tasks = load(args.file)
    args.func(args, tasks)


if __name__ == "__main__":
    main()
