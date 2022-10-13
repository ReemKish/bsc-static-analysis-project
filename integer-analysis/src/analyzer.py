#!/usr/bin/env python3
import networkx as nx

MAX_ITERATIONS = 1024

def chaotic_iteration(cfg: nx.DiGraph, analysis, verbose=False):
    from random import shuffle

    # TODO: find the in degree 0 label and use it instead of assuming
    # it is always label 0
    assert cfg.in_degree(0) == 0, "label 0 is starting node for now"
    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)
    lattice = analysis.lat

    X = [ lattice.top() ] + [ lattice.bot() for _ in range(n-1) ]

    # start with (1,...,n) without 0 because 0 is already set to top
    initial_inds = range(1,n)
    work_s = set(initial_inds)

    num_iter = 0
    while work_s:

        # pop-order randomization
        #l = list(work_s)
        #shuffle(l)
        #i = l.pop()
        #work_s = set(l)

        # no randomization
        i = work_s.pop()

        # In our version we analyze what we know BEFORE each program
        # pointer instead of after, this causes a small change in the
        # transformation process - the transformers are applied before
        # joining instead of the other way around.
        prev_inds_asts = list((j, d['ast']) for j,d in rev_cfg[i].items())
        transed = list(analysis.transform(ast,X[j]) for j, ast in prev_inds_asts)

        if verbose: print(f"[{num_iter}] i={i}, X={X}, prev_inds_asts={prev_inds_asts}, transed={transed}")

        N = lattice.join(*transed)

        # See the stabilize method documention in BaseAnalysis class
        # for documentation
        N = analysis.stabilize(N)

        #if len(N)!=num_vars:
        #    print('\n'.join(f"X[i] = {X[i]}",
        #                    f"transed = {transed}",
        #                    f"N = {N}"
        #                   )
        #         )

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

    X = [ lattice.top() ] + [ lattice.bot() for _ in range(n-1) ]
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

def _print_res(res):
    print('\n'.join(f'{i}. {v}' for i,v in enumerate(res)))

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
    res = map(list,res)
    _print_res(res)
   # X = X_old = res
   # for _ in range(30):
   #     X = chaotic_iteration(num_vars,g,PADumb)
   #     X = list(map(list, X))
   #     _print_res(X_old)
   #     print("---------------")
   #     _print_res(X)
   #     if not all(PADumb(num_vars).equiv(cur, old) for cur,old in zip(X,X_old)):
   #         assert False
   #     X_old = X

    #nx.draw(g, with_labels = True)
    #plt.show()

if __name__ == "__main__":
    _main()
