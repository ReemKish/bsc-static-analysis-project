#!/usr/bin/env python3
import networkx as nx

MAX_ITERATIONS = 1024

def chaotic_iteration(num_vars: int, cfg: nx.DiGraph, method):
    # TODO: find the in degree 0 label and use it instead of assuming
    # it is always label 0
    assert cfg.in_degree(0) == 0, "label 0 is starting node for now"
    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)

    lattice = method(num_vars)

    X = [ lattice.top() ] + [ lattice.bottom() for _ in range(n-1) ]

    # start with (1,...,n) without 0 because 0 is already set to top
    work_s = set(range(1,n))

    num_iter = 0
    while work_s:
        i = work_s.pop()

        # In our version we analyze what we know BEFORE each program
        # poinrt instead of after, this causes a small change in the
        # transformation process - the transformers are applied before
        # joining instead of the other way around.
        prev_inds_asts = ((j, d['ast']) for j,d in rev_cfg[i].items())
        transed = (lattice.transform(ast,X[j]) for j, ast in prev_inds_asts)
        N = lattice.join(transed)
        if not lattice.equiv(N,X[i]):
            X[i] = N
            work_s.update(cfg[i])
        num_iter+=1
        if num_iter>=MAX_ITERATIONS:
            assert False, f"Iteration didn't finish in {MAX_ITERATIONS} iterations."
    return X

def vanilla_iteration(num_vars: int, cfg: nx.DiGraph, method):
    # TODO: find the in degree 0 label and use it instead
    assert cfg.in_degree(0) == 0, "label 0 is starting node for now"
    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)

    lattice = method(num_vars)

    X = [ lattice.top() ] + [ lattice.bottom() for _ in range(n-1) ]
    for k in range(MAX_ITERATIONS):
        X_old = X.copy()
        for i in range(1,n):
            prev_inds_asts = ((j, d['ast']) for j,d in rev_cfg[i].items())
            transed = [lattice.transform(ast,X_old[j])
                      for j,ast in prev_inds_asts]
            X[i] = lattice.join(transed)
        if all(lattice.equiv(cur, old) for cur,old in zip(X,X_old)):
            return X
    assert False, f"Iteration didn't finish in {MAX_ITERATIONS} iterations."

def _main():
    from parser import Parser
    from sys import argv
    from parity_analysis import PADumb
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    g,num_vars = p.parse_complete_program()
    res = chaotic_iteration(num_vars,g,PADumb)
    print('\n'.join(f'{i}. {v}' for i,v in enumerate(res)))

    #nx.draw(g, with_labels = True)
    #plt.show()

if __name__ == "__main__":
    _main()
