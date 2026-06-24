import time
import random
import numpy as np
import scipy.sparse
import scipy.sparse.linalg
from scipy.optimize import linprog, minimize

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
    return A, var_to_idx

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

def solve_edge_space_qp(A, omega, rho, edges_list, edge_to_idx, triangles, kappa=1.0):
    """
    Formulates and solves the bounded convex edge-space QP using SciPy.
    Runs in O(Nt) complexity per iteration, vectorized with sparse incidence matrices.
    """
    Ne = len(edges_list)
    Nt = len(triangles)
    W = np.array([abs(A[u, v]) for u, v in edges_list], dtype=np.float64)
    
    if Ne == 0:
        return np.zeros(0)
    if Nt == 0:
        return np.zeros(Ne)
        
    rows = []
    cols = []
    data = []
    b = np.zeros(Nt, dtype=np.float64)
    
    for t_idx, (i, j, k) in enumerate(triangles):
        e1 = (i, j) if (i, j) in edge_to_idx else (j, i)
        e2 = (j, k) if (j, k) in edge_to_idx else (k, j)
        e3 = (i, k) if (i, k) in edge_to_idx else (k, i)
        
        idx1 = edge_to_idx[e1]
        idx2 = edge_to_idx[e2]
        idx3 = edge_to_idx[e3]
        
        rows.extend([t_idx, t_idx, t_idx])
        cols.extend([idx1, idx2, idx3])
        data.extend([1.0, 1.0, 1.0])
        
        sign1 = np.sign(A[e1[0], e1[1]])
        sign2 = np.sign(A[e2[0], e2[1]])
        sign3 = np.sign(A[e3[0], e3[1]])
        
        p_t = sign1 * sign2 * sign3
        b[t_idx] = 0.5 * (1.0 - p_t)
        
    # B2T is Nt x Ne. This is the transpose of the incidence matrix B2.
    B2T = scipy.sparse.coo_matrix((data, (rows, cols)), shape=(Nt, Ne)).tocsr()
    # B2 is Ne x Nt
    B2 = B2T.T.tocsr()
    
    def objective(p):
        obj = np.dot(W, p)
        v = B2T.dot(p) - b
        obj += kappa * np.dot(omega, v**2)
        return obj
        
    def gradient(p):
        v = B2T.dot(p) - b
        grad = W + 2.0 * kappa * B2.dot(omega * v)
        return grad
        
    p0 = np.zeros(Ne)
    res = minimize(objective, x0=p0, jac=gradient, bounds=[(0.0, 1.0)]*Ne, method='L-BFGS-B')
    return res.x

def project_edge_spins_to_vertices(A, p_opt, edges_list, y_cand, total_nodes):
    """
    Projects the predicted edge spins back to vertices using Z2 synchronization.
    """
    W = np.array([abs(A[u, v]) for u, v in edges_list], dtype=np.float64)
    c_e = W * np.abs(1.0 - 2.0 * p_opt)
    
    R = np.zeros((total_nodes, total_nodes), dtype=np.float64)
    for idx, (u, v) in enumerate(edges_list):
        epsilon_e = np.sign(A[u, v])
        val = c_e[idx] * epsilon_e * y_cand[idx]
        R[u, v] = val
        R[v, u] = val
        
    d = np.sum(np.abs(R), axis=1)
    if np.sum(d) < 1e-9:
        return np.ones(total_nodes)
        
    d_inv_sqrt = np.zeros_like(d)
    mask = d > 1e-9
    d_inv_sqrt[mask] = 1.0 / np.sqrt(d[mask])
    
    D_inv_sqrt = scipy.sparse.diags(d_inv_sqrt)
    D_sparse = scipy.sparse.diags(d)
    L_sync = D_sparse - scipy.sparse.csc_matrix(R)
    L_sync_norm = D_inv_sqrt @ L_sync @ D_inv_sqrt
    
    try:
        if total_nodes <= 100:
            eigenvalues, eigenvectors = np.linalg.eigh(L_sync_norm.toarray())
            idx_min = np.argmin(eigenvalues)
            v_min = eigenvectors[:, idx_min]
        else:
            eigenvalues, eigenvectors = scipy.sparse.linalg.eigsh(L_sync_norm, k=1, sigma=-1e-5, which='LM')
            v_min = eigenvectors[:, 0]
        v_min = D_inv_sqrt @ v_min
    except Exception:
        v_min = np.ones(total_nodes)
        
    aligned_spins = np.where(v_min >= 0, 1.0, -1.0)
    aligned_spins = aligned_spins * (1.0 if v_min[0] >= 0 else -1.0)
    aligned_spins[0] = 1.0
    return aligned_spins

def extract_full_assignment(aligned_spins, var_to_idx, fixed_literals, num_vars):
    """
    Reconstructs the full 3-SAT assignment including simplified variables.
    """
    spins = {}
    for v in range(1, num_vars + 1):
        if v in var_to_idx:
            idx = var_to_idx[v]
            spins[v] = int(aligned_spins[idx])
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

def solve_3sat_spectral_higher_order(num_vars, clauses, u=1.0, kappa=1.0, verbose=False):
    """
    The full Higher-Order Spectral signed graph solver.
    """
    t_start = time.time()
    
    active_vars, active_clauses, fixed_literals, fixed_empty_clauses = \
        recursive_unit_propagation_and_reductions(num_vars, clauses, verbose=verbose)
        
    if len(active_vars) == 0:
        spins = {v: fixed_literals.get(v, 1) for v in range(1, num_vars + 1)}
        return spins, time.time() - t_start, fixed_empty_clauses
        
    A, var_to_idx = build_signed_graph_for_3sat(num_vars, active_vars, active_clauses, u=u, verbose=verbose)
    total_nodes = A.shape[0]
    
    triangles = find_triangles(A)
    omega, rho, edges_list, edge_to_idx = transfer_weights_to_triangles(A, triangles)
    
    p_opt = solve_edge_space_qp(A, omega, rho, edges_list, edge_to_idx, triangles, kappa=kappa)
    
    thresholds = np.linspace(0.05, 0.95, 20)
    best_spins = None
    best_unsat = len(clauses) + 1
    
    unique_y = []
    for tau in thresholds:
        y_cand = np.where(p_opt <= tau, 1, -1)
        already_processed = False
        for y_seen in unique_y:
            if np.array_equal(y_cand, y_seen):
                already_processed = True
                break
        if already_processed:
            continue
        unique_y.append(y_cand)
        
        aligned_spins = project_edge_spins_to_vertices(A, p_opt, edges_list, y_cand, total_nodes)
        spins = extract_full_assignment(aligned_spins, var_to_idx, fixed_literals, num_vars)
        unsat = count_unsat_clauses(spins, clauses)
        
        if unsat < best_unsat:
            best_unsat = unsat
            best_spins = spins
            
    t_elapsed = time.time() - t_start
    return best_spins, t_elapsed, best_unsat
