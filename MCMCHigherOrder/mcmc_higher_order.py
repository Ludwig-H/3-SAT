import time
import random
import numpy as np
import scipy.sparse
import scipy.sparse.linalg
from scipy.optimize import linprog

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

def build_signed_graph_for_3sat(num_vars, active_vars, active_clauses, u=1.0, verbose=False):
    """
    Builds the extended signed graph. Merges auxiliary nodes sharing the same canonical pair.
    """
    var_list = sorted(list(active_vars))
    var_to_idx = {v: i + 1 for i, v in enumerate(var_list)}
    N_red = len(var_list)
    
    clause3_list = []
    for c in active_clauses:
        if len(c) == 3:
            v1, v2, v3 = abs(c[0]), abs(c[1]), abs(c[2])
            idx1, idx2, idx3 = var_to_idx[v1], var_to_idx[v2], var_to_idx[v3]
            pol1 = 1 if c[0] > 0 else -1
            pol2 = 1 if c[1] > 0 else -1
            pol3 = 1 if c[2] > 0 else -1
            
            lits = [(idx1, pol1), (idx2, pol2), (idx3, pol3)]
            lits.sort(key=lambda x: x[0])
            canonical_pair = (lits[0][0], lits[0][1], lits[1][0], lits[1][1])
            
            clause3_list.append({
                'idx': [idx1, idx2, idx3],
                'pol': [pol1, pol2, pol3],
                'canonical_pair': canonical_pair
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
            
    edges = []
    clause3_counter = 0
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
        elif len(c) == 3:
            info = clause3_list[clause3_counter]
            idx1, idx2, idx3 = info['idx']
            pol1, pol2, pol3 = info['pol']
            s = clause_to_merged_idx[clause3_counter]
            
            edges.append((idx1, 0, u / 2.0, pol1))
            edges.append((idx2, 0, u / 2.0, pol2))
            edges.append((idx3, 0, u / 2.0, pol3))
            edges.append((s, idx1, u / 2.0, pol1))
            edges.append((s, idx2, u / 2.0, pol2))
            edges.append((s, idx3, u / 2.0, pol3))
            edges.append((s, 0, u / 2.0, -1))
            edges.append((idx1, idx2, u / 2.0, -pol1 * pol2))
            edges.append((idx2, idx3, u / 2.0, -pol2 * pol3))
            edges.append((idx1, idx3, u / 2.0, -pol1 * pol3))
            clause3_counter += 1
            
    total_nodes = N_red + 1 + n_merged_nodes
    A = np.zeros((total_nodes, total_nodes), dtype=np.float32)
    for u_node, v_node, weight, sign in edges:
        val = sign * weight
        A[u_node, v_node] += val
        A[v_node, u_node] += val
    return A, var_to_idx, clause3_list, clause_to_merged_idx

def find_triangles(A):
    """
    Finds all unique triangles (i < j < k) in the graph with non-zero edge weights.
    """
    N = A.shape[0]
    adj_sets = [set(np.where(A[r] != 0)[0]) for r in range(N)]
    triangles = []
    for u in range(N):
        neighbors_u = np.where(A[u] != 0)[0]
        neighbors_u = neighbors_u[neighbors_u > u]
        for v in neighbors_u:
            common = adj_sets[u].intersection(adj_sets[v])
            for w in common:
                if w > v:
                    triangles.append((u, v, w))
    return triangles

def transfer_weights_to_triangles(A, triangles):
    """
    Formulates and solves the LP weight transfer to maximize triangle weights.
    Uses sparse matrix for the constraints to prevent memory issues.
    """
    N = A.shape[0]
    edges_list = []
    edge_to_idx = {}
    for u in range(N):
        for v in range(u + 1, N):
            if A[u, v] != 0:
                idx = len(edges_list)
                edges_list.append((u, v))
                edge_to_idx[(u, v)] = idx
                
    Ne = len(edges_list)
    Nt = len(triangles)
    W = np.array([abs(A[u, v]) for u, v in edges_list], dtype=np.float64)
    
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
    
    c = -np.ones(Nt, dtype=np.float64)
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
            
            total_val += (1.0 - L1 - L2 - L3)
            
        if total_val >= 0.0:
            sigma[aux_node] = -1.0
        else:
            sigma[aux_node] = 1.0

def build_reduced_problem(clauses, full_sigma, parent, pinned_root, var_to_idx):
    """
    Reduces the original SAT clauses to constraint clauses over the flippable cluster variables.
    """
    def find_root(i):
        path = []
        while parent[i] != i:
            path.append(i)
            i = parent[i]
        for node in path:
            parent[node] = i
        return i

    reduced_clauses = []
    for c_idx, c in enumerate(clauses):
        trivially_satisfied = False
        forbidden = {}
        for lit in c:
            var = abs(lit)
            pol = 1 if lit > 0 else -1
            L_0 = pol * full_sigma[var]
            
            if var in var_to_idx:
                c_root = find_root(var_to_idx[var])
            else:
                c_root = pinned_root
                
            if c_root == pinned_root:
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

def solve_reduced_walksat(reduced_clauses, m, root_to_idx, max_flips=1500, p_noise=0.15):
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

def update_beta(beta, observed_sizes, target=0.10, gamma=0.5):
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

def solve_3sat_mcmc_higher_order(num_vars, clauses, max_sweeps=300, u_sat=1.0, beta_init=0.5, target_q=0.10, exact_threshold=18, verbose=False):
    """
    The full MCMC Higher-Order solver.
    """
    t_start = time.time()
    
    # 1. Preprocessing
    active_vars, active_clauses, fixed_literals, fixed_empty_clauses = \
        recursive_unit_propagation_and_reductions(num_vars, clauses, verbose=verbose)
        
    if len(active_vars) == 0:
        spins = {v: fixed_literals.get(v, 1) for v in range(1, num_vars + 1)}
        return spins, time.time() - t_start, fixed_empty_clauses
        
    # 2. Extended Graph construction
    A, var_to_idx, clause3_list, clause_to_merged_idx = \
        build_signed_graph_for_3sat(num_vars, active_vars, active_clauses, u=u_sat, verbose=verbose)
    total_nodes = A.shape[0]
    N_red = len(active_vars)
    
    # 3. Triangles and LP Transfer
    triangles = find_triangles(A)
    omega, rho, edges_list, edge_to_idx = transfer_weights_to_triangles(A, triangles)
    
    # 4. Initialize spins
    sigma = np.ones(total_nodes, dtype=float)
    # Initialize variables randomly
    for v in range(1, N_red + 1):
        sigma[v] = random.choice([-1.0, 1.0])
    sigma[0] = 1.0 # reference T
    optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
    
    best_spins = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
    best_unsat = count_unsat_clauses(best_spins, clauses)
    
    if best_unsat == 0:
        return best_spins, time.time() - t_start, 0
        
    beta = beta_init
    observed_sizes = []
    
    for sweep in range(1, max_sweeps + 1):
        frozen_edges = []
        
        # 1. Gel of residual edges
        for idx, (u, v) in enumerate(edges_list):
            epsilon_e = np.sign(A[u, v])
            if epsilon_e * sigma[u] * sigma[v] == 1.0:
                p_gel = 1.0 - np.exp(-beta * rho[idx])
                if random.random() < p_gel:
                    frozen_edges.append((u, v))
                    
        # 2. Gel of triangles
        for t_idx, (u, v, w) in enumerate(triangles):
            omega_t = omega[t_idx]
            if omega_t < 1e-9:
                continue
                
            e1 = (u, v) if (u, v) in edge_to_idx else (v, u)
            e2 = (v, w) if (v, w) in edge_to_idx else (w, v)
            e3 = (u, w) if (u, w) in edge_to_idx else (w, u)
            
            eps1 = np.sign(A[e1[0], e1[1]])
            eps2 = np.sign(A[e2[0], e2[1]])
            eps3 = np.sign(A[e3[0], e3[1]])
            
            y1 = eps1 * sigma[e1[0]] * sigma[e1[1]]
            y2 = eps2 * sigma[e2[0]] * sigma[e2[1]]
            y3 = eps3 * sigma[e3[0]] * sigma[e3[1]]
            
            p_t = eps1 * eps2 * eps3
            
            if p_t == 1.0: # Non-frustrated
                if y1 == 1.0 and y2 == 1.0 and y3 == 1.0:
                    p_gel = 1.0 - np.exp(-2.0 * beta * omega_t)
                    if random.random() < p_gel:
                        frozen_edges.extend([e1, e2, e3])
            else: # Frustrated
                satisfied_edges = []
                if y1 == 1.0: satisfied_edges.append(e1)
                if y2 == 1.0: satisfied_edges.append(e2)
                if y3 == 1.0: satisfied_edges.append(e3)
                
                if len(satisfied_edges) == 2:
                    p_gel = 1.0 - np.exp(-2.0 * beta * omega_t)
                    if random.random() < p_gel:
                        e_freeze = random.choice(satisfied_edges)
                        frozen_edges.append(e_freeze)
                        
        # 3. Construct clusters (Union-Find)
        parent = {i: i for i in range(total_nodes)}
        
        def find_root(i):
            path = []
            while parent[i] != i:
                path.append(i)
                i = parent[i]
            for node in path:
                parent[node] = i
            return i

        def union(i, j):
            root_i = find_root(i)
            root_j = find_root(j)
            if root_i != root_j:
                parent[root_i] = root_j
                
        for u, v in frozen_edges:
            union(u, v)
            
        clusters = {}
        for i in range(total_nodes):
            root = find_root(i)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(i)
            
        pinned_root = find_root(0)
        
        # Adaptation of beta
        largest_q = get_largest_flippable_cluster_proportion(clusters, pinned_root, N_red)
        observed_sizes.append(largest_q)
        
        if sweep % 15 == 0:
            beta = update_beta(beta, observed_sizes, target=target_q)
            observed_sizes = []
            
        # 4. Build reduced MaxSAT problem on cluster flips
        full_sigma = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
        reduced_clauses = build_reduced_problem(clauses, full_sigma, parent, pinned_root, var_to_idx)
        reduced_clauses = [rc for rc in reduced_clauses if len(rc['forbidden']) > 0]
        
        flippable_roots = [r for r in clusters.keys() if r != pinned_root]
        m = len(flippable_roots)
        
        if m == 0:
            # All variables are pinned, no flip is possible.
            continue
            
        root_to_idx = {r: i for i, r in enumerate(flippable_roots)}
        
        # 5. Solve reduced problem
        if m <= exact_threshold:
            z_best = solve_reduced_exhaustive(reduced_clauses, m, root_to_idx)
        else:
            z_best = solve_reduced_walksat(reduced_clauses, m, root_to_idx)
            
        # 6. Apply flips
        for idx in range(1, total_nodes):
            r = find_root(idx)
            if r == pinned_root:
                z_val = 1
            else:
                z_val = z_best[root_to_idx[r]]
            sigma[idx] = z_val * sigma[idx]
            
        sigma[0] = 1.0 # Ensure T remains +1
        optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
        
        # 7. Evaluate SAT score
        curr_spins = extract_full_assignment(sigma, var_to_idx, fixed_literals, num_vars)
        curr_unsat = count_unsat_clauses(curr_spins, clauses)
        
        if curr_unsat < best_unsat:
            best_unsat = curr_unsat
            best_spins = curr_spins
            if best_unsat == 0:
                break
                
        # 8. Periodic restarts if stymied
        if sweep % 80 == 0 and best_unsat > 0:
            # Soft perturbation: restart 30% of original variables randomly
            for v in range(1, N_red + 1):
                if random.random() < 0.3:
                    sigma[v] = random.choice([-1.0, 1.0])
            optimize_auxiliaries(sigma, active_clauses, var_to_idx, clause3_list, clause_to_merged_idx)
            
    t_elapsed = time.time() - t_start
    return best_spins, t_elapsed, best_unsat
