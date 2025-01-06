# the standard way to import PySAT:
from pysat.formula import CNF
from pysat.solvers import Solver

import sys
import time

import sdfa as SDFA


class sdfa_minimiser:
    # now we have trees, it is time to create numbers
    # 0 <= i < j <= n-1
    # 1. p_{j, i}: i is the parent of j in the BFS-tree
    # 2. e_{a,i,j}: i goes to j over letter a
    # 3. t_{i,j}: there is a transition from i to j
    # 4. r_{a,i,j}: there is a transition from i to j over a and no smaller transition


    def create_variables(self, n, alphabet, nb_states):

        num = 1
        # variables for DFA transitions
        prs = [(i, a, j) for i in range(n) for a in alphabet for j in range(n)]
        prs_m = prs
        edges = {element: (index + num) for index, element in enumerate(prs)}

        # variables for final states
        num += len(edges)
        sub_edges = {(i, -1, -1): (num + i) for i in range(n)}

        edges.update(sub_edges)

        # print("edge vars:\n" + str(edges))
        # variables for tree node and state
        num = len(edges) + 1
        prs = [(p, q) for p in range(nb_states) for q in range(n)]
        nodes = {element: (index + num) for index, element in enumerate(prs)}
        # print("node vars:\n" + str(nodes))

        # variables to encode BFS tree for DFA
        num += len(nodes)
        prs = [(p, q) for p in range(n) for q in range(n)]
        parents = {element: (index + num) for index, element in enumerate(prs)}
        # print("para vars:\n" + str(parents))

        num += len(parents)
        t_aux = {element: (index + num) for index, element in enumerate(prs)}
        # print("t vars:\n" + str(t_aux))

        num += len(t_aux)
        m_aux = {element: (index + num) for index, element in enumerate(prs_m)}
        # print("m vars:\n" + str(m_aux))

        return (nodes, edges, parents, t_aux, m_aux)


    # def search_vertex(gr, init_state, w):
    #     # from init to the state
    #     curr_state = init_state
    #     curr_index = 0
    #     # print (str(w))
    #     while True:
    #         if curr_index >= len(w):
    #             return curr_state
    #         # otherwise, we move to next one
    #         # print("curr_state = " + str(curr_state))
    #         # print("curr_index = " + str(curr_index))
    #         # print("g[curr_state]: " + str(gr[curr_state]))
    #         # print("w = " + str(w))
    #         # print("prev index: " + str(curr_index))
    #         succ = gr[curr_state][w[curr_index]]
    #         curr_index += 1
    #         # print("after index: " + str(curr_index))
    #         curr_state = succ


    def create_dfa_cnf(self, nodes, edges, input_sdfa, n, alphabet):

        clauses = []
        # A. deterministic transition formulas
        # A.1. not d_(p, a, q) or not d_(p, a, q')
        prs = [(p, a) for p in range(n) for a in alphabet]
        sub_clauses = []
        for p, a in prs:
            # must have one successor
            one_succ = [edges[p, a, q] for q in range(n)]
            sub_clauses = [one_succ] + sub_clauses
        clauses = sub_clauses + clauses

        # A.2. one edge over a letter
        diff_succs = [(q, qp) for q in range(n) for qp in range(n)]
        diff_succs = list(filter(lambda x: x[0] != x[1], diff_succs))
        # print("diff_succ: " + str(diff_succs))
        sub_clauses = [[0-edges[p, a, q], 0-edges[p, a, qp]]
                    for (p, a) in prs for (q, qp) in diff_succs]
        clauses = sub_clauses + clauses

        # B. consistent with samples
        # B.1. first ensure that initial states are empty word
        clauses += [[nodes[init, 0]] for init in input_sdfa.init_states]
        clauses += [[0-nodes[init, i]] for i in range(1, n) for init in input_sdfa.init_states]
        # B.2. setup final states
        # final_node = search_vertex(graph, init_state, pos[0])
        # print("final node: " + str(final_node))
        sub_clauses = [[0-nodes[final_node, q], edges[q, -1, -1]]
                    for q in range(n) for final_node in input_sdfa.final_states]

        # reject_node = search_vertex(graph, init_state, negs[0])
        # print("reject node: " + str(reject_node))
        sub_clauses = [[0-nodes[reject_node, q], -edges[q, -1, -1]]
                    for q in range(n) for reject_node in input_sdfa.reject_states] + sub_clauses

        clauses = sub_clauses + clauses
        # print("add clauses for samples")
        # B.3. consistent with samples
        prs = [(nr, dr, letter) for (nr, dr) in enumerate(input_sdfa.trans)
            for letter in alphabet]
        prs = list(filter(lambda x: (x[2] in x[1]), prs))
        # print (str(prs[0]))
        # check whether node has a child whose name is a
        # (nr, p) /\ edge(p, a, q) => (nr', q)
        sub_clauses = [[0-nodes[nr, p], 0-edges[p, letter, q], nodes[dr[letter], q]]
                    for (nr, dr, letter) in prs for p in range(n) for q in range(n)]
        # (nr, p) /\ (nr', q) => edge(p, a, q)
        # sub_clauses += [[0-nodes[nr, p], edges[p, letter, q], 0-nodes[dr[letter], q]]
        #               for (nr, dr, letter) in prs for p in range(n) for q in range(n)]
        clauses = sub_clauses + clauses

        #EXT. if they are two separate DFAs, we can just add
        # (s, p) and (t, p) cannot hold at the same time for final s and reject t
        # if they can reach the same states, then they must be not final and not reject
        # if len(init_state) == 2:
        #     max_init = max(init_state)
        #     max_state = max([ dr[letter] for (_, dr, letter) in prs])
        #     # s is final and t is reject, cannot reach the same state in DFA
        sub_clauses = [ [ -nodes[s, p], -nodes[t, p]] 
            for s in input_sdfa.final_states # not accept
            for t in input_sdfa.reject_states
            for p in range(0, n)] # the first posDFA

        clauses = sub_clauses + clauses
            

        return clauses

    # Symmetry breaking by enforcing a BFS-tree on the generated
    # DFA, so the form is unique
    # reference to "BFS-Based Symmetry Breaking Predicates
    # for DFA Identification"


    def create_BFStree_cnf(self, edges, parents, t_aux, m_aux, n, alphabet, safety):
        #print("adding constraints for BFS tree...")
        clauses = []
        # C. node BFS-tree constraints
        # 1. t_{i,j} <-> there is a transition from i to j
        prs = [(p, q) for p in range(n) for q in range(n)]
        # 1.1 e(p,a,q) => t(p,q)
        sub_cluases = [[0 - edges[p, a, q], t_aux[p, q]]
                    for a in alphabet for (p, q) in prs]
        # 1.2 t(p, q) => some e(p, a, q)
        for p, q in prs:
            edge_rel = [edges[p, a, q] for a in alphabet]
            edge_rel = [0 - t_aux[p, q]] + edge_rel
            sub_cluases = [edge_rel] + sub_cluases

        clauses = sub_cluases + clauses

        # 2. BFS tree order
        # 2.1 p_{j, i} i is the parent of j
        sub_cluases = []
        for j in range(1, n):
            # only one p_{j, 0}, p_{j,1} ... only one parent

            one_parent = [parents[j, i] for i in range(j)]
            sub_cluases = [one_parent] + sub_cluases

            # p_{j,i} => t_{i,j}
            exist_edges = [[0 - parents[j, i], t_aux[i, j]] for i in range(j)]
            sub_cluases = exist_edges + sub_cluases

            # t_{i,j} /\ !t_{i-1, j} /\ !t_{i-2,j} /\ ... /\ !t_{0,j} => p_{j,i}
            for i in range(j):
                no_smaller_pred = [t_aux[k, j] for k in range(i)]
                no_smaller_pred = [0-t_aux[i, j], parents[j, i]] + no_smaller_pred
                sub_cluases = [no_smaller_pred] + sub_cluases

        clauses = sub_cluases + clauses

        ij_pairs = [(i, j) for j in range(n) for i in range(n)]
        ij_pairs = list(filter(lambda x: x[0] < x[1], ij_pairs))

        sub_cluases = []
        for i, j in ij_pairs:
            # only k < i < j, p_{j,i} => ! t_{k,j}
            # if i is parent of j in the BFS-tree, then no edge from k to j
            # otherwise k will traverse j first
            k_vals = list(range(i))
            no_smaller_edges = [[0-parents[j, i], 0-t_aux[k, j]] for k in k_vals]
            sub_cluases = no_smaller_edges + sub_cluases

        clauses = sub_cluases + clauses

        # 3. relation to edges
        # m_{i, a, j} => e_{i, a, j}
        edge_rel = [[0-m_aux[i, a, j], edges[i, a, j]]
                    for a in alphabet for (i, j) in ij_pairs]

        kh_pairs = [(k, h) for h in alphabet for k in alphabet]
        kh_pairs = list(filter(lambda x: x[0] < x[1], kh_pairs))
        # larger h > k, m_{i, h, j} => ! e_{i, k, j}
        # if there is a larger letter over i -> j in the BFS-tree,
        # then there must be no edge from i to j over a smaller letter
        edge_rel = [[0-m_aux[i, h, j], 0-edges[i, k, j]]
                    for (k, h) in kh_pairs for (i, j) in ij_pairs] + edge_rel
        clauses = edge_rel + clauses

        # for every (i,j), e_{i,h,j} /\ ! e_{i,h-1,j} /\ .../\ !e_{i,0,j} => m_{i,h,j}
        # that is, if h is the smallest letter from i to j, then it is in BFS tree
        sub_cluases = []
        prs = [(i, j, a) for (i, j) in ij_pairs for a in alphabet]
        for i, j, a in prs:
            edge_rel = [edges[i, h, j] for h in range(a)]  # smaller letters
            edge_rel = [0-edges[i, a, j], m_aux[i, a, j]] + edge_rel
            sub_cluases = [edge_rel] + sub_cluases

        clauses = sub_cluases + clauses

        max_state = -1
        if safety: 
            max_state = n - 2 
        else: 
            max_state = n - 1
        # 4. BFS tree parent-child relation
        ijk_pairs = [(k, i, j) for k in range(n-1)
                    for i in range(n-1) for j in range(max_state)]
        ijk_pairs = list(filter(lambda x: x[0] < x[1] and x[1] < x[2], ijk_pairs))
        # p_{j, i} => !p_{j+1, k}, it means that i is parent of j, then k is not possible to be the parent of j + 1
        # since k is even smaller than i
        edge_rel = [[0 - parents[j, i], 0-parents[j+1, k]]
                    for (k, i, j) in ijk_pairs]

        ij_pairs = [(i, j) for j in range(max_state) for i in range(n-1)]
        ij_pairs = list(filter(lambda x: x[0] < x[1], ij_pairs))
        # (6)
        # p_{j,i} /\ p_{j+1, i} /\ m_{i,h,j} => !m_{i,k,j+1}
        # if i is parent of both j and j + 1, and in the BFS-tree, we have i ->j over h,
        # then there is no smaller letter k from i to j+1?
        edge_rel = [[0-parents[j, i], 0-parents[j+1, i], 0-m_aux[i, h, j], 0-m_aux[i, k, j+1]]
                    for (i, j) in ij_pairs for (k, h) in kh_pairs] + edge_rel

        clauses = edge_rel + clauses

        return clauses

    # here we define the DSA constraints
    # DSA with n-1 safe states and 1 rejecting sink
    # 1. for all odd letter a, it follows that Tr(0, a) = q then q not 0 and not sink
    # 2. for all even letter a, it follows that Tr(0, a) = 0; Tr(i, a) = n implies i = n and Tr(i, a) = 0 implies i = 0
    # 3. if the maximal number is even, say h, i < n (not sink) implies Tr(i, h) = 0
    # 4. Tr(0, 1) = 1
    def create_DSA_cnf(self, edges, n, alphabet):

        #print("adding constraints for safety automaton...")
        max_letter = max (alphabet)
        clauses = []
        is_max_even = max_letter % 2 == 0 
        if is_max_even:   
            #A first set sink to be n-1
            clauses += [[-edges[n-1, -1, -1]]] 
            #B other states will be accepting
            clauses += [ [edges[s, -1, -1]] for s in range(0, n-1)]
        else:
            # highest color is odd, we construct reachability DFA
            #A first set sink accepting to be n-1
            clauses += [[edges[n-1, -1, -1]]] 
            #B other states will be rejecting
            clauses += [ [-edges[s, -1, -1]] for s in range(0, n-1)]

        #C. sink only has self-loops
        clauses += [ [edges[n-1, a, n-1]] for a in alphabet]
        # more specific to DSA for parity games 
        #4. 0 goes o 1 over 1
        if len(alphabet) > 1 and n > 1 and is_max_even:
                clauses += [[edges[0, 1, 1]]]
                
        
        #1. this should be true
        odd_letters = [ num for num in alphabet if num % 2 != 0]
        even_letters = [ num for num in alphabet if num % 2 == 0]

        # if maximam color is odd, swap
        if not is_max_even:
            temp = odd_letters
            odd_letters = even_letters
            even_letters = temp
        
        clauses += [[-edges[0, ol, 0]] for ol in odd_letters]
        clauses += [[-edges[0, ol, n-1]] for ol in odd_letters]

        
        #2. even letter a, we have Tr(0, a, 0) = true
        clauses += [[edges[0, el, 0]] for el in even_letters]
        #2.A i \neq n implies Tr(i, a, n) = false
        s_even = [ (s, el) for s in range(0, n-1) for el in even_letters]
        clauses += [ [-edges[s, el, n-1]] for (s, el) in s_even]
        #2.B i not 0 implies Tr(i, a, 0) = false
        #snot0_even = [ (s, el) for s in range(1, n) for el in even_letters]
        #clauses += [ [-edges[s, el, 0]] for (s, el) in snot0_even]

        #3. reset: highest color goes back to 0
        clauses += [ [edges[s, max_letter, 0]] for s in range(0, n-1)]

        #4. loop condition: no state but the sink can loop over
        # a colour of an opponent parity as the highest one
        clauses += [ [-edges[s, ol, s]] for s in range(0, n-1) for ol in odd_letters]

        #5. progress-n: whenever a state reads a colour of the same parity as the 
        # highest one, it cannot reach the sink
        clauses += [ [-edges[s, el, n-1]] for s in range(0, n-1) for el in even_letters]

        
        return clauses


    def create_cnf(self, nodes, edges, parents, t_aux, m_aux, input_sdfa
                , n, alphabet, nobfs, safety):
        clauses = self.create_dfa_cnf(nodes, edges, input_sdfa,
                                n, alphabet)
        if not nobfs:
            sub_clauses = self.create_BFStree_cnf(edges, parents, t_aux, m_aux, n, alphabet, safety)
            clauses = sub_clauses + clauses
        
        if safety:
            sub_clauses = self.create_DSA_cnf(edges, n, alphabet)
            clauses = sub_clauses + clauses

        #for cls in clauses:
        #    print(cls)
        return clauses


    def construct_dfa_from_model(self, model, edges, n, alphabet):
        # print("type(model) = " + str(type(model)))
        dfa = SDFA.sdfa()
        dfa.set_num_states(n)
        dfa.set_num_letters(len(alphabet))
        for p in range(n):
            # print("State " + str(p))
            is_final = False
            if model[edges[p, -1, -1] - 1] > 0:
                # print(" final")
                is_final = True
            for a, letter in enumerate(alphabet):
                # print("a =" +str(a) + ", letter=" + str(letter))
                for q in range(n):
                    if model[edges[p, a, q] - 1] > 0:
                        # print("var = " + str(e1[p, a, q]))
                        # print("letter " + str(letter) + " -> " + str(q))
                        dfa.add_transition(p, a, q)
            if is_final:
                dfa.add_final_state(p)
            #else:
            #    dfa.add_reject_state(p)

        dfa.add_initial_state(0)
        return dfa


    def solve(self,
            sat, n, alphabet, input_sdfa, nobfs, safety):

        nodes, edges, parents, t_aux, m_aux = self.create_variables(n, alphabet, input_sdfa.num_states)
        # solvers, Glucose3(), Cadical103(), Cadical153(), Gluecard4(), Glucose42()
        # g = Cadical153() #Lingeling() #Glucose42()
        # g = Glucose42()
        g = Solver(name=sat)

        clauses = self.create_cnf(nodes, edges, parents, t_aux, m_aux,
                            input_sdfa, n, alphabet, nobfs, safety)
        #print("Created # of vars: " + str(len(nodes) + len(edges) +
        #    len(parents) + len(t_aux) + len(m_aux)))
        #print("Created # of clauses: " + str(len(clauses)))
        for cls in clauses:
            g.add_clause(cls)

        is_sat = g.solve()
        #print(is_sat)

        if is_sat:
            #print(g.get_model())
            #print("Found a DFA with size " + str(n))
            model = g.get_model()
            # now print out transition relation
            # print("type(model) = " + str(type(model)))
            dfa = self.construct_dfa_from_model(model, edges, n, alphabet)
            return (True, dfa)
        else:
            #print("No DFA existing for size " + str(n))
            return (False, None)


    def minimise(self,
            input_sdfa, sat, lbound, ubound, nobfs, safety):

        alphabet = list(range(input_sdfa.num_letters))
        n = lbound
        max_bound = min([input_sdfa.num_states, ubound])
        # the maximal number of states must not be bigger than
        # the number of states in the input FA
        result_dfa = None
        #print("Input SDFA size: " + str(input_sdfa.num_states))
        #print("Input alphabet size: " + str(input_sdfa.num_letters))

        start_time = time.time()
        while n <= max_bound:
            #print("Looking for DFA with " + str(n) + " states...")
            res, dfa = self.solve(sat, n, alphabet, input_sdfa, nobfs, safety)
            if res:
                result_dfa = dfa
                break
            else:
                n += 1
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 4)
        #print(f"Elapsed time in minimiser: {elapsed_time} secs")
        return result_dfa



solver_choices = {"cadical103", "cadical153", "gluecard4", "glucose4",
                  "glucose42", "lingeling", "maplechrono", "mergesat3", "minisat22"}

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Obtain minimal equivalent DFA for automata with dont care words')
    parser.add_argument('--f', metavar='path', required=True,
                        help='path to input FA')
    parser.add_argument('--out', metavar='path', required=True,
                        help='path to output FA')
    parser.add_argument('--solver', type=str.lower, required=False,
                        choices=solver_choices, default="cadical153",
                        help='choose the SAT solver')
    parser.add_argument('--lower', type=int, required=False,
                        default=1,
                        help='the lower bound for the DFA')
    parser.add_argument('--upper', type=int, required=False,
                        default=sys.maxsize,
                        help='the upper bound for the DFA')
    parser.add_argument('--nobfs', action="store_true", required=False,
                        default=False,
                        help='disable the constraints for BFS tree')
    parser.add_argument('--safety', action="store_true", required=False,
                        default=False,
                        help='construct safety DFA for solving parity games')
    args = parser.parse_args()
    minimiser = sdfa_minimiser() 
    sdfa = SDFA.sdfa()
    sdfa.load(args.f)
    #print("Launch sdfa minimiser...")
    dfa = minimiser.minimise(input_sdfa=sdfa, sat=args.solver
         , lbound=args.lower, ubound=args.upper, nobfs=args.nobfs, safety=args.safety)
    #print("Output to " + args.out)
    with open(args.out, "w") as file:
        file.write(dfa.dot())
