#!/usr/bin/env python3
import networkx as nx

MAX_ITERATIONS = 1024

def vanilla_iteration(cfg: nx.DiGraph, lattice):
    # TODO: find the in degree 0 label and use it instead
    assert cfg.in_degree(0) == 0, "label 0 is starting node for now"
    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)
    X = [ lattice.top() ] + [ lattice.bottom() for _ in range(n-1) ]
    for _ in range(MAX_ITERATIONS):
        X_old = X.copy()
        for i in range(n):
            prev_inds_asts = ((j, d['ast']) for j,d in rev_cfg[i].items())
            transed = (lattice.transform(ast,X_old[j])
                      for j,ast in prev_inds_asts)
            X[i] = lattice.join(transed)
        if all(lattice.equiv(cur, old) for cur,old in zip(X,X_old)):
            return X
    assert False, f"Iteration didn't finish in {MAX_ITERATIONS} iterations."
