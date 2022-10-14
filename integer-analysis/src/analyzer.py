#!/usr/bin/env python3
from ast_nodes import Assert
import networkx as nx
from typing import Type, List, Tuple, Dict
import analysis

MAX_ITERATIONS = 1024


def _find_start_node(cfg: nx.DiGraph):
    root_nodes = [n for n,d in cfg.in_degree() if d==0]
    assert len(root_nodes) > 0, "There should be a node with no incoming edges"
    assert len(root_nodes) == 1, "Only one node should have no incoming edges!"
    return root_nodes[0]

def chaotic_iteration(num_vars: int, cfg: nx.DiGraph,
                      method: Type[analysis.BaseAnalysis],
                      verbose=False):
    cfg = nx.convert_node_labels_to_integers(cfg, label_attribute="original_label")

    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)
    analysis = method(num_vars)

    start_node = _find_start_node(cfg)

    X = [ analysis.bottom() ] * n
    X[start_node] = analysis.top()

    initial_worklist_nodes = range(n)
    work_s = set(initial_worklist_nodes)
    work_s.remove(start_node)

    num_iter = 0
    while work_s:
        # no randomization
        i = work_s.pop()

        # In our version we analyze what we know BEFORE each program
        # pointer instead of after, this causes a small change in the
        # transformation process - the transformers are applied before
        # joining instead of the other way around.
        prev_inds_asts = list((j, d['ast']) for j,d in rev_cfg[i].items())
        transed = list(analysis.transform(ast,X[j]) for j, ast in prev_inds_asts)

        if verbose: print(f"[{num_iter}] i={i}, X={X}, prev_inds_asts={prev_inds_asts}, transed={transed}")

        N = analysis.join(transed)

        # See the stabilize method documention in BaseAnalysis class
        # for documentation
        N = analysis.stabilize(N)

        if not analysis.equiv(N,X[i]):
            X[i] = N
            work_s.update(cfg[i])
        num_iter+=1
        if num_iter>=MAX_ITERATIONS:
            assert False, f"Iteration didn't finish in {MAX_ITERATIONS} iterations."
    return {cfg.nodes[i]['original_label']:X[i] for i in range(n)}

def _print_res(res):
    print('\n'.join(f'{i}. {res[i]}' for i in res.keys()))

def get_all_assertions(cfg: nx.DiGraph) -> List[Tuple[int, Assert]]:
    """Retrieves all assertion statements of a program from its control flow graph.

    Returns a list of tuples of a the form: (label index, Assert command).
    """
    l = []
    for i in cfg:
        for ast in [d['ast'] for _,d in cfg[i].items() if isinstance(d['ast'], Assert)]:
            l.append((i, ast))
    return l

# def validate_assertions(analysis: analysis.BaseAnalysis,
#                         assertions: List[Tuple[int, Assert]],
#                         fixpoint):
#     """Uses an analysis to validates a sequence of assertions against a fixpoint.
#
#     Returns a dictionary mapping each tuple in `assertions` (see get_all_assertions documention)
#     to a boolean that indicates whether the assertion could be validated (always holds) or not.
#     """
#     d = dict()
#     for label, ass in assertions:
#         d[(label, ass)] = analysis.validate_assertion(ass, fixpoint)
#     return d
        


def debug_analysis(method: Type[analysis.BaseAnalysis]):
    from parser import Parser
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cfg, num_vars = p.parse_complete_program()
    res = chaotic_iteration(num_vars, cfg, method)
    _print_res(res)


def run_analysis(method: Type[analysis.BaseAnalysis]):
    from parser import Parser
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cfg, num_vars = p.parse_complete_program()
    assertions = get_all_assertions(cfg)
    fixpoint = chaotic_iteration(num_vars, cfg, method)
    # d = validate_assertions(method, assertions, fixpoint)
    _print_res(fixpoint)
