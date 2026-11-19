#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Put the nodes of a "must finish before" graph into columns, left to right.

What it reads: a list of nodes and a list of edges. An edge (a, b) means "a must finish before b
can start" - so a is drawn somewhere to the left of b.

What it returns (from layout(nodes, edges)) - a Layout with:
    column    {node: column number}. Column 0 holds every node nothing points at. Every other node
              sits one column to the right of the furthest-right node that points at it (this is
              called "longest path" layering), so every edge runs left to right.
    order     {column number: [nodes, top to bottom]}. The order inside each column is chosen to
              cut down how often lines cross: each node is moved towards the average position of
              the nodes it is joined to (the "barycentre" method), sweeping left to right and then
              right to left a few times.
    cycle     None, or one loop as a list of nodes [a, b, c, a]. A graph with a loop cannot be put
              into columns; column and order are then empty and the caller must refuse to draw.

Other helpers:
    find_cycle(nodes, edges)              one loop, or None
    longest_chain(nodes, edges, weight)   the longest chain of nodes, start to end. With no weight
                                          every node counts 1, so it is the chain with the most
                                          nodes (what a plan calls the critical path)
    crossings(order, edges, column)       how many pairs of lines between neighbouring columns cross

There is no geometry here: the build script turns columns into x positions and the order into y.
An edge that skips columns is the caller's to route. Standard library only.

    python layout_layers.py EDGES_FILE     # one edge per line: "a -> b"  (or "a b"); "#" starts a comment
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field


@dataclass
class Layout:
    column: dict = field(default_factory=dict)
    order: dict = field(default_factory=dict)
    cycle: list | None = None


def _check(nodes, edges):
    known = set(nodes)
    for a, b in edges:
        for n in (a, b):
            if n not in known:
                raise ValueError(f"edge {a!r} -> {b!r} names {n!r}, which is not in the node list")


def _succ(nodes, edges):
    out = {n: [] for n in nodes}
    for a, b in edges:
        if b not in out[a]:
            out[a].append(b)
    return out


def find_cycle(nodes, edges):
    """One loop as [a, b, ..., a], or None. Depth-first search, white / grey / black."""
    _check(nodes, edges)
    out = _succ(nodes, edges)
    state = {n: 0 for n in nodes}            # 0 not seen, 1 on the current path, 2 finished
    for start in nodes:
        if state[start]:
            continue
        path, stack = [], [(start, iter(out[start]))]
        state[start] = 1
        path.append(start)
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                path.pop()
                state[node] = 2
            elif state[nxt] == 1:
                return path[path.index(nxt):] + [nxt]
            elif state[nxt] == 0:
                state[nxt] = 1
                path.append(nxt)
                stack.append((nxt, iter(out[nxt])))
    return None


def _topo(nodes, edges):
    indeg = {n: 0 for n in nodes}
    out = _succ(nodes, edges)
    for a in nodes:
        for b in out[a]:
            indeg[b] += 1
    ready = [n for n in nodes if indeg[n] == 0]
    seq = []
    while ready:
        n = ready.pop(0)
        seq.append(n)
        for b in out[n]:
            indeg[b] -= 1
            if indeg[b] == 0:
                ready.append(b)
    return seq


def columns(nodes, edges):
    """{node: column} by longest path from a node nothing points at."""
    col = {n: 0 for n in nodes}
    out = _succ(nodes, edges)
    for n in _topo(nodes, edges):
        for b in out[n]:
            col[b] = max(col[b], col[n] + 1)
    return col


def longest_chain(nodes, edges, weight=None):
    """The heaviest chain start to end, as a list of nodes. weight(node) defaults to 1 for every
    node. Ties are broken by the order the nodes were given in, so the answer is repeatable."""
    _check(nodes, edges)
    w = weight or (lambda n: 1)
    out = _succ(nodes, edges)
    pred = {n: [] for n in nodes}
    for a in nodes:
        for b in out[a]:
            pred[b].append(a)
    best, back = {}, {}
    for n in _topo(nodes, edges):
        prev = max(pred[n], key=lambda p: (best[p], -nodes.index(p)), default=None)
        best[n] = w(n) + (best[prev] if prev is not None else 0)
        back[n] = prev
    if not best:
        return []
    end = max(nodes, key=lambda n: (best[n], -nodes.index(n)))
    chain = [end]
    while back[chain[-1]] is not None:
        chain.append(back[chain[-1]])
    return chain[::-1]


def crossings(order, edges, column):
    """Pairs of lines that cross. Only edges between neighbouring columns are counted, because an
    edge that skips columns is routed by the caller and its crossings depend on that routing."""
    pos = {n: i for col in order.values() for i, n in enumerate(col)}
    total = 0
    adj = [(a, b) for a, b in edges if column[b] == column[a] + 1]
    for i, (a1, b1) in enumerate(adj):
        for a2, b2 in adj[i + 1:]:
            if column[a1] != column[a2]:
                continue
            if (pos[a1] - pos[a2]) * (pos[b1] - pos[b2]) < 0:
                total += 1
    return total


def _sweep(order, edges, column, left_to_right):
    pos = {n: i for col in order.values() for i, n in enumerate(col)}
    cols = sorted(order) if left_to_right else sorted(order, reverse=True)
    for c in cols[1:]:
        # average position of the neighbours on the side already fixed in this sweep
        def bary(n):
            if left_to_right:
                ns = [pos[a] for a, b in edges if b == n and column[a] < c]
            else:
                ns = [pos[b] for a, b in edges if a == n and column[b] > c]
            return sum(ns) / len(ns) if ns else pos[n]
        order[c] = sorted(order[c], key=lambda n: (bary(n), pos[n]))
        for i, n in enumerate(order[c]):
            pos[n] = i


def layout(nodes, edges, passes=4):
    """Columns, an order inside each column that reduces crossings, and any loop found."""
    _check(nodes, edges)
    loop = find_cycle(nodes, edges)
    if loop:
        return Layout(cycle=loop)
    col = columns(nodes, edges)
    order = {}
    for n in nodes:                        # start in the order the nodes were given
        order.setdefault(col[n], []).append(n)
    best = {c: list(v) for c, v in order.items()}
    best_x = crossings(best, edges, col)
    for i in range(passes):
        _sweep(order, edges, col, left_to_right=(i % 2 == 0))
        x = crossings(order, edges, col)
        if x < best_x:
            best, best_x = {c: list(v) for c, v in order.items()}, x
    return Layout(column=col, order=dict(sorted(best.items())))


# ---------------------------------------------------------------------- command line
def _read_edges(path):
    nodes, edges = [], []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            parts = [p.strip() for p in (line.split("->") if "->" in line else line.split())]
            for p in parts:
                if p and p not in nodes:
                    nodes.append(p)
            if len(parts) == 2:
                edges.append((parts[0], parts[1]))
    return nodes, edges


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python layout_layers.py EDGES_FILE   (one 'a -> b' per line)", file=sys.stderr)
        return 2
    nodes, edges = _read_edges(argv[0])
    lay = layout(nodes, edges)
    if lay.cycle:
        print("LOOP - cannot be put into columns: " + " -> ".join(lay.cycle))
        return 1
    for c, ns in lay.order.items():
        print(f"column {c}: " + ", ".join(ns))
    chain = longest_chain(nodes, edges)
    print(f"\nlongest chain ({len(chain)} nodes): " + " -> ".join(chain))
    print(f"lines crossing between neighbouring columns: {crossings(lay.order, edges, lay.column)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
