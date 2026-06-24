import time
import random
import numpy as np
import scipy.sparse
import scipy.sparse.linalg
from scipy.optimize import linprog

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

def recursive_unit_propagation_and_reductions(num_vars, clauses, active_vars=None, verbose=False):
    """
    Recursively applies unit propagation and pure literal elimination.
    """
    fixed_literals = {}
    active_clauses = [list(c) for c in clauses]
    if active_vars is None:
        active_vars = set(range(1, num_vars + 1))
    else:
        active_vars = set(active_vars)
    fixed_empty_clauses = 0
    
    changed = True
    while changed:
        changed = False
        
        # Count empty clauses
        empty_clauses = sum(1 for c in active_clauses if len(c) == 0)
        if empty_clauses:
            fixed_empty_clauses += empty_clauses
            active_clauses = [c for c in active_clauses if len(c) > 0]
        
        # 1. Unit propagation
        unit_counts = {}
        for c in active_clauses:
            if len(c) == 1:
                lit = c[0]
                unit_counts[lit] = unit_counts.get(lit, 0) + 1
                
        if unit_counts:
            var_unit_info = {}
            for lit, count in unit_counts.items():
                var = abs(lit)
                pol = 1 if lit > 0 else -1
                if var not in var_unit_info:
                    var_unit_info[var] = {1: 0, -1: 0}
                var_unit_info[var][pol] = count
                
            for var in sorted(list(var_unit_info.keys())):
                info = var_unit_info[var]
                pos_units = info[1]
                neg_units = info[-1]
                
                if pos_units >= neg_units:
                    l_val = 1
                    m = pos_units
                    opp_units = neg_units
                else:
                    l_val = -1
                    m = neg_units
                    opp_units = pos_units
                    
                opp_clauses_count = 0
                for c in active_clauses:
                    if len(c) >= 2:
                        for lit in c:
                            if abs(lit) == var:
                                pol = 1 if lit > 0 else -1
                                if pol != l_val:
                                    opp_clauses_count += 1
                                    break
                                    
                k = opp_clauses_count + opp_units
                
                if m >= k:
                    fixed_literals[var] = l_val
                    active_vars.remove(var)
                    
                    new_active_clauses = []
                    for c in active_clauses:
                        satisfied = False
                        for lit in c:
                            if abs(lit) == var:
                                pol = 1 if lit > 0 else -1
                                if pol == l_val:
                                    satisfied = True
                                    break
                        if not satisfied:
                            new_clause = [lit for lit in c if abs(lit) != var]
                            new_active_clauses.append(new_clause)
                    active_clauses = new_active_clauses
                    changed = True
                    break
            if changed:
                continue
                
        # 2. Pure literal elimination
        pos_counts = {v: 0 for v in active_vars}
        neg_counts = {v: 0 for v in active_vars}
        for c in active_clauses:
            for lit in c:
                var = abs(lit)
                if var in active_vars:
                    if lit > 0:
                        pos_counts[var] += 1
                    else:
                        neg_counts[var] += 1
                        
        pure_vars = []
        for var in list(active_vars):
            pos = pos_counts[var]
            neg = neg_counts[var]
            if pos > 0 and neg == 0:
                pure_vars.append((var, 1))
            elif neg > 0 and pos == 0:
                pure_vars.append((var, -1))
            elif pos == 0 and neg == 0:
                pure_vars.append((var, 1))
                
        if pure_vars:
            changed = True
            for var, val in pure_vars:
                fixed_literals[var] = val
                active_vars.remove(var)
            
            new_active_clauses = []
            for c in active_clauses:
                satisfied = False
                for lit in c:
                    var = abs(lit)
                    val = 1 if lit > 0 else -1
                    if var in fixed_literals and fixed_literals[var] == val:
                        satisfied = True
                        break
                if not satisfied:
                    new_clause = [lit for lit in c if abs(lit) in active_vars]
                    new_active_clauses.append(new_clause)
            active_clauses = new_active_clauses
            
    return active_vars, active_clauses, fixed_literals, fixed_empty_clauses

def normalize_and_clean_clauses(clauses):
    """
    Normalizes a list of clauses by removing duplicate literals,
    removing tautologies, and sorting literals for canonical representation.
    """
    cleaned_clauses = []
    for c in clauses:
        seen = set()
        new_c = []
        tautology = False
        for lit in c:
            if lit in seen:
                continue
            if -lit in seen:
                tautology = True
                break
            seen.add(lit)
            new_c.append(lit)
        if not tautology:
            new_c.sort(key=lambda x: abs(x))
            cleaned_clauses.append(new_c)
    return cleaned_clauses

def build_signed_graph_for_3sat(num_vars, active_vars, active_clauses, u=1.0, verbose=False):
    """
    Builds the extended signed graph.
    Applies triplet-level Walsh-Fourier simplification and merges auxiliary nodes 
    sharing the same canonical/best literal pair.
    """
    var_list = sorted(list(active_vars))
    var_to_idx = {v: i + 1 for i, v in enumerate(var_list)}
    N_red = len(var_list)
    
    # 1. Group ternary clauses by variable index triplet
    triplet_to_clauses = {}
    for c in active_clauses:
        if len(c) == 3:
            v1, v2, v3 = abs(c[0]), abs(c[1]), abs(c[2])
            idx1, idx2, idx3 = var_to_idx[v1], var_to_idx[v2], var_to_idx[v3]
            pol1 = 1 if c[0] > 0 else -1
            pol2 = 1 if c[1] > 0 else -1
            pol3 = 1 if c[2] > 0 else -1
            
            lits = [(idx1, pol1), (idx2, pol2), (idx3, pol3)]
            lits.sort(key=lambda x: x[0])
            
            triplet = (lits[0][0], lits[1][0], lits[2][0])
            if triplet not in triplet_to_clauses:
                triplet_to_clauses[triplet] = []
            triplet_to_clauses[triplet].append(lits)
            
    direct_edges = []
    effective_clauses = []
    
    for triplet, list_of_clauses in triplet_to_clauses.items():
        idx1, idx2, idx3 = triplet
        
        # Calculate sum of sign products
        sign_sum = 0
        for lits in list_of_clauses:
            sign_sum += lits[0][1] * lits[1][1] * lits[2][1]
            
        lambda_val = u * abs(sign_sum)
        
        # Calculate base linear and quadratic coefficients
        h = [0.0, 0.0, 0.0]
        J = {(0,1): 0.0, (1,2): 0.0, (0,2): 0.0}
        
        for lits in list_of_clauses:
            for r in range(3):
                h[r] += -u / 8.0 * lits[r][1]
            J[(0,1)] += (u / 8.0) * lits[0][1] * lits[1][1]
            J[(1,2)] += (u / 8.0) * lits[1][1] * lits[2][1]
            J[(0,2)] += (u / 8.0) * lits[0][1] * lits[2][1]
            
        if lambda_val < 1e-9:
            # Complete cancellation! No auxiliary needed.
            for r, idx in enumerate([idx1, idx2, idx3]):
                if abs(h[r]) > 1e-9:
                    direct_edges.append((idx, 0, 2.0 * abs(h[r]), -1 if h[r] > 0 else 1))
            for (r, m), idx_pair in [((0, 1), (idx1, idx2)), ((1, 2), (idx2, idx3)), ((0, 2), (idx1, idx3))]:
                coeff = J[(r, m)]
                if abs(coeff) > 1e-9:
                    direct_edges.append((idx_pair[0], idx_pair[1], 2.0 * abs(coeff), -1 if coeff > 0 else 1))
        else:
            # We need exactly one auxiliary
            pi1 = 1
            pi2 = 1
            pi3 = 1 if sign_sum > 0 else -1
            pi = [pi1, pi2, pi3]
            
            h_diff = [0.0, 0.0, 0.0]
            for r in range(3):
                h_diff[r] = h[r] + (lambda_val / 8.0) * pi[r]
                
            J_diff = {(0,1): 0.0, (1,2): 0.0, (0,2): 0.0}
            J_diff[(0,1)] = J[(0,1)] - (lambda_val / 8.0) * pi1 * pi2
            J_diff[(1,2)] = J[(1,2)] - (lambda_val / 8.0) * pi2 * pi3
            J_diff[(0,2)] = J[(0,2)] - (lambda_val / 8.0) * pi1 * pi3
            
            for r, idx in enumerate([idx1, idx2, idx3]):
                if abs(h_diff[r]) > 1e-9:
                    direct_edges.append((idx, 0, 2.0 * abs(h_diff[r]), -1 if h_diff[r] > 0 else 1))
            for (r, m), idx_pair in [((0, 1), (idx1, idx2)), ((1, 2), (idx2, idx3)), ((0, 2), (idx1, idx3))]:
                coeff = J_diff[(r, m)]
                if abs(coeff) > 1e-9:
                    direct_edges.append((idx_pair[0], idx_pair[1], 2.0 * abs(coeff), -1 if coeff > 0 else 1))
                    
            effective_clauses.append((idx1, idx2, idx3, pi1, pi2, pi3, lambda_val))
            
    # Count pair frequencies among effective clauses (best shared pair heuristic)
    pair_counts = {}
    raw_eff = []
    for idx1, idx2, idx3, pi1, pi2, pi3, lambda_val in effective_clauses:
        p12 = (idx1, pi1, idx2, pi2)
        p23 = (idx2, pi2, idx3, pi3)
        p13 = (idx1, pi1, idx3, pi3)
        for p in (p12, p23, p13):
            pair_counts[p] = pair_counts.get(p, 0) + 1
        raw_eff.append((idx1, idx2, idx3, pi1, pi2, pi3, lambda_val, p12, p23, p13))
        
    clause3_list = []
    for idx1, idx2, idx3, pi1, pi2, pi3, lambda_val, p12, p23, p13 in raw_eff:
        candidate_pairs = [p12, p13, p23]
        candidate_pairs.sort(key=lambda p: (-pair_counts[p], p[0], p[2]))
        chosen_pair = candidate_pairs[0]
        
        clause3_list.append({
            'idx': [idx1, idx2, idx3],
            'pol': [pi1, pi2, pi3],
            'canonical_pair': chosen_pair,
            'lambda': lambda_val
        })
        
    n_clause3 = len(clause3_list)
    adj = {i: [] for i in range(n_clause3)}
    for i in range(n_clause3):
        for j in range(i + 1, n_clause3):
            if clause3_list[i]['canonical_pair'] == clause3_list[j]['canonical_pair']:
                adj[i].append(j)
                adj[j].append(i)
                
    visited = [False] * n_clause3
    components = []
    for i in range(n_clause3):
        if not visited[i]:
            comp = []
            queue = [i]
            visited[i] = True
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)
            components.append(comp)
            
    clause_to_merged_idx = {}
    n_merged_nodes = len(components)
    for comp_idx, comp in enumerate(components):
        merged_node = N_red + 1 + comp_idx
        for clause_idx in comp:
            clause_to_merged_idx[clause_idx] = merged_node
            
    edges = list(direct_edges)
    for c in active_clauses:
        if len(c) == 1:
            lit = c[0]
            v = abs(lit)
            idx = var_to_idx[v]
            pol = 1 if lit > 0 else -1
            edges.append((idx, 0, u, pol))
        elif len(c) == 2:
            v1, v2 = abs(c[0]), abs(c[1])
            idx1, idx2 = var_to_idx[v1], var_to_idx[v2]
            pol1 = 1 if c[0] > 0 else -1
            pol2 = 1 if c[1] > 0 else -1
            edges.append((idx1, 0, u / 2.0, pol1))
            edges.append((idx2, 0, u / 2.0, pol2))
            edges.append((idx1, idx2, u / 2.0, -pol1 * pol2))
            
    for clause3_counter in range(n_clause3):
        info = clause3_list[clause3_counter]
        idx1, idx2, idx3 = info['idx']
        pol1, pol2, pol3 = info['pol']
        s = clause_to_merged_idx[clause3_counter]
        u_eff = info['lambda']
        
        edges.append((idx1, 0, u_eff / 2.0, pol1))
        edges.append((idx2, 0, u_eff / 2.0, pol2))
        edges.append((idx3, 0, u_eff / 2.0, pol3))
        edges.append((s, idx1, u_eff / 2.0, pol1))
        edges.append((s, idx2, u_eff / 2.0, pol2))
        edges.append((s, idx3, u_eff / 2.0, pol3))
        edges.append((s, 0, u_eff / 2.0, -1))
        edges.append((idx1, idx2, u_eff / 2.0, -pol1 * pol2))
        edges.append((idx2, idx3, u_eff / 2.0, -pol2 * pol3))
        edges.append((idx1, idx3, u_eff / 2.0, -pol1 * pol3))
            
    total_nodes = N_red + 1 + n_merged_nodes
    # Initialize A as a sparse dict-of-dicts pre-populated with empty dicts for each node
    A = {i: {} for i in range(total_nodes)}
    for u_node, v_node, weight, sign in edges:
        val = sign * weight
        A[u_node][v_node] = A[u_node].get(v_node, 0.0) + val
        A[v_node][u_node] = A[v_node].get(u_node, 0.0) + val
    return A, var_to_idx, clause3_list, clause_to_merged_idx, total_nodes

def find_triangles(A, total_nodes):
    """
    Finds all unique triangles (i < j < k) in the graph with non-zero edge weights.
    """
    adj_sets = {}
    for u in range(total_nodes):
        adj_sets[u] = {v for v, w in A[u].items() if abs(w) > 1e-9}
        
    triangles = []
    for u in range(total_nodes):
        neighbors_u = adj_sets[u]
        # Only check neighbors v > u
        neighbors_u_gt = [v for v in neighbors_u if v > u]
        for v in neighbors_u_gt:
            common = neighbors_u.intersection(adj_sets[v])
            for w in common:
                if w > v:
                    triangles.append((u, v, w))
    return triangles

def transfer_weights_to_triangles(A, triangles, total_nodes, lambda_T=0.1):
    """
    Formulates and solves the LP weight transfer to maximize triangle weights.
    Applies lambda_T penalty to triangles containing T (node 0).
    Uses sparse matrix for the constraints to prevent memory issues.
    """
    edges_list = []
    edge_to_idx = {}
    for u in range(total_nodes):
        for v in A[u]:
            if v > u and abs(A[u][v]) > 1e-9:
                idx = len(edges_list)
                edges_list.append((u, v))
                edge_to_idx[(u, v)] = idx
                
    Ne = len(edges_list)
    Nt = len(triangles)
    W = np.array([abs(A[u][v]) for u, v in edges_list], dtype=np.float64)
    
    if Nt == 0:
        return np.zeros(0), W, edges_list, edge_to_idx
        
    rows = []
    cols = []
    data = []
    for t_idx, (i, j, k) in enumerate(triangles):
        e1 = (i, j) if (i, j) in edge_to_idx else (j, i)
        e2 = (j, k) if (j, k) in edge_to_idx else (k, j)
        e3 = (i, k) if (i, k) in edge_to_idx else (k, i)
        
        rows.extend([edge_to_idx[e1], edge_to_idx[e2], edge_to_idx[e3]])
        cols.extend([t_idx, t_idx, t_idx])
        data.extend([1.0, 1.0, 1.0])
        
    M_sparse = scipy.sparse.coo_matrix((data, (rows, cols)), shape=(Ne, Nt))
    
    # Minimize -sum alpha_t * omega_t
    c = -np.ones(Nt, dtype=np.float64)
    for t_idx, (i, j, k) in enumerate(triangles):
        if i == 0 or j == 0 or k == 0:
            c[t_idx] = -lambda_T
            
    res = linprog(c, A_ub=M_sparse, b_ub=W, bounds=(0, None), method='highs')
    if res.success:
        omega = res.x
    else:
        omega = np.zeros(Nt, dtype=np.float64)
        
    rho = np.maximum(0.0, W - M_sparse.dot(omega))
    return omega, rho, edges_list, edge_to_idx

def optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx):
    """
    Optimizes each auxiliary spin (or merged certificate) to minimize extended energy.
    """
    aux_to_clauses = {}
    for c_idx, info in enumerate(clause3_list):
        aux_node = clause_to_merged_idx[c_idx]
        if aux_node not in aux_to_clauses:
            aux_to_clauses[aux_node] = []
        aux_to_clauses[aux_node].append(info)
        
    for aux_node, infos in aux_to_clauses.items():
        total_val = 0.0
        for info in infos:
            idx1, idx2, idx3 = info['idx']
            pol1, pol2, pol3 = info['pol']
            
            L1 = pol1 * sigma[idx1]
            L2 = pol2 * sigma[idx2]
            L3 = pol3 * sigma[idx3]
            
            weight = info.get('lambda', 1.0)
            total_val += weight * (1.0 - L1 - L2 - L3)
            
        if total_val >= 0.0:
            sigma[aux_node] = -1.0
        else:
            sigma[aux_node] = 1.0


def find_root(i, parent):
    path = []
    while parent[i] != i:
        path.append(i)
        i = parent[i]
    for node in path:
        parent[node] = i
    return i

def union(i, j, parent):
    root_i = find_root(i, parent)
    root_j = find_root(j, parent)
    if root_i != root_j:
        parent[root_i] = root_j

def build_reduced_problem(clauses, full_sigma, parent, pinned_root, var_to_idx, root_to_idx):
    """
    Reduces the original SAT clauses to constraint clauses over the flippable cluster variables.
    """
    reduced_clauses = []
    for c_idx, c in enumerate(clauses):
        trivially_satisfied = False
        forbidden = {}
        for lit in c:
            var = abs(lit)
            pol = 1 if lit > 0 else -1
            L_0 = pol * full_sigma[var]
            
            if var in var_to_idx:
                c_root = find_root(var_to_idx[var], parent)
            else:
                c_root = pinned_root
                
            if c_root == pinned_root or c_root not in root_to_idx:
                if L_0 == 1:
                    trivially_satisfied = True
                    break
                else:
                    continue
            else:
                forbidden_val = -L_0
                if c_root in forbidden:
                    if forbidden[c_root] != forbidden_val:
                        trivially_satisfied = True
                        break
                else:
                    forbidden[c_root] = forbidden_val
                    
        if not trivially_satisfied:
            reduced_clauses.append({
                'forbidden': forbidden,
                'c_idx': c_idx
            })
            
    return reduced_clauses

def solve_reduced_exhaustive(reduced_clauses, m, root_to_idx):
    """
    Finds the exact optimal flip combination by testing all 2^m configurations.
    """
    best_i = 0
    best_unsat = len(reduced_clauses)
    
    parsed = []
    for rc in reduced_clauses:
        items = []
        for r, val in rc['forbidden'].items():
            var_idx = root_to_idx[r]
            val_bin = 0 if val == 1 else 1
            items.append((var_idx, val_bin))
        parsed.append(items)
        
    for i in range(1 << m):
        unsat = 0
        for items in parsed:
            clause_unsat = True
            for var_idx, val_bin in items:
                bit = (i >> var_idx) & 1
                if bit != val_bin:
                    clause_unsat = False
                    break
            if clause_unsat:
                unsat += 1
                
        if unsat < best_unsat:
            best_unsat = unsat
            best_i = i
            if best_unsat == 0:
                break
                
    best_z = np.array([1 if not (best_i & (1 << j)) else -1 for j in range(m)], dtype=int)
    return best_z

def solve_reduced_walksat(reduced_clauses, m, root_to_idx, max_flips=None, p_noise=0.15):
    """
    WalkSAT on the cluster flip variables, targeting minimal unsatisfied reduced clauses.
    """
    z = np.ones(m, dtype=int)
    parsed = []
    cluster_to_clauses = [[] for _ in range(m)]
    
    for rc_idx, rc in enumerate(reduced_clauses):
        items = [(root_to_idx[r], val) for r, val in rc['forbidden'].items()]
        parsed.append(items)
        for var_idx, _ in items:
            cluster_to_clauses[var_idx].append(rc_idx)
            
    diff_count = np.zeros(len(reduced_clauses), dtype=int)
    unsat_list = []
    clause_to_unsat_idx = np.full(len(reduced_clauses), -1, dtype=int)
    
    for rc_idx, items in enumerate(parsed):
        c = sum(1 for var_idx, val in items if z[var_idx] != val)
        diff_count[rc_idx] = c
        if c == 0:
            clause_to_unsat_idx[rc_idx] = len(unsat_list)
            unsat_list.append(rc_idx)
            
    best_unsat = len(unsat_list)
    best_z = z.copy()
    
    if best_unsat == 0:
        return best_z
        
    if max_flips is None:
        max_flips = max(1500, 15 * best_unsat)
        
    for flip in range(max_flips):
        if not unsat_list:
            break
            
        rc_idx = random.choice(unsat_list)
        items = parsed[rc_idx]
        
        if random.random() < p_noise:
            flip_var = random.choice(items)[0]
        else:
            best_diff = -1e9
            best_vars = []
            for var_idx, _ in items:
                broken = 0
                made = 0
                for incident_rc_idx in cluster_to_clauses[var_idx]:
                    c_curr = diff_count[incident_rc_idx]
                    for v_idx, f_val in parsed[incident_rc_idx]:
                        if v_idx == var_idx:
                            forbidden_val = f_val
                            break
                            
                    if z[var_idx] != forbidden_val:
                        c_new = c_curr - 1
                    else:
                        c_new = c_curr + 1
                        
                    if c_curr == 0 and c_new > 0:
                        made += 1
                    elif c_curr > 0 and c_new == 0:
                        broken += 1
                        
                diff = made - broken
                if diff > best_diff:
                    best_diff = diff
                    best_vars = [var_idx]
                elif diff == best_diff:
                    best_vars.append(var_idx)
                    
            flip_var = random.choice(best_vars)
            
        old_val = z[flip_var]
        new_val = -old_val
        z[flip_var] = new_val
        
        for incident_rc_idx in cluster_to_clauses[flip_var]:
            for v_idx, f_val in parsed[incident_rc_idx]:
                if v_idx == flip_var:
                    forbidden_val = f_val
                    break
            
            c_old = diff_count[incident_rc_idx]
            if old_val != forbidden_val:
                diff_count[incident_rc_idx] -= 1
            else:
                diff_count[incident_rc_idx] += 1
            c_new = diff_count[incident_rc_idx]
            
            if c_old == 0 and c_new > 0:
                idx = clause_to_unsat_idx[incident_rc_idx]
                if idx != -1:
                    last_rc_idx = unsat_list[-1]
                    unsat_list[idx] = last_rc_idx
                    clause_to_unsat_idx[last_rc_idx] = idx
                    unsat_list.pop()
                    clause_to_unsat_idx[incident_rc_idx] = -1
            elif c_old > 0 and c_new == 0:
                if clause_to_unsat_idx[incident_rc_idx] == -1:
                    clause_to_unsat_idx[incident_rc_idx] = len(unsat_list)
                    unsat_list.append(incident_rc_idx)
                    
        curr_unsat = len(unsat_list)
        if curr_unsat < best_unsat:
            best_unsat = curr_unsat
            best_z = z.copy()
            if best_unsat == 0:
                break
                
    return best_z

def get_largest_flippable_cluster_proportion(clusters, pinned_root, N_red):
    max_size = 0
    for root, nodes in clusters.items():
        if root == pinned_root:
            continue
        orig_nodes = sum(1 for n in nodes if 1 <= n <= N_red)
        if orig_nodes > max_size:
            max_size = orig_nodes
    return max_size / N_red if N_red > 0 else 0.0

def get_pinned_cluster_proportion(clusters, pinned_root, N_red):
    if pinned_root not in clusters:
        return 0.0
    orig_nodes = sum(1 for n in clusters[pinned_root] if 1 <= n <= N_red)
    return orig_nodes / N_red if N_red > 0 else 0.0

def update_beta(beta, observed_sizes, observed_S_T=None, target=0.10, gamma=0.5):
    if observed_S_T is not None and len(observed_S_T) > 0:
        median_S_T = np.median(observed_S_T)
        if median_S_T > 0.70:
            # Force melting by decreasing beta
            new_log_beta = np.log(beta) - gamma * 0.3
            return np.clip(np.exp(new_log_beta), 0.01, 10.0)
            
    if not observed_sizes:
        return beta
    s_obs = np.median(observed_sizes)
    new_log_beta = np.log(beta) + gamma * (target - s_obs)
    return np.clip(np.exp(new_log_beta), 0.01, 10.0)


def extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars):
    """
    Reconstructs the full 3-SAT assignment including simplified variables.
    """
    spins = {}
    for v in range(1, num_vars + 1):
        if v in var_to_idx:
            idx = var_to_idx[v]
            spins[v] = int(sigma[idx])
        elif v in fixed_literals:
            spins[v] = int(fixed_literals[v])
        else:
            spins[v] = 1
    return spins

def count_unsat_clauses(spins, clauses):
    """
    Evaluates the number of unsatisfied clauses for a given spin assignment.
    """
    unsat_count = 0
    for c in clauses:
        sat = False
        for lit in c:
            var = abs(lit)
            val = 1 if lit > 0 else -1
            if spins[var] == val:
                sat = True
                break
        if not sat:
            unsat_count += 1
    return unsat_count

def perform_gel_and_get_clusters_torch(beta, sigma_torch, device_obj, Ne, Nt_active, edges_src, edges_dst, epsilon_edges_torch, rho_torch, t_eps1, t_eps2, t_eps3, t_e1_src, t_e1_dst, t_e2_src, t_e2_dst, t_e3_src, t_e3_dst, t_omega, t_pt, total_nodes, N_red, beta_T_factor=0.1):
    frozen_edges_src = []
    frozen_edges_dst = []
    n_frozen_residuals = 0
    n_frozen_triangles = 0
    
    # 1. Gel of residual edges
    if Ne > 0:
        y = epsilon_edges_torch * sigma_torch[edges_src] * sigma_torch[edges_dst]
        is_T_edge = (edges_src == 0) | (edges_dst == 0)
        beta_eff = torch.where(is_T_edge, beta * beta_T_factor, beta)
        probs = 1.0 - torch.exp(-beta_eff * rho_torch)
        freeze_mask = (y == 1.0) & (torch.rand(Ne, device=device_obj) < probs)
        
        frozen_edges_src.append(edges_src[freeze_mask])
        frozen_edges_dst.append(edges_dst[freeze_mask])
        n_frozen_residuals = int(torch.sum(freeze_mask).item())
        
    # 2. Gel of triangles
    if Nt_active > 0:
        y1 = t_eps1 * sigma_torch[t_e1_src] * sigma_torch[t_e1_dst]
        y2 = t_eps2 * sigma_torch[t_e2_src] * sigma_torch[t_e2_dst]
        y3 = t_eps3 * sigma_torch[t_e3_src] * sigma_torch[t_e3_dst]
        
        is_T_triangle = (t_e1_src == 0)
        t_beta_eff = torch.where(is_T_triangle, beta * beta_T_factor, beta)
        
        # Non-frustrated
        satisfied_nf = (t_pt == 1.0) & (y1 == 1.0) & (y2 == 1.0) & (y3 == 1.0) & (t_omega >= 1e-9)
        probs_nf = 1.0 - torch.exp(-2.0 * t_beta_eff * t_omega)
        freeze_nf = satisfied_nf & (torch.rand(Nt_active, device=device_obj) < probs_nf)
        
        frozen_edges_src.extend([t_e1_src[freeze_nf], t_e2_src[freeze_nf], t_e3_src[freeze_nf]])
        frozen_edges_dst.extend([t_e1_dst[freeze_nf], t_e2_dst[freeze_nf], t_e3_dst[freeze_nf]])
        n_frozen_triangles += int(torch.sum(freeze_nf).item()) * 3
        
        # Frustrated
        sat_count = (y1 == 1.0).float() + (y2 == 1.0).float() + (y3 == 1.0).float()
        state_bas = (t_pt == -1.0) & (sat_count == 2.0) & (t_omega >= 1e-9)
        probs_f = 1.0 - torch.exp(-2.0 * t_beta_eff * t_omega)
        freeze_f = state_bas & (torch.rand(Nt_active, device=device_obj) < probs_f)
        
        r = torch.rand(Nt_active, device=device_obj)
        
        # Case A
        mask_A = freeze_f & (y1 == 1.0) & (y2 == 1.0)
        src_A = torch.where(r < 0.5, t_e1_src, t_e2_src)
        dst_A = torch.where(r < 0.5, t_e1_dst, t_e2_dst)
        frozen_edges_src.append(src_A[mask_A])
        frozen_edges_dst.append(dst_A[mask_A])
        n_frozen_triangles += int(torch.sum(mask_A).item())
        
        # Case B
        mask_B = freeze_f & (y2 == 1.0) & (y3 == 1.0)
        src_B = torch.where(r < 0.5, t_e2_src, t_e3_src)
        dst_B = torch.where(r < 0.5, t_e2_dst, t_e3_dst)
        frozen_edges_src.append(src_B[mask_B])
        frozen_edges_dst.append(dst_B[mask_B])
        n_frozen_triangles += int(torch.sum(mask_B).item())
        
        # Case C
        mask_C = freeze_f & (y1 == 1.0) & (y3 == 1.0)
        src_C = torch.where(r < 0.5, t_e1_src, t_e3_src)
        dst_C = torch.where(r < 0.5, t_e1_dst, t_e3_dst)
        frozen_edges_src.append(src_C[mask_C])
        frozen_edges_dst.append(dst_C[mask_C])
        n_frozen_triangles += int(torch.sum(mask_C).item())
        
    if frozen_edges_src:
        src_all = torch.cat(frozen_edges_src)
        dst_all = torch.cat(frozen_edges_dst)
        n_frozen_total = src_all.numel()
    else:
        src_all = torch.zeros(0, dtype=torch.long, device=device_obj)
        dst_all = torch.zeros(0, dtype=torch.long, device=device_obj)
        n_frozen_total = 0
        
    # 3. Construct clusters (Label Propagation in PyTorch)
    parent_arr = np.arange(total_nodes)
    if src_all.numel() > 0:
        sym_src = torch.cat([src_all, dst_all])
        sym_dst = torch.cat([dst_all, src_all])
        
        labels = torch.arange(total_nodes, device=device_obj)
        for _ in range(100):
            labels_next = torch.scatter_reduce(labels, 0, sym_dst, labels[sym_src], reduce='amax', include_self=True)
            if torch.equal(labels, labels_next):
                break
            labels = labels_next
        parent_arr = labels.cpu().numpy()
        
    clusters = {}
    for i in range(total_nodes):
        root = find_root(i, parent_arr)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(i)
        
    pinned_root = find_root(0, parent_arr)
    largest_q = get_largest_flippable_cluster_proportion(clusters, pinned_root, N_red)
    pinned_orig = sum(1 for n in clusters.get(pinned_root, []) if 1 <= n <= N_red)
    S_T = pinned_orig / N_red if N_red > 0 else 0.0
    return clusters, parent_arr, pinned_root, n_frozen_total, n_frozen_residuals, n_frozen_triangles, largest_q, S_T


def perform_gel_and_get_clusters_numpy(beta, sigma, total_nodes, N_red, edges_list, epsilon_edges, rho, precomputed_triangles, omega, beta_T_factor=0.1):
    frozen_edges = []
    n_frozen_residuals = 0
    n_frozen_triangles = 0
    
    # 1. Gel of residual edges
    for idx, (u, v) in enumerate(edges_list):
        if epsilon_edges[idx] * sigma[u] * sigma[v] == 1.0:
            beta_eff = beta * beta_T_factor if (u == 0 or v == 0) else beta
            p_gel = 1.0 - np.exp(-beta_eff * rho[idx])
            if random.random() < p_gel:
                frozen_edges.append((u, v))
                n_frozen_residuals += 1
                
    # 2. Gel of triangles
    for t_idx, (e1, e2, e3, eps1, eps2, eps3, p_t) in enumerate(precomputed_triangles):
        omega_t = omega[t_idx]
        if omega_t < 1e-9:
            continue
            
        y1 = eps1 * sigma[e1[0]] * sigma[e1[1]]
        y2 = eps2 * sigma[e2[0]] * sigma[e2[1]]
        y3 = eps3 * sigma[e3[0]] * sigma[e3[1]]
        
        is_T_tri = (e1[0] == 0)
        beta_eff = beta * beta_T_factor if is_T_tri else beta
        
        if p_t == 1.0: # Non-frustrated
            if y1 == 1.0 and y2 == 1.0 and y3 == 1.0:
                p_gel = 1.0 - np.exp(-2.0 * beta_eff * omega_t)
                if random.random() < p_gel:
                    frozen_edges.extend([e1, e2, e3])
                    n_frozen_triangles += 3
        else: # Frustrated
            satisfied_edges = []
            if y1 == 1.0: satisfied_edges.append(e1)
            if y2 == 1.0: satisfied_edges.append(e2)
            if y3 == 1.0: satisfied_edges.append(e3)
            
            if len(satisfied_edges) == 2:
                p_gel = 1.0 - np.exp(-2.0 * beta_eff * omega_t)
                if random.random() < p_gel:
                    e_freeze = random.choice(satisfied_edges)
                    frozen_edges.append(e_freeze)
                    n_frozen_triangles += 1
                    
    # 3. Construct clusters (Union-Find)
    parent = {i: i for i in range(total_nodes)}
    
    for u, v in frozen_edges:
        union(u, v, parent)
        
    clusters = {}
    for i in range(total_nodes):
        root = find_root(i, parent)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(i)
        
    pinned_root = find_root(0, parent)
    largest_q = get_largest_flippable_cluster_proportion(clusters, pinned_root, N_red)
    pinned_orig = sum(1 for n in clusters.get(pinned_root, []) if 1 <= n <= N_red)
    S_T = pinned_orig / N_red if N_red > 0 else 0.0
    return clusters, parent, pinned_root, len(frozen_edges), n_frozen_residuals, n_frozen_triangles, largest_q, S_T


def solve_3sat_mcmc_higher_order(num_vars, clauses, max_sweeps=300, u_sat=1.0, beta_init=0.5, target_q=0.10, exact_threshold=10, beta_T_factor=0.1, lambda_T=0.1, verbose=False, device='auto'):
    """
    The full MCMC Higher-Order solver.
    Supports a device-agnostic PyTorch backend ('cuda', 'cpu') for GPU acceleration,
    and a native NumPy CPU backend ('numpy').
    """
    t_start = time.time()
    
    if device == 'auto':
        if HAS_TORCH:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            device = 'numpy'
            
    if device != 'numpy' and not HAS_TORCH:
        if verbose:
            print("Warning: PyTorch is not installed. Falling back to NumPy CPU backend.")
        device = 'numpy'
        
    # 1. Preprocessing
    if verbose:
        print("\n=== MCMC Higher-Order Solver Preprocessing ===")
        print(f"Input formula: {num_vars} variables, {len(clauses)} clauses")
        
    cleaned_clauses = normalize_and_clean_clauses(clauses)
    
    active_vars, active_clauses, fixed_literals, fixed_empty_clauses = \
        recursive_unit_propagation_and_reductions(num_vars, cleaned_clauses, verbose=verbose)
        
    active_clauses = normalize_and_clean_clauses(active_clauses)
    
    if verbose:
        print(f"After reductions: {len(active_vars)} active variables, {len(active_clauses)} active clauses")
        print(f"Fixed literals: {len(fixed_literals)} | Fixed empty clauses: {fixed_empty_clauses}")
        
    if len(active_vars) == 0:
        spins = {v: fixed_literals.get(v, 1) for v in range(1, num_vars + 1)}
        if verbose:
            print("Formula solved in preprocessing.")
        return spins, time.time() - t_start, fixed_empty_clauses
        
    # 2. Extended Graph construction
    if verbose:
        print("Constructing extended signed graph...")
    A, var_to_idx, clause3_list, clause_to_merged_idx, total_nodes = \
        build_signed_graph_for_3sat(num_vars, active_vars, active_clauses, u=u_sat, verbose=verbose)
    N_red = len(active_vars)
    
    # 3. Triangles and LP Transfer
    if verbose:
        print("Finding triangles and running LP weight transfer...")
    triangles = find_triangles(A, total_nodes)
    omega, rho, edges_list, edge_to_idx = transfer_weights_to_triangles(A, triangles, total_nodes, lambda_T=lambda_T)
    
    if verbose:
        nf_count = 0
        f_count = 0
        nf_omega = 0.0
        f_omega = 0.0
        for t_idx, (u, v, w) in enumerate(triangles):
            e1 = (u, v) if (u, v) in edge_to_idx else (v, u)
            e2 = (v, w) if (v, w) in edge_to_idx else (w, v)
            e3 = (u, w) if (u, w) in edge_to_idx else (w, u)
            eps1 = np.sign(A[e1[0]][e1[1]])
            eps2 = np.sign(A[e2[0]][e2[1]])
            eps3 = np.sign(A[e3[0]][e3[1]])
            p_t = eps1 * eps2 * eps3
            if p_t == 1.0:
                nf_count += 1
                nf_omega += omega[t_idx]
            else:
                f_count += 1
                f_omega += omega[t_idx]
                
        total_init_mass = np.sum(np.array([abs(A[u_n][v_n]) for u_n, v_n in edges_list])) if len(edges_list) > 0 else 0.0
        total_transferred = 3.0 * np.sum(omega)
        total_residual = np.sum(rho)
        pct_transferred = (total_transferred / total_init_mass * 100) if total_init_mass > 1e-9 else 0.0
        pct_residual = (total_residual / total_init_mass * 100) if total_init_mass > 1e-9 else 0.0
        
        print(f"Found {len(triangles)} triangles in the extended signed graph.")
        print(f"  - Non-frustrated (NF) triangles: {nf_count} | Transferred weight sum: {nf_omega:.4f} (actual edge energy = {3*nf_omega:.4f})")
        print(f"  - Frustrated (F) triangles: {f_count} | Transferred weight sum: {f_omega:.4f} (actual edge energy = {3*f_omega:.4f})")
        print(f"  - Total initial edge mass: {total_init_mass:.4f}")
        print(f"  - Total energy transferred to triangles: {total_transferred:.4f} ({pct_transferred:.2f}%)")
        print(f"  - Total residual edge energy: {total_residual:.4f} ({pct_residual:.2f}%)")
        print(f"LP Transfer: mass on triangles = {np.sum(omega):.4f} | residual edge mass = {np.sum(rho):.4f}")
        
    # Precompute edge signs and triangle properties to avoid overhead in the sweep loop
    epsilon_edges = np.array([np.sign(A[u][v]) for u, v in edges_list])
    precomputed_triangles = []
    for t_idx, (u, v, w) in enumerate(triangles):
        e1 = (u, v) if (u, v) in edge_to_idx else (v, u)
        e2 = (v, w) if (v, w) in edge_to_idx else (w, v)
        e3 = (u, w) if (u, w) in edge_to_idx else (w, u)
        
        eps1 = np.sign(A[e1[0]][e1[1]])
        eps2 = np.sign(A[e2[0]][e2[1]])
        eps3 = np.sign(A[e3[0]][e3[1]])
        p_t = eps1 * eps2 * eps3
        precomputed_triangles.append((e1, e2, e3, eps1, eps2, eps3, p_t))
        
    # BACKEND: PyTorch (CPU or GPU/CUDA)
    if device != 'numpy':
        device_obj = torch.device(device)
        if verbose:
            print(f"Running MCMC sweeps on PyTorch device: {device_obj}")
            
        Ne = len(edges_list)
        Nt_active = len(precomputed_triangles)
        
        # Move precomputations to PyTorch
        edges_src_np = np.array([e[0] for e in edges_list], dtype=np.int64) if Ne > 0 else np.zeros(0, dtype=np.int64)
        edges_dst_np = np.array([e[1] for e in edges_list], dtype=np.int64) if Ne > 0 else np.zeros(0, dtype=np.int64)
        
        edges_src = torch.tensor(edges_src_np, dtype=torch.long, device=device_obj)
        edges_dst = torch.tensor(edges_dst_np, dtype=torch.long, device=device_obj)
        epsilon_edges_torch = torch.tensor(epsilon_edges, dtype=torch.float32, device=device_obj)
        rho_torch = torch.tensor(rho, dtype=torch.float32, device=device_obj)
        
        t_e1_src_list, t_e1_dst_list = [], []
        t_e2_src_list, t_e2_dst_list = [], []
        t_e3_src_list, t_e3_dst_list = [], []
        t_eps1_list, t_eps2_list, t_eps3_list = [], [], []
        t_omega_list = []
        t_pt_list = []
        
        for t_idx, (e1, e2, e3, eps1, eps2, eps3, p_t) in enumerate(precomputed_triangles):
            t_e1_src_list.append(e1[0])
            t_e1_dst_list.append(e1[1])
            t_e2_src_list.append(e2[0])
            t_e2_dst_list.append(e2[1])
            t_e3_src_list.append(e3[0])
            t_e3_dst_list.append(e3[1])
            t_eps1_list.append(eps1)
            t_eps2_list.append(eps2)
            t_eps3_list.append(eps3)
            t_omega_list.append(omega[t_idx])
            t_pt_list.append(p_t)
            
        if Nt_active > 0:
            t_e1_src = torch.tensor(t_e1_src_list, dtype=torch.long, device=device_obj)
            t_e1_dst = torch.tensor(t_e1_dst_list, dtype=torch.long, device=device_obj)
            t_e2_src = torch.tensor(t_e2_src_list, dtype=torch.long, device=device_obj)
            t_e2_dst = torch.tensor(t_e2_dst_list, dtype=torch.long, device=device_obj)
            t_e3_src = torch.tensor(t_e3_src_list, dtype=torch.long, device=device_obj)
            t_e3_dst = torch.tensor(t_e3_dst_list, dtype=torch.long, device=device_obj)
            
            t_eps1 = torch.tensor(t_eps1_list, dtype=torch.float32, device=device_obj)
            t_eps2 = torch.tensor(t_eps2_list, dtype=torch.float32, device=device_obj)
            t_eps3 = torch.tensor(t_eps3_list, dtype=torch.float32, device=device_obj)
            t_omega = torch.tensor(t_omega_list, dtype=torch.float32, device=device_obj)
            t_pt = torch.tensor(t_pt_list, dtype=torch.float32, device=device_obj)
        else:
            t_e1_src = torch.zeros(0, dtype=torch.long, device=device_obj)
            t_e1_dst = torch.zeros(0, dtype=torch.long, device=device_obj)
            t_e2_src = torch.zeros(0, dtype=torch.long, device=device_obj)
            t_e2_dst = torch.zeros(0, dtype=torch.long, device=device_obj)
            t_e3_src = torch.zeros(0, dtype=torch.long, device=device_obj)
            t_e3_dst = torch.zeros(0, dtype=torch.long, device=device_obj)
            t_eps1 = torch.zeros(0, dtype=torch.float32, device=device_obj)
            t_eps2 = torch.zeros(0, dtype=torch.float32, device=device_obj)
            t_eps3 = torch.zeros(0, dtype=torch.float32, device=device_obj)
            t_omega = torch.zeros(0, dtype=torch.float32, device=device_obj)
            t_pt = torch.zeros(0, dtype=torch.float32, device=device_obj)
            
        # Initialize spins
        sigma_torch = torch.ones(total_nodes, dtype=torch.float32, device=device_obj)
        sigma_torch[1:N_red + 1] = (torch.rand(N_red, device=device_obj) > 0.5).float() * 2.0 - 1.0
        sigma_torch[0] = 1.0
        
        # Optimize auxiliaries initially on CPU
        sigma = sigma_torch.cpu().numpy()
        optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
        sigma_torch = torch.tensor(sigma, dtype=torch.float32, device=device_obj)
        
        best_spins = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
        best_unsat = count_unsat_clauses(best_spins, clauses)
        
        if best_unsat == 0:
            return best_spins, time.time() - t_start, 0
            
        # Stochastic bisection to calibrate initial beta
        if verbose:
            print(f"Calibrating initial beta via stochastic bisection to target q = {target_q}...")
        beta_min = 0.01
        beta_max = 5.0
        for bisection_step in range(6):
            beta_mid = (beta_min + beta_max) / 2.0
            samples_q = []
            samples_S_T = []
            for _ in range(5):
                _, _, _, _, _, _, q_val, S_T_val = perform_gel_and_get_clusters_torch(
                    beta_mid, sigma_torch, device_obj, Ne, Nt_active, edges_src, edges_dst,
                    epsilon_edges_torch, rho_torch, t_eps1, t_eps2, t_eps3,
                    t_e1_src, t_e1_dst, t_e2_src, t_e2_dst, t_e3_src, t_e3_dst,
                    t_omega, t_pt, total_nodes, N_red, beta_T_factor=beta_T_factor
                )
                samples_q.append(q_val)
                samples_S_T.append(S_T_val)
            median_q = np.median(samples_q)
            median_S_T = np.median(samples_S_T)
            if verbose:
                print(f"  Bisection step {bisection_step + 1}: beta = {beta_mid:.4f} => median S_max = {median_q:.4f} | median S_T = {median_S_T:.4f}")
            if median_S_T > 0.70:
                beta_max = beta_mid
            else:
                if median_q < target_q:
                    beta_min = beta_mid
                else:
                    beta_max = beta_mid
        beta_init = (beta_min + beta_max) / 2.0
        beta = beta_init
        if verbose:
            print(f"Initial beta calibrated to: {beta:.4f}")
            
        observed_sizes = []
        observed_S_T = []
        
        if verbose:
            print("\n=== Starting MCMC Sweeps (PyTorch Backend) ===")
            
        for sweep in range(1, max_sweeps + 1):
            clusters, parent_arr, pinned_root, n_frozen_total, n_frozen_residuals, n_frozen_triangles, largest_q, S_T = \
                perform_gel_and_get_clusters_torch(
                    beta, sigma_torch, device_obj, Ne, Nt_active, edges_src, edges_dst,
                    epsilon_edges_torch, rho_torch, t_eps1, t_eps2, t_eps3,
                    t_e1_src, t_e1_dst, t_e2_src, t_e2_dst, t_e3_src, t_e3_dst,
                    t_omega, t_pt, total_nodes, N_red, beta_T_factor=beta_T_factor
                )
            observed_sizes.append(largest_q)
            observed_S_T.append(S_T)
            
            if sweep % 15 == 0:
                beta = update_beta(beta, observed_sizes, observed_S_T=observed_S_T, target=target_q)
                observed_sizes = []
                observed_S_T = []
                
            # 4. Build reduced MaxSAT problem on cluster flips
            sigma = sigma_torch.cpu().numpy()
            full_sigma = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
            
            flippable_roots = []
            for r, nodes in clusters.items():
                if r == pinned_root:
                    continue
                if any(1 <= n <= N_red for n in nodes):
                    flippable_roots.append(r)
            m = len(flippable_roots)
            
            if m == 0:
                if verbose:
                    print(f"Sweep {sweep:3d}/{max_sweeps} | Beta: {beta:.3f} | All variables pinned.")
                continue
                
            root_to_idx = {r: i for i, r in enumerate(flippable_roots)}
            
            reduced_clauses = build_reduced_problem(clauses, full_sigma, parent_arr, pinned_root, var_to_idx, root_to_idx)
            reduced_clauses = [rc for rc in reduced_clauses if len(rc['forbidden']) > 0]
            
            # 5. Solve reduced problem
            solver_type = 'Exhaustive'
            if m <= exact_threshold:
                z_best = solve_reduced_exhaustive(reduced_clauses, m, root_to_idx)
            else:
                solver_type = 'WalkSAT'
                z_best = solve_reduced_walksat(reduced_clauses, m, root_to_idx)
                
            # 6. Apply flips
            for idx in range(1, total_nodes):
                r = find_root(idx, parent_arr)
                if r == pinned_root or r not in root_to_idx:
                    z_val = 1
                else:
                    z_val = z_best[root_to_idx[r]]
                sigma[idx] = z_val * sigma[idx]
                
            sigma[0] = 1.0 # Ensure T remains +1
            optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
            sigma_torch = torch.tensor(sigma, dtype=torch.float32, device=device_obj)
            
            # 7. Evaluate SAT score
            curr_spins = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
            curr_unsat = count_unsat_clauses(curr_spins, clauses)
            
            pinned_size = len(clusters.get(pinned_root, []))
            largest_flippable_size = int(largest_q * N_red)
            
            if verbose:
                print(f"Sweep {sweep:3d}/{max_sweeps} | Beta: {beta:.3f} | Frozen edges: {n_frozen_total:4d} (res: {n_frozen_residuals:3d}, tri: {n_frozen_triangles:3d}) | "
                      f"Clusters: {len(clusters):3d} | Pinned K_T: {pinned_size:3d} | Max Flip: {largest_flippable_size:3d} ({largest_q*100.0:.1f}%) | "
                      f"Flippable m: {m:3d} ({solver_type}) | UNSAT: {curr_unsat:3d} (best: {best_unsat:3d})")
                      
            if curr_unsat < best_unsat:
                best_unsat = curr_unsat
                best_spins = curr_spins
                if verbose:
                    print(f"  *** [NEW RECORD] Sweep {sweep}: Best UNSAT count is now {best_unsat} ***")
                if best_unsat == 0:
                    break
                    
            # 8. Periodic restarts if stymied
            if sweep % 80 == 0 and best_unsat > 0:
                if verbose:
                    print(f"  *** [RESTART] Stagnation detected. Perturbing 30% of original spins. ***")
                mask = np.random.random(N_red) < 0.3
                sigma[1:N_red + 1][mask] = np.random.choice([-1.0, 1.0], size=np.sum(mask))
                optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
                sigma_torch = torch.tensor(sigma, dtype=torch.float32, device=device_obj)
                
        t_elapsed = time.time() - t_start
        if verbose:
            print(f"=== Solver finished in {t_elapsed:.4f}s. Best UNSAT: {best_unsat} ===")
        return best_spins, t_elapsed, best_unsat

    # BACKEND: NumPy (Native CPU)
    else:
        if verbose:
            print("Running MCMC sweeps on NumPy CPU backend")
            
        # 4. Initialize spins
        sigma = np.ones(total_nodes, dtype=float)
        sigma[1:N_red + 1] = np.random.choice([-1.0, 1.0], size=N_red)
        sigma[0] = 1.0
        optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
        
        best_spins = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
        best_unsat = count_unsat_clauses(best_spins, clauses)
        
        if best_unsat == 0:
            return best_spins, time.time() - t_start, 0
            
        # Stochastic bisection to calibrate initial beta
        if verbose:
            print(f"Calibrating initial beta via stochastic bisection to target q = {target_q}...")
        beta_min = 0.01
        beta_max = 5.0
        for bisection_step in range(6):
            beta_mid = (beta_min + beta_max) / 2.0
            samples_q = []
            samples_S_T = []
            for _ in range(5):
                _, _, _, _, _, _, q_val, S_T_val = perform_gel_and_get_clusters_numpy(
                    beta_mid, sigma, total_nodes, N_red, edges_list, epsilon_edges, rho,
                    precomputed_triangles, omega, beta_T_factor=beta_T_factor
                )
                samples_q.append(q_val)
                samples_S_T.append(S_T_val)
            median_q = np.median(samples_q)
            median_S_T = np.median(samples_S_T)
            if verbose:
                print(f"  Bisection step {bisection_step + 1}: beta = {beta_mid:.4f} => median S_max = {median_q:.4f} | median S_T = {median_S_T:.4f}")
            if median_S_T > 0.70:
                beta_max = beta_mid
            else:
                if median_q < target_q:
                    beta_min = beta_mid
                else:
                    beta_max = beta_mid
        beta_init = (beta_min + beta_max) / 2.0
        beta = beta_init
        if verbose:
            print(f"Initial beta calibrated to: {beta:.4f}")
            
        observed_sizes = []
        observed_S_T = []
        
        if verbose:
            print("\n=== Starting MCMC Sweeps (NumPy CPU Backend) ===")
            
        for sweep in range(1, max_sweeps + 1):
            clusters, parent, pinned_root, n_frozen_total, n_frozen_residuals, n_frozen_triangles, largest_q, S_T = \
                perform_gel_and_get_clusters_numpy(
                    beta, sigma, total_nodes, N_red, edges_list, epsilon_edges, rho,
                    precomputed_triangles, omega, beta_T_factor=beta_T_factor
                )
            observed_sizes.append(largest_q)
            observed_S_T.append(S_T)
            
            if sweep % 15 == 0:
                beta = update_beta(beta, observed_sizes, observed_S_T=observed_S_T, target=target_q)
                observed_sizes = []
                observed_S_T = []
                
            # 4. Build reduced MaxSAT problem on cluster flips
            full_sigma = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
            
            flippable_roots = []
            for r, nodes in clusters.items():
                if r == pinned_root:
                    continue
                if any(1 <= n <= N_red for n in nodes):
                    flippable_roots.append(r)
            m = len(flippable_roots)
            
            if m == 0:
                if verbose:
                    print(f"Sweep {sweep:3d}/{max_sweeps} | Beta: {beta:.3f} | All variables pinned.")
                continue
                
            root_to_idx = {r: i for i, r in enumerate(flippable_roots)}
            
            reduced_clauses = build_reduced_problem(clauses, full_sigma, parent, pinned_root, var_to_idx, root_to_idx)
            reduced_clauses = [rc for rc in reduced_clauses if len(rc['forbidden']) > 0]
            
            # 5. Solve reduced problem
            solver_type = 'Exhaustive'
            if m <= exact_threshold:
                z_best = solve_reduced_exhaustive(reduced_clauses, m, root_to_idx)
            else:
                solver_type = 'WalkSAT'
                z_best = solve_reduced_walksat(reduced_clauses, m, root_to_idx)
                
            # 6. Apply flips
            for idx in range(1, total_nodes):
                r = find_root(idx, parent)
                if r == pinned_root or r not in root_to_idx:
                    z_val = 1
                else:
                    z_val = z_best[root_to_idx[r]]
                sigma[idx] = z_val * sigma[idx]
                
            sigma[0] = 1.0 # Ensure T remains +1
            optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
            
            # 7. Evaluate SAT score
            curr_spins = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
            curr_unsat = count_unsat_clauses(curr_spins, clauses)
            
            pinned_size = len(clusters.get(pinned_root, []))
            largest_flippable_size = int(largest_q * N_red)
            
            if verbose:
                print(f"Sweep {sweep:3d}/{max_sweeps} | Beta: {beta:.3f} | Frozen edges: {n_frozen_total:4d} (res: {n_frozen_residuals:3d}, tri: {n_frozen_triangles:3d}) | "
                      f"Clusters: {len(clusters):3d} | Pinned K_T: {pinned_size:3d} | Max Flip: {largest_flippable_size:3d} ({largest_q*100.0:.1f}%) | "
                      f"Flippable m: {m:3d} ({solver_type}) | UNSAT: {curr_unsat:3d} (best: {best_unsat:3d})")
                      
            if curr_unsat < best_unsat:
                best_unsat = curr_unsat
                best_spins = curr_spins
                if verbose:
                    print(f"  *** [NEW RECORD] Sweep {sweep}: Best UNSAT count is now {best_unsat} ***")
                if best_unsat == 0:
                    break
                    
            # 8. Periodic restarts if stymied
            if sweep % 80 == 0 and best_unsat > 0:
                if verbose:
                    print(f"  *** [RESTART] Stagnation detected. Perturbing 30% of original spins. ***")
                mask = np.random.random(N_red) < 0.3
                sigma[1:N_red + 1][mask] = np.random.choice([-1.0, 1.0], size=np.sum(mask))
                optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
                
        t_elapsed = time.time() - t_start
        if verbose:
            print(f"=== Solver finished in {t_elapsed:.4f}s. Best UNSAT: {best_unsat} ===")
        return best_spins, t_elapsed, best_unsat
