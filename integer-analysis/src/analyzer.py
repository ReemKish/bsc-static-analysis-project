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

def chaotic_iteration(cfg: nx.DiGraph,
                      analysis: analysis.BaseAnalysis,
                      verbose=False):
    cfg = nx.convert_node_labels_to_integers(cfg, label_attribute="original_label")

    n = len(cfg)
    rev_cfg = nx.reverse_view(cfg)

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

def _print_fixpoint(res):
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

def verify_assertions(analysis: analysis.BaseAnalysis,
                        assertions: List[Tuple[int, Assert]],
                        fixpoint):
    """Uses an analysis to verify a sequence of assertions against a fixpoint.

    Returns a dictionary mapping each tuple in `assertions` (see get_all_assertions documention)
    to a boolean that indicates whether the assertion could be validated (always holds) or not.
    """
    d = dict()
    for label_ind, assertion in assertions:
        d[(label_ind, assertion)] = analysis.verify_assertion(assertion, fixpoint[label_ind])
    return d

def debug_analysis(method: Type[analysis.BaseAnalysis], verbose=False):
    from parser import Parser
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cfg, num_vars = p.parse_complete_program()
    analysis = method(num_vars)
    fixpoint = chaotic_iteration(cfg, analysis, verbose=verbose)
    _print_fixpoint(fixpoint)

def print_analysis_results(conclusions):
    """Pretty-prints to the console the results of an analysis.
    
    The input dictionary is the one returned from verify_assertions.
    """
    STYLE_UNDERLINE = "\033[4m"
    STYLE_BOLD = "\033[1m"
    STYLE_GREEN = "\033[92m"
    STYLE_RED = "\033[31m"
    STYLE_RESET = "\033[0m"

    valid = []; invalid = []
    for t, verified in conclusions.items():
        (valid if verified else invalid).append(t)

    if valid: 
        print(f"The program {STYLE_UNDERLINE}does not violate{STYLE_RESET} the following assertions:")
        for label_ind, assertion in valid:
            print(f"  {STYLE_GREEN}✓{STYLE_RESET} {STYLE_BOLD}L{label_ind}{STYLE_RESET}", end=" ")
            print(assertion)

    if invalid: 
        print(f"\nThe analysis {STYLE_UNDERLINE}could not prove{STYLE_RESET} the following assertions:")
        for label_ind, assertion in invalid:
            print(f"  {STYLE_RED}*{STYLE_RESET} {STYLE_BOLD}L{label_ind}{STYLE_RESET}", end=" ")
            print(assertion)



def run_analysis(method: Type[analysis.BaseAnalysis]):
    from parser import Parser
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cfg, num_vars = p.parse_complete_program()
    analysis = method(num_vars)
    assertions = get_all_assertions(cfg)
    fixpoint = chaotic_iteration(cfg, analysis)
    conclusions = verify_assertions(analysis, assertions, fixpoint)
    print_analysis_results(conclusions)
