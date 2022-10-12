#!/usr/bin/env python3
import networkx as nx
from typing import Type
import analysis

MAX_ITERATIONS = 1024

def _find_start_node(cfg: nx.DiGraph):
    root_nodes = [n for n,d in cfg.in_degree() if d==0]
    assert len(root_nodes) > 0, "There should be a node with no incoming edges"
    assert len(root_nodes) == 1, "Only one node should have no incoming edges!"
    return root_nodes[0]

def chaotic_iteration(num_vars: int, cfg: nx.DiGraph,
                      method: Type[analysis.BaseAnalysis]):
    from random import shuffle

    cfg = nx.convert_node_labels_to_integers(cfg, label_attribute="original_label")

    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)
    lattice = method(num_vars)

    start_node = _find_start_node(cfg)

    X = [ lattice.bottom() ] * n
    X[start_node] = lattice.top()

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
        # poinrt instead of after, this causes a small change in the
        # transformation process - the transformers are applied before
        # joining instead of the other way around.
        prev_inds_asts = ((j, d['ast']) for j,d in rev_cfg[i].items())
        transed = (lattice.transform(ast,X[j]) for j, ast in prev_inds_asts)
        N = lattice.join(transed)

        # See the stabilize method documention in BaseAnalysis class
        # for documentation
        N = lattice.stabilize(N)

        if not lattice.equiv(N,X[i]):
            X[i] = N
            work_s.update(cfg[i])
        num_iter+=1
        if num_iter>=MAX_ITERATIONS:
            assert False, f"Iteration didn't finish in {MAX_ITERATIONS} iterations."
    return {cfg.nodes[i]['original_label']:X[i] for i in range(n)}

def _print_analysis(res):
    print(type(res))
    print('\n'.join(f'L{i}.\n {v}' for i,v in res.items()))

def test_analysis(method: Type[analysis.BaseAnalysis]):
    from parser import Parser
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    g,num_vars = p.parse_complete_program()
    res = chaotic_iteration(num_vars,g,method)
    _print_analysis(res)


def _main():
    from parity_analysis import PADumb
    test_analysis(PADumb)

if __name__ == "__main__":
    _main()
