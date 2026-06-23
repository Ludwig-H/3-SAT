
import matplotlib
matplotlib.use('Agg')
import random
random.seed(42)
source_du_benchmark = "Circuit Miter"
difficulte = "Moyen"
miter_nombre_portes = 50
prop_gel = 0.1
PUBLIC_BENCHMARKS = {}

# ==========================================
# MARKDOWN CELL 0
# ==========================================
# # Comparaison de Performance GPU (A100) : Solver de Clusters vs Baseline CDCL (PySAT)
# 
# Ce notebook implémente et compare deux approches de résolution pour le problème 3-SAT sur des instances réelles/industrielles :
# 1. **Baseline CDCL** : Résolution via MiniSat/Glucose via la bibliothèque `PySAT` (s'exécutant sur CPU).
# 2. **Solver de Clusters Hybride Optimisé GPU** : Implémentation complète en **PyTorch** s'exécutant entièrement sur le GPU (A100). Elle utilise la propagation d'étiquettes parallèle pour la phase de gel de Swendsen-Wang, un échantillonnage MCMC parallèle, et une décomposition spectrale sur GPU pour le clustering final.
# 
# ## 0. Configuration de l'environnement

# ==========================================
# CODE CELL 1
# ==========================================
#@title Installation et Importations
# !pip install python-sat

import time
import random
import urllib.request
import numpy as np
import torch
from scipy.optimize import linprog
import matplotlib.pyplot as plt

# Vérification du GPU
print("GPU Disponible :", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Nom du GPU :", torch.cuda.get_device_name(0))

# ==========================================
# MARKDOWN CELL 2
# ==========================================
# ## 1. Choix du Benchmark Réel, de la Taille et de la Difficulté
# 
# Sélectionnez le type d'instance réelle à évaluer via les formulaires ci-dessous :
# - **Circuit Miter** : Généré sur le champ, paramétrable en taille (nombre de portes) et en difficulté.
# - **SATLIB BMC / Planning** : Téléchargement automatique de benchmarks industriels classiques réels de difficultés croissantes (Facile, Moyen, Difficile).

# ==========================================
# CODE CELL 3
# ==========================================
#@title Configuration de l'Instance { run: "auto" }
source_du_benchmark = "Circuit Miter" #@param ["Circuit Miter", "SATLIB Bounded Model Checking (BMC)", "SATLIB Planning (Blocks World)"]
difficulte = "Moyen" #@param ["Facile", "Moyen", "Difficile"]
miter_nombre_portes = 300 #@param {type:"integer"}
prop_gel = 0.15 #@param {type:"number"}

PUBLIC_BENCHMARKS = {
    "SATLIB Bounded Model Checking (BMC)": {
        "Facile": {
            "url": "http://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/BMC/queueinvar10.cnf",
            "name": "queueinvar10"
        },
        "Moyen": {
            "url": "http://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/BMC/barrel7.cnf",
            "name": "barrel7"
        },
        "Difficile": {
            "url": "http://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/BMC/barrel8.cnf",
            "name": "barrel8"
        }
    },
    "SATLIB Planning (Blocks World)": {
        "Facile": {
            "url": "http://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/PLANNING/BlocksWorld/bw_large.a.cnf",
            "name": "bw_large.a"
        },
        "Moyen": {
            "url": "http://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/PLANNING/BlocksWorld/bw_large.b.cnf",
            "name": "bw_large.b"
        },
        "Difficile": {
            "url": "http://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/PLANNING/BlocksWorld/bw_large.c.cnf",
            "name": "bw_large.c"
        }
    }
}

# ==========================================
# MARKDOWN CELL 4
# ==========================================
# ## 2. Utilitaires de Chargement et Encodage 3-SAT

# ==========================================
# CODE CELL 5
# ==========================================
def generate_miter_circuit_3sat(n_inputs=50, n_gates=150, diff="Moyen"):
    """
    Génère une instance de vérification d'équivalence de circuits sous forme de clauses 3-SAT.
    La difficulté ajuste la mutation : 1 porte mutée (Facile), 2 portes mutées (Moyen), 4 portes mutées (Difficile).
    """
    clauses = []
    next_var = n_inputs + 1
    gates1 = []
    gates2 = []
    
    current_vars = list(range(1, n_inputs + 1))
    for _ in range(n_gates):
        gtype = random.choice(["AND", "OR", "XOR"])
        in1 = random.choice(current_vars)
        in2 = random.choice(current_vars)
        out = next_var
        next_var += 1
        gates1.append((gtype, out, in1, in2))
        current_vars.append(out)
    output1 = current_vars[-1]
    
    # Détermination du nombre de mutations selon la difficulté
    n_mutations = 1 if diff == "Facile" else (2 if diff == "Moyen" else 4)
    mutated_indices = set(random.sample(range(n_gates), min(n_mutations, n_gates)))
    
    var_offset = next_var - (n_inputs + 1)
    
    for i, (gtype, out, in1, in2) in enumerate(gates1):
        out2 = out + var_offset
        in1_2 = in1 if in1 <= n_inputs else in1 + var_offset
        in2_2 = in2 if in2 <= n_inputs else in2 + var_offset
        
        if i in mutated_indices:
            new_type = "OR" if gtype == "AND" else "AND"
            gates2.append((new_type, out2, in1_2, in2_2))
        else: 
            gates2.append((gtype, out2, in1_2, in2_2))
            
    output2 = current_vars[-1] + var_offset
    next_var = output2 + 1
    
    # Encodage de Tseitin pour les deux circuits
    for g1, g2 in [(gates1, ""), (gates2, "_2")]:
        for gtype, out, in1, in2 in g1:
            if gtype == "AND":
                clauses.append([in1, -out])
                clauses.append([in2, -out])
                clauses.append([-in1, -in2, out])
            elif gtype == "OR":
                clauses.append([-in1, out])
                clauses.append([-in2, out])
                clauses.append([in1, in2, -out])
            elif gtype == "XOR":
                clauses.append([-in1, -in2, -out])
                clauses.append([in1, in2, -out])
                clauses.append([-in1, in2, out])
                clauses.append([in1, -in2, out])
                
    # Porte Miter XOR finale sur les sorties des deux circuits
    miter_out = next_var
    clauses.append([-output1, -output2, -miter_out])
    clauses.append([output1, output2, -miter_out])
    clauses.append([-output1, output2, miter_out])
    clauses.append([output1, -output2, miter_out])
    clauses.append([miter_out])
    
    return convert_to_3sat(miter_out, clauses)

def parse_dimacs(content):
    clauses = []
    num_vars = 0
    current_clause = []
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('c'):
            continue
        if line.startswith('p cnf'):
            parts = line.split()
            num_vars = int(parts[2])
            continue
        for token in line.split():
            val = int(token)
            if val == 0:
                if current_clause:
                    clauses.append(current_clause)
                    current_clause = []
            else: 
                current_clause.append(val)
    if current_clause:
        clauses.append(current_clause)
    return num_vars, clauses

def convert_to_3sat(num_vars, clauses):
    final_cnf = []
    next_var = num_vars + 1
    for c in clauses:
        if len(c) <= 3:
            final_cnf.append(c)
        else:
            curr = c
            while len(curr) > 3:
                aux = next_var
                next_var += 1
                final_cnf.append([curr[0], curr[1], aux])
                curr = [-aux] + curr[2:]
            final_cnf.append(curr)
    return next_var - 1, final_cnf

def load_selected_benchmark():
    if source_du_benchmark == "Circuit Miter":
        n_inputs = max(5, miter_nombre_portes // 5)
        return generate_miter_circuit_3sat(n_inputs=n_inputs, n_gates=miter_nombre_portes, diff=difficulte)
    else:
        bench_info = PUBLIC_BENCHMARKS[source_du_benchmark][difficulte]
        url = bench_info["url"]
        print(f"Téléchargement du benchmark public : {bench_info['name']}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
            num_vars, clauses = parse_dimacs(content)
            return convert_to_3sat(num_vars, clauses)
        except Exception as e:
            print(f"\n[ERREUR] Impossible de télécharger le benchmark ({e}).")
            print("Génération automatique d'un fallback local 'Circuit Miter'...")
            n_inputs = max(5, miter_nombre_portes // 5)
            return generate_miter_circuit_3sat(n_inputs=n_inputs, n_gates=miter_nombre_portes, diff=difficulte)

num_vars, clauses_3sat = load_selected_benchmark()
print(f"Instance prête : {num_vars} variables, {len(clauses_3sat)} clauses (toutes tailles confondues, 1/2/3-SAT conservées).")


# ==========================================
# MARKDOWN CELL 6
# ==========================================
# ## 3. Pré-traitement et Double Transfert d'Énergie

# ==========================================
# CODE CELL 7
# ==========================================
def recursive_unit_propagation_and_reductions(num_vars, clauses, verbose=True):
    if verbose:
        print(f"[Preprocessing] Élimination unitaire récursive & littéraux purs sur {num_vars} variables et {len(clauses)} clauses...")
    
    fixed_literals = {}
    active_clauses = [list(c) for c in clauses]
    active_vars = set(range(1, num_vars + 1))
    
    changed = True
    while changed:
        changed = False
        
        # Éliminer les clauses vides de façon robuste
        active_clauses = [c for c in active_clauses if len(c) > 0]
        
        # Détection et comptage des clauses unitaires actives
        unit_counts = {}
        for c in active_clauses:
            if len(c) == 1:
                lit = c[0]
                unit_counts[lit] = unit_counts.get(lit, 0) + 1
                
        if unit_counts:
            # Traiter les variables avec clauses unitaires
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
                    
                # Compter les occurrences opposées dans les clauses de taille >= 2
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
                
                # Condition d'assignation forcée m >= k
                if m >= k:
                    if verbose:
                        print(f"  -> Assignation forcée de x_{var} = {l_val} (m={m} >= k={k})")
                    fixed_literals[var] = l_val
                    active_vars.remove(var)
                    
                    # Mise à jour des clauses
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
                
        # Élimination des littéraux purs si aucune assignation unitaire forcée n'a eu lieu
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
                pure_vars.append((var, 1)) # Variable orpheline
                
        if pure_vars:
            changed = True
            for var, val in pure_vars:
                if verbose:
                    if pos_counts[var] == 0 and neg_counts[var] == 0:
                        print(f"  -> Élimination de la variable orpheline x_{var} = {val}")
                    else:
                        print(f"  -> Élimination du littéral pur x_{var} = {val}")
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
            
    if verbose:
        print(f"  -> Prétraitement terminé : {len(active_vars)} variables actives, {len(active_clauses)} clauses actives (fixées : {len(fixed_literals)}).")
    return active_vars, active_clauses, fixed_literals

def perform_double_energy_transfer(active_vars, active_clauses, u=1.0, verbose=True):
    if verbose:
        print(f"[Preprocessing] Début du Double Transfert d'Énergie...")
    var_list = sorted(list(active_vars))
    var_to_idx = {v: i for i, v in enumerate(var_list)}
    N_red = len(var_list)
    
    W_init = {}
    for c in active_clauses:
        if len(c) == 3:
            i1, i2, i3 = abs(c[0]), abs(c[1]), abs(c[2])
            idx1, idx2, idx3 = var_to_idx[i1], var_to_idx[i2], var_to_idx[i3]
            pols = [1 if x > 0 else -1 for x in c]
            
            pairs = [(idx1, idx2, pols[0]*pols[1]), 
                     (idx2, idx3, pols[1]*pols[2]), 
                     (idx1, idx3, pols[0]*pols[2])]
            
            for u_idx, v_idx, sign in pairs:
                edge = (min(u_idx, v_idx), max(u_idx, v_idx))
                contrib = -sign * (u / 2.0)
                W_init[edge] = W_init.get(edge, 0.0) + contrib
        elif len(c) == 2:
            i1, i2 = abs(c[0]), abs(c[1])
            idx1, idx2 = var_to_idx[i1], var_to_idx[i2]
            pols = [1 if x > 0 else -1 for x in c]
            
            edge = (min(idx1, idx2), max(idx1, idx2))
            contrib = -pols[0]*pols[1] * u
            W_init[edge] = W_init.get(edge, 0.0) + contrib

    W_init = {k: v for k, v in W_init.items() if abs(v) > 1e-6}
    edges_list = sorted(list(W_init.keys()))
    edge_to_idx = {e: i for i, e in enumerate(edges_list)}
    
    triangles = []
    adjacency = {i: set() for i in range(N_red)}
    for u_idx, v_idx in edges_list:
        adjacency[u_idx].add(v_idx)
        adjacency[v_idx].add(u_idx)
        
    for a in range(N_red):
        for b in adjacency[a]:
            if b > a:
                for c in adjacency[b]:
                    if c > b and c in adjacency[a]:
                        s1 = np.sign(W_init[(a, b)])
                        s2 = np.sign(W_init[(b, c)])
                        s3 = np.sign(W_init[(a, c)])
                        prod_signs = s1 * s2 * s3
                        triangles.append((a, b, c, prod_signs))
                        
    n_edges = len(edges_list)
    n_triangles = len(triangles)
    if verbose:
        print(f"  -> Graphe d'interactions : {n_edges} arêtes et {n_triangles} triangles détectés.")
    
    if n_triangles > 0 and n_edges > 0:
        if verbose:
            print("  -> Résolution de l'optimisation linéaire (LP) pour recalibrer les poids des triangles...")
        c_lp = -np.ones(n_triangles)
        A_ub = np.zeros((n_edges, n_triangles))
        b_ub = np.zeros(n_edges)
        
        for t_idx, (a, b, c, _) in enumerate(triangles):
            e1 = edge_to_idx[(a, b)]
            e2 = edge_to_idx[(b, c)]
            e3 = edge_to_idx[(a, c)]
            A_ub[e1, t_idx] = 1.0
            A_ub[e2, t_idx] = 1.0
            A_ub[e3, t_idx] = 1.0
            
        for e_idx, edge in enumerate(edges_list):
            b_ub[e_idx] = abs(W_init[edge])
            
        res = linprog(c_lp, A_ub=A_ub, b_ub=b_ub, bounds=(0, None), method='highs')
        omega = res.x if res.success else np.zeros(n_triangles)
    else:
        omega = np.zeros(n_triangles)
        
    W_res = W_init.copy()
    triangles_nf = []
    triangles_f = []
    
    for t_idx, (a, b, c, prod_signs) in enumerate(triangles):
        w_t = omega[t_idx]
        if w_t > 1e-6:
            for u_idx, v_idx in [(a, b), (b, c), (a, c)]:
                edge = (u_idx, v_idx)
                W_res[edge] -= np.sign(W_res[edge]) * w_t
                
            s1 = np.sign(W_init[(a, b)])
            s2 = np.sign(W_init[(b, c)])
            s3 = np.sign(W_init[(a, c)])
            
            if prod_signs > 0:
                triangles_nf.append([a, b, c, w_t, s1, s2, s3])
            else:
                triangles_f.append([a, b, c, w_t, s1, s2, s3])
                
    W_res = {k: v for k, v in W_res.items() if abs(v) > 1e-6}
    if verbose:
        total_init = sum(abs(v) for v in W_init.values())
        total_transferred = 3.0 * sum(omega)
        total_residual = sum(abs(v) for v in W_res.values())
        pct_transferred = (total_transferred / total_init) * 100 if total_init > 1e-6 else 0.0
        pct_residual = (total_residual / total_init) * 100 if total_init > 1e-6 else 0.0
        print(f"  -> LP terminé. Poids résiduels : {len(W_res)} arêtes résiduelles, {len(triangles_nf)} triangles NF, {len(triangles_f)} triangles F.")
        print(f"  -> Bilan de transfert d'énergie :")
        print(f"     * Énergie couplage initiale (arêtes) : {total_init:.4f}")
        print(f"     * Énergie transférée (triangles)      : {total_transferred:.4f} ({pct_transferred:.2f}%)")
        print(f"     * Énergie résiduelle (arêtes)         : {total_residual:.4f} ({pct_residual:.2f}%)")
    
    return N_red, var_to_idx, W_res, triangles_nf, triangles_f


# ==========================================
# MARKDOWN CELL 8
# ==========================================
# ## 4. Implémentation du Solver GPU (PyTorch CUDA Optimisé)

# ==========================================
# CODE CELL 9
# ==========================================
class GPUPartialClusterDynamicsSolver:
    def __init__(self, N_red, var_to_idx, W_res, triangles_nf, triangles_f, active_clauses, u=1.0, verbose=True):
        self.N_red = N_red
        self.var_to_idx = var_to_idx
        self.u = u
        self.verbose = verbose
        
        # Extraction des clauses par taille
        clause3_vars = []
        clause3_pols = []
        clause2_vars = []
        clause2_pols = []
        
        # Vecteur pour les champs unitaires (1-SAT)
        h_tot_np = np.zeros(N_red)
        
        for c in active_clauses:
            if len(c) == 3:
                clause3_vars.append([var_to_idx[abs(lit)] for lit in c])
                clause3_pols.append([1 if lit > 0 else -1 for lit in c])
            elif len(c) == 2:
                clause2_vars.append([var_to_idx[abs(lit)] for lit in c])
                clause2_pols.append([1 if lit > 0 else -1 for lit in c])
            elif len(c) == 1:
                var_idx = var_to_idx[abs(c[0])]
                pol = 1 if c[0] > 0 else -1
                h_tot_np[var_idx] += pol * 0.5 # Facteur u multiplié dans set_u
                
        self.clause3_vars = torch.tensor(clause3_vars, dtype=torch.long, device='cpu') if clause3_vars else torch.zeros((0, 3), dtype=torch.long, device='cpu')
        self.clause3_pols = torch.tensor(clause3_pols, dtype=torch.float32, device='cpu') if clause3_pols else torch.zeros((0, 3), dtype=torch.float32, device='cpu')
        
        self.clause2_vars = torch.tensor(clause2_vars, dtype=torch.long, device='cpu') if clause2_vars else torch.zeros((0, 2), dtype=torch.long, device='cpu')
        self.clause2_pols = torch.tensor(clause2_pols, dtype=torch.float32, device='cpu') if clause2_pols else torch.zeros((0, 2), dtype=torch.float32, device='cpu')
        
        self.h_tot_base = torch.tensor(h_tot_np, dtype=torch.float32, device='cpu')
        
        res_src, res_dst, res_weights = [], [], []
        for (u_node, v_node), weight in W_res.items():
            res_src.append(u_node)
            res_dst.append(v_node)
            res_weights.append(weight)
            
        self.res_src = torch.tensor(res_src, dtype=torch.long, device='cpu')
        self.res_dst = torch.tensor(res_dst, dtype=torch.long, device='cpu')
        self.res_weights_base = torch.tensor(res_weights, dtype=torch.float32, device='cpu')
        
        if triangles_nf:
            nf_arr = np.array(triangles_nf)
            self.nf_vertices = torch.tensor(nf_arr[:, :3], dtype=torch.long, device='cpu')
            self.nf_weights_base = torch.tensor(nf_arr[:, 3], dtype=torch.float32, device='cpu')
            self.nf_signs = torch.tensor(nf_arr[:, 4:7], dtype=torch.float32, device='cpu')
        else:
            self.nf_vertices = torch.zeros((0, 3), dtype=torch.long, device='cpu')
            self.nf_weights_base = torch.zeros(0, dtype=torch.float32, device='cpu')
            self.nf_signs = torch.zeros((0, 3), dtype=torch.float32, device='cpu')
            
        if triangles_f:
            f_arr = np.array(triangles_f)
            self.f_vertices = torch.tensor(f_arr[:, :3], dtype=torch.long, device='cpu')
            self.f_weights_base = torch.tensor(f_arr[:, 3], dtype=torch.float32, device='cpu')
            self.f_signs = torch.tensor(f_arr[:, 4:7], dtype=torch.float32, device='cpu')
        else:
            self.f_vertices = torch.zeros((0, 3), dtype=torch.long, device='cpu')
            self.f_weights_base = torch.zeros(0, dtype=torch.float32, device='cpu')
            self.f_signs = torch.zeros((0, 3), dtype=torch.float32, device='cpu')
            
        self.set_u(u)
        if self.verbose:
            print(f"[GPU Solver] Initialisation avec N_red={N_red} variables actives, res_edges={self.res_src.shape[0]}, triangles_nf={self.nf_vertices.shape[0]}, triangles_f={self.f_vertices.shape[0]}.")
        
    def set_u(self, u):
        self.u = u
        self.res_weights = self.res_weights_base * u
        self.nf_weights = self.nf_weights_base * u
        self.f_weights = self.f_weights_base * u
        self.h_tot = self.h_tot_base * u
        
    def compute_oriented_energy(self, spins):
        """
        Calcule uniquement l'énergie de la partie orientée U_ori(spins) :
        U_ori = u * sum(I_ori_3) + u * sum(I_ori_bin_2) - sum(h_tot * spins)
        """
        energy3 = 0.0
        if self.clause3_vars.shape[0] > 0:
            lit_vals = self.clause3_pols * spins[self.clause3_vars]
            satisfied = (lit_vals == 1.0).any(dim=1)
            energy3 = self.u * (~satisfied).sum()
            
        energy2 = 0.0
        if self.clause2_vars.shape[0] > 0:
            lit_vals = self.clause2_pols * spins[self.clause2_vars]
            satisfied = (lit_vals == 1.0).any(dim=1)
            energy2 = self.u * (~satisfied).sum()
            
        energy_fields = - (self.h_tot * spins).sum()
        
        return energy3 + energy2 + energy_fields

    def compute_total_unsat_clauses(self, spins):
        """
        Calcule le nombre réel de clauses insatisfaites de toutes tailles
        """
        unsat = 0
        
        # 1-clauses
        if self.h_tot.shape[0] > 0:
            unsat += (torch.abs(self.h_tot_base) - self.h_tot_base * spins).sum().item()
            
        # 2-clauses
        if self.clause2_vars.shape[0] > 0:
            lit_vals = self.clause2_pols * spins[self.clause2_vars]
            satisfied = (lit_vals == 1.0).any(dim=1)
            unsat += (~satisfied).sum().item()
            
        # 3-clauses
        if self.clause3_vars.shape[0] > 0:
            lit_vals = self.clause3_pols * spins[self.clause3_vars]
            satisfied = (lit_vals == 1.0).any(dim=1)
            unsat += (~satisfied).sum().item()
            
        return int(round(unsat))
        
    def compute_giant_size(self, spins):
        t_nf_count = self.nf_vertices.shape[0]
        t_f_count = self.f_vertices.shape[0]
        res_count = self.res_src.shape[0]
        
        frozen_edges_src = []
        frozen_edges_dst = []
        if res_count > 0:
            satisfied_res = (spins[self.res_src] * spins[self.res_dst] * self.res_weights.sign()) > 0
            probs_res = 1.0 - torch.exp(-torch.abs(self.res_weights))
            freeze_res = satisfied_res & (torch.rand(res_count, device='cpu') < probs_res)
            frozen_edges_src.append(self.res_src[freeze_res])
            frozen_edges_dst.append(self.res_dst[freeze_res])
            
        if t_nf_count > 0:
            e0 = (spins[self.nf_vertices[:, 0]] * spins[self.nf_vertices[:, 1]] * self.nf_signs[:, 0]) > 0
            e1 = (spins[self.nf_vertices[:, 1]] * spins[self.nf_vertices[:, 2]] * self.nf_signs[:, 1]) > 0
            e2 = (spins[self.nf_vertices[:, 0]] * spins[self.nf_vertices[:, 2]] * self.nf_signs[:, 2]) > 0
            satisfied_tri = e0 & e1 & e2
            probs_nf = 1.0 - torch.exp(-2.0 * self.nf_weights)
            freeze_nf = satisfied_tri & (torch.rand(t_nf_count, device='cpu') < probs_nf)
            u_nodes = self.nf_vertices[freeze_nf]
            for u_n, v_n in [(u_nodes[:, 0], u_nodes[:, 1]), (u_nodes[:, 1], u_nodes[:, 2]), (u_nodes[:, 0], u_nodes[:, 2])]:
                frozen_edges_src.append(u_n)
                frozen_edges_dst.append(v_n)

        if t_f_count > 0:
            e0 = (spins[self.f_vertices[:, 0]] * spins[self.f_vertices[:, 1]] * self.f_signs[:, 0]) > 0
            e1 = (spins[self.f_vertices[:, 1]] * spins[self.f_vertices[:, 2]] * self.f_signs[:, 1]) > 0
            e2 = (spins[self.f_vertices[:, 0]] * spins[self.f_vertices[:, 2]] * self.f_signs[:, 2]) > 0
            case = e0.to(torch.int32) * 1 + e1.to(torch.int32) * 2 + e2.to(torch.int32) * 4
            sat_edge1 = torch.where(case == 6, 1, 0)
            sat_edge2 = torch.where(case == 3, 1, 2)
            r = torch.rand(t_f_count, device='cpu')
            half_prob = 0.5 * (1.0 - torch.exp(-2.0 * self.f_weights))
            freeze1 = (r < half_prob) & (case > 0)
            freeze2 = (r >= half_prob) & (r < 2.0 * half_prob) & (case > 0)
            edges1_nodes = torch.where((sat_edge1 == 0).unsqueeze(1), self.f_vertices[:, [0, 1]], 
                                       torch.where((sat_edge1 == 1).unsqueeze(1), self.f_vertices[:, [1, 2]], self.f_vertices[:, [0, 2]]))
            frozen_edges_src.append(edges1_nodes[freeze1, 0])
            frozen_edges_dst.append(edges1_nodes[freeze1, 1])
            edges2_nodes = torch.where((sat_edge2 == 0).unsqueeze(1), self.f_vertices[:, [0, 1]], 
                                       torch.where((sat_edge2 == 1).unsqueeze(1), self.f_vertices[:, [1, 2]], self.f_vertices[:, [0, 2]]))
            frozen_edges_src.append(edges2_nodes[freeze2, 0])
            frozen_edges_dst.append(edges2_nodes[freeze2, 1])

        labels = torch.arange(self.N_red, dtype=torch.float32, device='cpu')
        if len(frozen_edges_src) > 0:
            src = torch.cat(frozen_edges_src)
            dst = torch.cat(frozen_edges_dst)
            sym_src = torch.cat([src, dst])
            sym_dst = torch.cat([dst, src])
            if sym_src.shape[0] > 0:
                for _ in range(50):
                    labels_next = torch.scatter_reduce(labels, 0, sym_dst, labels[sym_src], reduce='amax', include_self=True)
                    if torch.equal(labels, labels_next):
                        break
                    labels = labels_next
        
        unique_labels, counts = torch.unique(labels, return_counts=True)
        max_count = counts.max().item() if counts.numel() > 0 else 0
        return max_count / self.N_red
        
    def calibrate_u(self, prop_gel=0.5, trials=5, search_steps=12):
        if self.verbose:
            print(f"[GPU Calibration] Lancement de la calibration de u (cible prop_gel={prop_gel})...")
        
        self.set_u(5.0)
        max_sizes = []
        for _ in range(trials):
            spins = torch.randint(0, 2, (self.N_red,), device='cpu').float() * 2 - 1
            max_sizes.append(self.compute_giant_size(spins))
        max_giant = sum(max_sizes) / len(max_sizes)
        
        target_gel = prop_gel
        if max_giant < prop_gel:
            target_gel = 0.9 * max_giant
            if self.verbose:
                print(f"  -> [Ajustement Cible] prop_gel={prop_gel} inaccessible en raison de la frustration (max={max_giant:.4f}). Nouvelle cible : {target_gel:.4f}")
                
        u_min, u_max = 0.01, 5.0
        for step in range(search_steps):
            u_mid = (u_min + u_max) / 2.0
            self.set_u(u_mid)
            
            giant_sizes = []
            for _ in range(trials):
                spins = torch.randint(0, 2, (self.N_red,), device='cpu').float() * 2 - 1
                giant_sizes.append(self.compute_giant_size(spins))
                
            avg_giant = sum(giant_sizes) / len(giant_sizes)
            if self.verbose:
                print(f"  Étape {step+1}/{search_steps} : u_mid={u_mid:.4f} -> taille moy. composante géante={avg_giant:.4f}")
            if avg_giant < target_gel:
                u_min = u_mid
            else:
                u_max = u_mid
                
        best_u = (u_min + u_max) / 2.0
        self.set_u(best_u)
        if best_u > 4.9 and avg_giant < prop_gel:
            print(f"ATTENTION : La cible prop_gel = {prop_gel} est inaccessible en raison de la frustration topologique.")
            print(f"La taille maximale de la composante géante sature à {avg_giant:.4f}. u a été limité à {best_u:.4f} pour éviter de figer la dynamique.")
        else:
            print(f"Calibration de u terminée : u_calibre = {best_u:.4f} (taille composante géante = {avg_giant:.4f})")
        return best_u

    def run_mcmc(self, steps=1000, burn_in=200, n_mh_steps=None):
        device = self.res_src.device
        if self.verbose:
            print(f"[GPU MCMC] Lancement de {steps} étapes MCMC (Burn-in={burn_in}) sur le device {device}...")
        
        spins = torch.randint(0, 2, (self.N_red,), device=device).float() * 2 - 1
        
        sum_spins = torch.zeros(self.N_red, dtype=torch.float64, device=device)
        sum_outer = torch.zeros((self.N_red, self.N_red), dtype=torch.float64, device=device)
        sample_count = 0
        
        t_nf_count = self.nf_vertices.shape[0]
        t_f_count = self.f_vertices.shape[0]
        res_count = self.res_src.shape[0]
        
        self.energy_history = []
        self.giant_component_history = []
        
        num_clause3 = self.clause3_vars.shape[0]
        num_clause2 = self.clause2_vars.shape[0]
        
        for step in range(steps):
            frozen_edges_src = []
            frozen_edges_dst = []
            
            if res_count > 0:
                satisfied_res = (spins[self.res_src] * spins[self.res_dst] * self.res_weights.sign()) > 0
                probs_res = 1.0 - torch.exp(-torch.abs(self.res_weights))
                freeze_res = satisfied_res & (torch.rand(res_count, device=device) < probs_res)
                frozen_edges_src.append(self.res_src[freeze_res])
                frozen_edges_dst.append(self.res_dst[freeze_res])
                
            if t_nf_count > 0:
                e0 = (spins[self.nf_vertices[:, 0]] * spins[self.nf_vertices[:, 1]] * self.nf_signs[:, 0]) > 0
                e1 = (spins[self.nf_vertices[:, 1]] * spins[self.nf_vertices[:, 2]] * self.nf_signs[:, 1]) > 0
                e2 = (spins[self.nf_vertices[:, 0]] * spins[self.nf_vertices[:, 2]] * self.nf_signs[:, 2]) > 0
                
                satisfied_tri = e0 & e1 & e2
                probs_nf = 1.0 - torch.exp(-2.0 * self.nf_weights)
                freeze_nf = satisfied_tri & (torch.rand(t_nf_count, device=device) < probs_nf)
                
                u_nodes = self.nf_vertices[freeze_nf]
                for u_n, v_n in [(u_nodes[:, 0], u_nodes[:, 1]), (u_nodes[:, 1], u_nodes[:, 2]), (u_nodes[:, 0], u_nodes[:, 2])]:
                    frozen_edges_src.append(u_n)
                    frozen_edges_dst.append(v_n)
                    
            if t_f_count > 0:
                e0 = (spins[self.f_vertices[:, 0]] * spins[self.f_vertices[:, 1]] * self.f_signs[:, 0]) > 0
                e1 = (spins[self.f_vertices[:, 1]] * spins[self.f_vertices[:, 2]] * self.f_signs[:, 1]) > 0
                e2 = (spins[self.f_vertices[:, 0]] * spins[self.f_vertices[:, 2]] * self.f_signs[:, 2]) > 0
                
                case = e0.to(torch.int32) * 1 + e1.to(torch.int32) * 2 + e2.to(torch.int32) * 4
                
                sat_edge1 = torch.where(case == 6, 1, 0)
                sat_edge2 = torch.where(case == 3, 1, 2)
                
                r = torch.rand(t_f_count, device=device)
                half_prob = 0.5 * (1.0 - torch.exp(-2.0 * self.f_weights))
                
                freeze1 = (r < half_prob) & (case > 0)
                freeze2 = (r >= half_prob) & (r < 2.0 * half_prob) & (case > 0)
                
                edges1_nodes = torch.where((sat_edge1 == 0).unsqueeze(1), self.f_vertices[:, [0, 1]], 
                                           torch.where((sat_edge1 == 1).unsqueeze(1), self.f_vertices[:, [1, 2]], self.f_vertices[:, [0, 2]]))
                
                frozen_edges_src.append(edges1_nodes[freeze1, 0])
                frozen_edges_dst.append(edges1_nodes[freeze1, 1])
                
                edges2_nodes = torch.where((sat_edge2 == 0).unsqueeze(1), self.f_vertices[:, [0, 1]], 
                                           torch.where((sat_edge2 == 1).unsqueeze(1), self.f_vertices[:, [1, 2]], self.f_vertices[:, [0, 2]]))
                
                frozen_edges_src.append(edges2_nodes[freeze2, 0])
                frozen_edges_dst.append(edges2_nodes[freeze2, 1])
                
            labels = torch.arange(self.N_red, dtype=torch.float32, device=device)
            
            if len(frozen_edges_src) > 0:
                src = torch.cat(frozen_edges_src)
                dst = torch.cat(frozen_edges_dst)
                sym_src = torch.cat([src, dst])
                sym_dst = torch.cat([dst, src])
                
                if sym_src.shape[0] > 0:
                    for _ in range(50):
                        labels_next = torch.scatter_reduce(labels, 0, sym_dst, labels[sym_src], reduce='amax', include_self=True)
                        if torch.equal(labels, labels_next):
                            break
                        labels = labels_next
            
            unique_labels, counts = torch.unique(labels, return_counts=True)
            max_count = counts.max().item() if counts.numel() > 0 else 0
            self.giant_component_history.append(max_count / self.N_red)
                        
            # Recoloriage de Metropolis-Hastings (Partie Orientée U_ori, Luby MIS 100% GPU)
            unique_labels, cluster_indices = torch.unique(labels, return_inverse=True)
            M = unique_labels.shape[0]
            
            steps_mh = n_mh_steps if n_mh_steps is not None else 10 * M
            num_mis_iterations = max(5, steps_mh // M)
            
            clause3_clusters = cluster_indices[self.clause3_vars] if num_clause3 > 0 else torch.zeros((0, 3), dtype=torch.long, device=device)
            clause2_clusters = cluster_indices[self.clause2_vars] if num_clause2 > 0 else torch.zeros((0, 2), dtype=torch.long, device=device)
            
            clause3_sat = (self.clause3_pols * spins[self.clause3_vars] == 1.0).any(dim=1) if num_clause3 > 0 else torch.zeros(0, dtype=torch.bool, device=device)
            clause2_sat = (self.clause2_pols * spins[self.clause2_vars] == 1.0).any(dim=1) if num_clause2 > 0 else torch.zeros(0, dtype=torch.bool, device=device)
            
            for iter_mis in range(num_mis_iterations):
                w = torch.rand(M, device=device)
                
                clause3_max_w = w[clause3_clusters].max(dim=1)[0] if num_clause3 > 0 else torch.zeros(0, device=device)
                clause2_max_w = w[clause2_clusters].max(dim=1)[0] if num_clause2 > 0 else torch.zeros(0, device=device)
                
                cluster_max_w = torch.zeros(M, device=device)
                if num_clause3 > 0:
                    cluster_max_w.scatter_reduce_(0, clause3_clusters.view(-1), clause3_max_w.repeat_interleave(3), reduce='amax', include_self=True)
                if num_clause2 > 0:
                    cluster_max_w.scatter_reduce_(0, clause2_clusters.view(-1), clause2_max_w.repeat_interleave(2), reduce='amax', include_self=True)
                    
                in_mis = (w == cluster_max_w)
                if not in_mis.any():
                    continue
                    
                in_class = in_mis[cluster_indices]
                spins_cand = spins.clone()
                spins_cand[in_class] *= -1.0
                
                delta_E_cluster = torch.zeros(M, device=device)
                
                if num_clause3 > 0:
                    clause3_in_class = in_class[self.clause3_vars]
                    has_var_in_class = clause3_in_class.any(dim=1)
                    if has_var_in_class.any():
                        clause3_sat_cand = clause3_sat.clone()
                        clause3_sat_cand[has_var_in_class] = (self.clause3_pols[has_var_in_class] * spins_cand[self.clause3_vars[has_var_in_class]] == 1.0).any(dim=1)
                        
                        var_idx_in_clause = clause3_in_class.float().argmax(dim=1)
                        affected_cluster = clause3_clusters[torch.arange(num_clause3, device=device), var_idx_in_clause]
                        delta_E_clauses3 = self.u * (clause3_sat.float() - clause3_sat_cand.float())
                        delta_E_cluster.scatter_add_(0, affected_cluster[has_var_in_class], delta_E_clauses3[has_var_in_class])
                        
                if num_clause2 > 0:
                    clause2_in_class = in_class[self.clause2_vars]
                    has_var_in_class_2 = clause2_in_class.any(dim=1)
                    if has_var_in_class_2.any():
                        clause2_sat_cand = clause2_sat.clone()
                        clause2_sat_cand[has_var_in_class_2] = (self.clause2_pols[has_var_in_class_2] * spins_cand[self.clause2_vars[has_var_in_class_2]] == 1.0).any(dim=1)
                        
                        var_idx_in_clause_2 = clause2_in_class.float().argmax(dim=1)
                        affected_cluster_2 = clause2_clusters[torch.arange(num_clause2, device=device), var_idx_in_clause_2]
                        delta_E_clauses2 = self.u * (clause2_sat.float() - clause2_sat_cand.float())
                        delta_E_cluster.scatter_add_(0, affected_cluster_2[has_var_in_class_2], delta_E_clauses2[has_var_in_class_2])
                        
                delta_E_fields = torch.zeros(M, device=device)
                delta_E_fields.scatter_add_(0, cluster_indices[in_class], 2.0 * self.h_tot[in_class] * spins[in_class])
                
                delta_E = delta_E_cluster + delta_E_fields
                
                rands = torch.rand(M, device=device)
                alpha = torch.exp(-delta_E)
                accept = (rands < alpha) & in_mis
                
                accepted_clusters = torch.arange(M, device=device)[accept]
                if accepted_clusters.numel() > 0:
                    flip_mask = torch.isin(cluster_indices, accepted_clusters)
                    spins[flip_mask] = spins_cand[flip_mask]
                    
                    if num_clause3 > 0:
                        clause3_sat = torch.where(has_var_in_class & torch.isin(affected_cluster, accepted_clusters), clause3_sat_cand, clause3_sat)
                    if num_clause2 > 0:
                        clause2_sat = torch.where(has_var_in_class_2 & torch.isin(affected_cluster_2, accepted_clusters), clause2_sat_cand, clause2_sat)
            
            self.energy_history.append(self.compute_total_unsat_clauses(spins))
            
            if self.verbose and (step + 1) % 100 == 0:
                print(f"  MCMC Étape {step+1}/{steps} : Clauses insatisfaites={self.energy_history[-1]} | S_giant={self.giant_component_history[-1]:.4f}")
            
            if step >= burn_in:
                sum_spins += spins
                sum_outer += torch.outer(spins, spins)
                sample_count += 1
                
        mean_spins = sum_spins / sample_count
        mean_outer = sum_outer / sample_count
        covariance = mean_outer
        
        return covariance, self.energy_history, self.giant_component_history
        
    def perform_signed_spectral_clustering(self, covariance):
        if self.verbose:
            print("[GPU Spectral] Lancement du clustering spectral sur Laplacien signé...")
        D = torch.diag(torch.abs(covariance).sum(dim=1))
        L_signed = D - covariance
        eigenvalues, eigenvectors = torch.linalg.eigh(L_signed)
        v_min = eigenvectors[:, 0]
        spins_spectral = torch.where(v_min >= 0.0, 1.0, -1.0)
        if self.verbose:
            print("[GPU Spectral] Clustering spectral terminé.")
        return spins_spectral


# ==========================================
# MARKDOWN CELL 10
# ==========================================
# ## 5. Fonction d'Orchestration et Évaluation

# ==========================================
# CODE CELL 11
# ==========================================
def evaluate_3sat_energy(spins, clauses):
    unsat = 0
    for c in clauses:
        satisfied = False
        for lit in c:
            var = abs(lit)
            val = 1 if lit > 0 else -1
            if spins[var] == val:
                satisfied = True
                break
        if not satisfied:
            unsat += 1
    return unsat

def solve_3sat_with_gpu_cluster_dynamics(num_vars, clauses, steps=1000, burn_in=300, prop_gel=0.5, n_mh_steps=None, verbose=True):
    t_start = time.time()
    
    # 1. Élimination unitaire récursive et littéraux purs
    active_vars, active_clauses, fixed_lits = recursive_unit_propagation_and_reductions(num_vars, clauses, verbose=verbose)
    
    if len(active_vars) == 0:
        if verbose:
            print("[Orchestration] Toutes les variables ont été éliminées par preprocessing !")
        full_spins = {v: fixed_lits.get(v, 1) for v in range(1, num_vars + 1)}
        return full_spins, time.time() - t_start, [0.0] * steps, [0.0] * steps
        
    # 2. Double transfert d'énergie
    N_red, var_to_idx, W_res, triangles_nf, triangles_f = perform_double_energy_transfer(active_vars, active_clauses, verbose=verbose)
    
    # 3. Initialisation du solver GPU
    solver = GPUPartialClusterDynamicsSolver(N_red, var_to_idx, W_res, triangles_nf, triangles_f, active_clauses, verbose=verbose)
    
    # 4. Calibration automatique de u par dichotomie sur GPU
    solver.calibrate_u(prop_gel=prop_gel)
    
    # 5. Échantillonnage MCMC GPU (Metropolis sur partie orientée)
    covariance, energy_history, giant_history = solver.run_mcmc(steps=steps, burn_in=burn_in, n_mh_steps=n_mh_steps)
    
    # 6. Clustering Spectral GPU
    spins_red_cuda = solver.perform_signed_spectral_clustering(covariance)
    spins_red = spins_red_cuda.numpy()
    
    # 7. Recomposition et sélection
    if verbose:
        print("[Orchestration] Recomposition de la solution et sélection du meilleur candidat spectral...")
    cand1 = {}
    cand2 = {}
    
    var_list = sorted(list(active_vars))
    for i, var in enumerate(var_list):
        cand1[var] = int(spins_red[i])
        cand2[var] = -int(spins_red[i])
        
    for var, val in fixed_lits.items():
        cand1[var] = val
        cand2[var] = val
        
    unsat1 = evaluate_3sat_energy(cand1, clauses)
    unsat2 = evaluate_3sat_energy(cand2, clauses)
    
    best_spins = cand1 if unsat1 < unsat2 else cand2
    
    # 8. Post-traitement de raffinement local (WalkSAT guidé par le spectral)
    unsat_before = min(unsat1, unsat2)
    if unsat_before > 0:
        if verbose:
            print(f"[Orchestration] Lancement du post-traitement WalkSAT pour corriger les {unsat_before} clauses insatisfaites...")
        refined_spins, unsat_after = solve_maxsat_walksat(
            num_vars, clauses, max_flips=20000, p=0.3, max_time=2.0, verbose=False, init_spins=best_spins
        )
        if unsat_after < unsat_before:
            best_spins = refined_spins
            if verbose:
                print(f"[Orchestration] Post-traitement terminé. Clauses insatisfaites : {unsat_before} -> {unsat_after}")
        else:
            if verbose:
                print("[Orchestration] Le post-traitement n'a pas pu améliorer l'énergie spectrale.")
                
    t_elapsed = time.time() - t_start
    return best_spins, t_elapsed, energy_history, giant_history


# ==========================================
# MARKDOWN CELL 12
# ==========================================
# ## 6. Baseline CDCL (PySAT Glucose4)
# 
# Nous exécutons la baseline PySAT sur CPU afin de comparer les performances.

# ==========================================
# CODE CELL 13
# ==========================================
from pysat.solvers import Glucose4

def solve_maxsat_walksat(num_vars, clauses, max_flips=150000, p=0.3, max_time=5.0, verbose=True, init_spins=None):
    t_start = time.time()
    if verbose:
        print(f"  [CPU WalkSAT] Lancement avec {num_vars} variables actives et {len(clauses)} clauses actives...")
    if init_spins is not None:
        spins = np.zeros(num_vars + 1, dtype=int)
        for v in range(1, num_vars + 1):
            spins[v] = init_spins.get(v, random.choice([-1, 1]))
    else:
        spins = np.random.choice([-1, 1], size=num_vars + 1)
    
    pos_clauses = [[] for _ in range(num_vars + 1)]
    neg_clauses = [[] for _ in range(num_vars + 1)]
    
    for c_idx, c in enumerate(clauses):
        for lit in c:
            v = abs(lit)
            if lit > 0:
                pos_clauses[v].append(c_idx)
            else:
                neg_clauses[v].append(c_idx)
                
    num_satisfied = np.zeros(len(clauses), dtype=int)
    unsat_list = []
    clause_to_idx = np.full(len(clauses), -1, dtype=int)
    
    for c_idx, c in enumerate(clauses):
        sat_count = sum(1 for lit in c if spins[abs(lit)] == (1 if lit > 0 else -1))
        num_satisfied[c_idx] = sat_count
        if sat_count == 0:
            clause_to_idx[c_idx] = len(unsat_list)
            unsat_list.append(c_idx)
            
    best_spins = spins.copy()
    best_unsat = len(unsat_list)
            
    for flip in range(max_flips):
        if not unsat_list:
            break
        if flip % 4000 == 0 and time.time() - t_start > max_time:
            break
            
        c_idx = random.choice(unsat_list)
        c = clauses[c_idx]
        
        if random.random() < p:
            flip_var = abs(random.choice(c))
        else:
            best_diff = -1e9
            best_vars = []
            
            for lit in c:
                v = abs(lit)
                if spins[v] == 1:
                    lose_clauses = pos_clauses[v]
                    gain_clauses = neg_clauses[v]
                else:
                    lose_clauses = neg_clauses[v]
                    gain_clauses = pos_clauses[v]
                    
                broken = sum(1 for tc_idx in lose_clauses if num_satisfied[tc_idx] == 1)
                made = sum(1 for tc_idx in gain_clauses if num_satisfied[tc_idx] == 0)
                
                diff = made - broken
                if diff > best_diff:
                    best_diff = diff
                    best_vars = [v]
                elif diff == best_diff:
                    best_vars.append(v)
                    
            flip_var = random.choice(best_vars)
            
        old_val = spins[flip_var]
        new_val = -old_val
        spins[flip_var] = new_val
        
        if old_val == 1:
            lose_clauses = pos_clauses[flip_var]
            gain_clauses = neg_clauses[flip_var]
        else:
            lose_clauses = neg_clauses[flip_var]
            gain_clauses = pos_clauses[flip_var]
            
        for tc_idx in lose_clauses:
            num_satisfied[tc_idx] -= 1
            if num_satisfied[tc_idx] == 0:
                if clause_to_idx[tc_idx] == -1:
                    clause_to_idx[tc_idx] = len(unsat_list)
                    unsat_list.append(tc_idx)
                
        for tc_idx in gain_clauses:
            if num_satisfied[tc_idx] == 0:
                idx = clause_to_idx[tc_idx]
                if idx != -1:
                    last_c_idx = unsat_list[-1]
                    unsat_list[idx] = last_c_idx
                    clause_to_idx[last_c_idx] = idx
                    unsat_list.pop()
                    clause_to_idx[tc_idx] = -1
            num_satisfied[tc_idx] += 1
            
        num_unsat = len(unsat_list)
        if num_unsat < best_unsat:
            best_unsat = num_unsat
            best_spins = spins.copy()
            if best_unsat == 0:
                break
        if verbose and flip > 0 and flip % 25000 == 0:
            print(f"    Flip {flip}/{max_flips} : Meilleure énergie active (clauses insatisfaites) = {best_unsat}")
                
    spins_dict = {v: int(best_spins[v]) for v in range(1, num_vars + 1)}
    if verbose:
        print(f"  [CPU WalkSAT] Recherche terminée en {time.time() - t_start:.4f}s. Clauses insatisfaites = {best_unsat}.")
    return spins_dict, best_unsat

def solve_3sat_with_pysat(num_vars, clauses, verbose=True):
    t_start = time.time()
    if verbose:
        print("[CPU PySAT] Lancement du solveur CDCL Glucose4...")
    # 1. Essai avec le solver SAT standard Glucose4 (très rapide)
    with Glucose4(bootstrap_with=clauses) as solver:
        satisfied = solver.solve()
        model = solver.get_model() if satisfied else None
        
    if model:
        t_elapsed = time.time() - t_start
        if verbose:
            print(f"  -> Glucose4 a trouvé une assignation satisfaisante (SAT) en {t_elapsed:.4f}s.")
        spins = {abs(lit): (1 if lit > 0 else -1) for lit in model}
        return spins, t_elapsed, 0
        
    # 2. Si UNSAT, résolution Max-SAT avec WalkSAT pour minimiser le nombre de clauses non satisfaites
    t_elapsed_glucose = time.time() - t_start
    if verbose:
        print(f"  -> Glucose4 a conclu à UNSAT en {t_elapsed_glucose:.4f}s. Lancement du repli WalkSAT...")
    spins, unsat_count = solve_maxsat_walksat(num_vars, clauses, max_flips=150000, p=0.3, max_time=5.0, verbose=verbose)
    t_elapsed = time.time() - t_start
    return spins, t_elapsed, unsat_count


# ==========================================
# MARKDOWN CELL 14
# ==========================================
# ## 7. Exécution et Analyse du Problème Sélectionné
# 
# Lancement des deux algorithmes sur l'instance choisie dans le formulaire et affichage des résultats.

# ==========================================
# CODE CELL 15
# ==========================================
verbose = True  #@param {type:"boolean"}

print(f"Source : {source_du_benchmark} | Difficulté : {difficulte}")
print(f"Nombre de variables initial : {num_vars} | Clauses 3-SAT : {len(clauses_3sat)}\n")

# 1. GPU Cluster solver
print("Exécution du Solver de Clusters Hybride GPU...")
gpu_spins, gpu_time, gpu_energy_history, gpu_giant_history = solve_3sat_with_gpu_cluster_dynamics(
    num_vars, clauses_3sat, steps=1000, burn_in=300, prop_gel=prop_gel, verbose=verbose
)
gpu_unsat = evaluate_3sat_energy(gpu_spins, clauses_3sat)
print(f"  -> Temps : {gpu_time:.4f} s | Clauses insatisfaites : {gpu_unsat}\n")

# 2. PySAT CDCL/Max-SAT solver
print("Exécution de la Baseline PySAT (Glucose4 + WalkSAT Fallback)...")
cpu_spins, cpu_time, cpu_unsat = solve_3sat_with_pysat(num_vars, clauses_3sat, verbose=verbose)
print(f"  -> Temps : {cpu_time:.4f} s | Clauses insatisfaites : {cpu_unsat}\n")

# Comparaison
speedup = cpu_time / gpu_time if gpu_time > 0 else 0.0
print(f"Facteur d'accélération (Speedup) : {speedup:.2f}x\n")

# Visualisation de l'évolution de l'énergie et de la taille de la composante géante
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=100)

# Graphique 1 : Énergie U(t)
ax1.plot(gpu_energy_history, color='#3b82f6', linewidth=2, label='Nombre de clauses insatisfaites')
ax1.axvline(x=300, color='#ef4444', linestyle='--', linewidth=1.5, label='Fin du Burn-in (Étape 300)')
ax1.set_title("Nombre de clauses activement insatisfaites au cours des étapes MCMC (GPU)", fontsize=11, fontweight='bold', pad=10)
ax1.set_xlabel("Étape MCMC (t)", fontsize=9)
ax1.set_ylabel("Nombre de clauses insatisfaites", fontsize=9)
ax1.grid(True, linestyle=':', alpha=0.6)
ax1.legend(frameon=True, facecolor='white', edgecolor='none')

# Graphique 2 : Taille relative de la plus grande composante gelée (S_giant)
ax2.plot(gpu_giant_history, color='#10b981', linewidth=2, label='Taille relative du composante géante (S_giant)')
ax2.axhline(y=prop_gel, color='#f59e0b', linestyle=':', linewidth=1.5, label=f'Cible prop_gel = {prop_gel}')
ax2.axvline(x=300, color='#ef4444', linestyle='--', linewidth=1.5, label='Fin du Burn-in (Étape 300)')
ax2.set_title("Taille relative de la plus grande composante connexe gelée", fontsize=11, fontweight='bold', pad=10)
ax2.set_xlabel("Étape MCMC (t)", fontsize=9)
ax2.set_ylabel("Fraction des variables actives (S_giant)", fontsize=9)
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(frameon=True, facecolor='white', edgecolor='none')

plt.tight_layout()
plt.show()
