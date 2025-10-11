#!/usr/bin/env python3
"""Simple trace summary reporter.

Reads the trace_summary.json produced by `tools.trace` and prints the top N
functions sorted by total time (descending).
"""
import os
import json
import argparse


def load_summary(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Summary file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def print_top(summary, top: int = 20):
    print(f"Top {top} functions by total time:\n")
    print(f"{'rank':>4}  {'total(s)':>10}  {'count':>6}  {'avg(s)':>8}  {'max(s)':>8}  name")
    for i, item in enumerate(summary[:top], start=1):
        print(f"{i:>4}  {item.get('total',0):10.4f}  {item.get('count',0):6d}  {item.get('avg',0):8.4f}  {item.get('max',0):8.4f}  {item.get('name')}")


def main():
    here = os.path.dirname(__file__)
    default_path = os.path.join(here, 'trace_summary.json')

    p = argparse.ArgumentParser()
    p.add_argument('--file', '-f', default=default_path, help='path to trace_summary.json')
    p.add_argument('--top', '-n', type=int, default=20, help='how many top entries to show')
    args = p.parse_args()

    try:
        summary = load_summary(args.file)
    except Exception as e:
        print('Error loading summary:', e)
        return

    print_top(summary, args.top)


if __name__ == '__main__':
    main()
