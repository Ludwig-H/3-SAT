import os
import sys
import time
import random
import numpy as np
from pysat.solvers import Glucose4

# Add the workspace root to sys.path to allow importing from MCMCHigherOrder
sys.path.append("/workspaces/3-SAT")

from MCMCHigherOrder.mcmc_higher_order import (
    solve_3sat_mcmc_higher_order,
    count_unsat_clauses
)

BENCHMARKS_DIR = "/workspaces/3-SAT/benchmarks"

KISSAT_BENCHMARKS = {
    "xor6": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/xor6.cnf",
    "ph6": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/ph6.cnf",
    "miter1": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/miter1.cnf",
    "add32": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/add32.cnf",
    "prime169": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/prime169.cnf",
    "add64": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/add64.cnf",
    "add128": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/add128.cnf",
    "prime841": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/prime841.cnf",
    "sqrt10609": "https://raw.githubusercontent.com/arminbiere/kissat/master/test/cnf/sqrt10609.cnf"
}

def generate_miter_circuit_3sat(n_inputs=15, n_gates=60, diff="Facile", seed=42):
    random.seed(seed)
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
                
    miter_out = next_var
    clauses.append([-output1, -output2, -miter_out])
    clauses.append([output1, output2, -miter_out])
    clauses.append([-output1, output2, miter_out])
    clauses.append([output1, -output2, miter_out])
    clauses.append([miter_out])
    
    return convert_to_3sat(miter_out, clauses)

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

def parse_dimacs_file(filepath):
    clauses = []
    num_vars = 0
    current_clause = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
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

def run_walksat(initial_spins, clauses, num_vars, max_flips=300000, p=0.3, max_time=10.0, target_unsat=0, seed=42):
    random.seed(seed)
    t_start = time.time()
    spins = np.zeros(num_vars + 1, dtype=int)
    for v in range(1, num_vars + 1):
        if initial_spins is None or v not in initial_spins:
            spins[v] = random.choice([-1, 1])
        else:
            spins[v] = initial_spins[v]
        
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
            
    init_unsat = len(unsat_list)
    if init_unsat <= target_unsat:
        return {v: int(spins[v]) for v in range(1, num_vars + 1)}, init_unsat, time.time() - t_start, 0
        
    best_unsat = init_unsat
    best_spins = spins.copy()
    
    flips_done = 0
    for flip in range(1, max_flips + 1):
        flips_done = flip
        if not unsat_list or len(unsat_list) <= target_unsat:
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
            if best_unsat <= target_unsat:
                break
                
    t_elapsed = time.time() - t_start
    best_spins_dict = {v: int(best_spins[v]) for v in range(1, num_vars + 1)}
    return best_spins_dict, best_unsat, t_elapsed, flips_done

def solve_with_glucose(num_vars, clauses):
    t_start = time.time()
    with Glucose4(bootstrap_with=clauses) as solver:
        satisfied = solver.solve()
    t_elapsed = time.time() - t_start
    return "SAT" if satisfied else "UNSAT", t_elapsed

def solve_maxsat_with_rc2(num_vars, clauses):
    t_start = time.time()
    if len(clauses) > 3000:
        return "Skip", 0.0, -1
    from pysat.examples.rc2 import RC2
    from pysat.formula import WCNF
    wcnf = WCNF()
    for c in clauses:
        wcnf.append(c, weight=1)
    try:
        with RC2(wcnf) as rc2:
            model = rc2.compute()
            t_elapsed = time.time() - t_start
            if model is not None:
                opt_unsat = rc2.cost
                return f"OPT: {opt_unsat}", t_elapsed, opt_unsat
    except Exception:
        pass
    return "Error", time.time() - t_start, -1

def run_all_benchmarks():
    bench_list = []
    
    # 1. Kissat CNF files
    for name in KISSAT_BENCHMARKS.keys():
        filepath = os.path.join(BENCHMARKS_DIR, f"{name}.cnf")
        if os.path.exists(filepath):
            n_vars, clauses = parse_dimacs_file(filepath)
            n_vars_3sat, clauses_3sat = convert_to_3sat(n_vars, clauses)
            bench_list.append((name, n_vars_3sat, clauses_3sat))
            
    # 2. Circuit Miters
    bench_list.append(("Miter_Small", *generate_miter_circuit_3sat(10, 40, "Facile", seed=1)))
    bench_list.append(("Miter_Medium", *generate_miter_circuit_3sat(30, 150, "Moyen", seed=2)))
    bench_list.append(("Miter_Large", *generate_miter_circuit_3sat(50, 300, "Difficile", seed=3)))
    bench_list.append(("Miter_Huge", *generate_miter_circuit_3sat(80, 500, "Très difficile", seed=4)))
    
    markdown_lines = []
    markdown_lines.append("# Rapport de Performance: Solveur MCMC Higher-Order pour 3-SAT\n")
    markdown_lines.append("Ce tableau présente les performances du nouveau solveur MCMC **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).\n")
    markdown_lines.append("L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation MCMC higher-order (warm-start) par rapport à un départ aléatoire (random-start).\n")
    
    headers = [
        "Instance",
        "CDCL (Glucose4)",
        "MaxSAT (RC2)",
        "WalkSAT Pur (Target=0)",
        "MCMC HO Seul",
        "MCMC HO + WalkSAT (Target=0)",
        "WalkSAT Pur (Ciblant MCMC HO Unsat)",
        "Flips Gagnés (%)"
    ]
    
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    markdown_lines.append(header_row)
    markdown_lines.append(separator_row)
    
    for name, n_vars, clauses in bench_list:
        n_clauses = len(clauses)
        print(f"\n--- Évaluation de {name} ({n_vars} variables, {n_clauses} clauses) ---")
        
        # 1. Glucose4
        glu_res, t_glu = solve_with_glucose(n_vars, clauses)
        print(f"Glucose4: {glu_res} en {t_glu:.4f}s")
        
        # 2. RC2 MaxSAT (Exact)
        rc2_res, t_rc2, rc2_unsat = solve_maxsat_with_rc2(n_vars, clauses)
        print(f"RC2 MaxSAT: {rc2_res} en {t_rc2:.4f}s")
        
        # 3. WalkSAT Pur (Target=0)
        _, pure_zero_unsat, t_pure_zero, flips_pure_zero = run_walksat(None, clauses, n_vars, max_flips=300000, target_unsat=0, max_time=10.0)
        print(f"WalkSAT Pur (Target=0): Unsat = {pure_zero_unsat} en {t_pure_zero:.4f}s ({flips_pure_zero} flips)")
        
        # 4. MCMC HO Seul
        ho_spins, t_ho, ho_unsat = solve_3sat_mcmc_higher_order(n_vars, clauses, max_sweeps=300, u_sat=1.0)
        print(f"MCMC HO Seul: Unsat = {ho_unsat} en {t_ho:.4f}s")
        
        # 5. MCMC HO + WalkSAT
        ho_walk_spins, ho_walk_unsat, t_ho_walk, flips_ho_walk = run_walksat(ho_spins, clauses, n_vars, max_flips=300000, target_unsat=0, max_time=10.0)
        t_total_ho_walk = t_ho + t_ho_walk
        print(f"MCMC HO + WalkSAT: Unsat = {ho_walk_unsat} en {t_total_ho_walk:.4f}s (WalkSAT: {t_ho_walk:.4f}s, {flips_ho_walk} flips)")
        
        # 6. Pure WalkSAT targeting MCMC HO Unsat
        _, pure_target_unsat, t_pure_target, flips_pure_target = run_walksat(None, clauses, n_vars, max_flips=300000, target_unsat=ho_unsat, max_time=10.0)
        print(f"WalkSAT Pur (Ciblant {ho_unsat} unsat): Unsat = {pure_target_unsat} en {t_pure_target:.4f}s ({flips_pure_target} flips)")
        
        # Calculate iteration/flip savings (if targeting 0)
        # We compare flips of Pure WalkSAT (Target=0) vs. (MCMC HO + WalkSAT)
        if flips_pure_zero > 0:
            flips_saved_pct = ((flips_pure_zero - flips_ho_walk) / flips_pure_zero) * 100.0
            flips_saved_str = f"{flips_saved_pct:.1f}%"
        else:
            flips_saved_str = "0.0%"
            
        # Format table cells
        cell_instance = f"**{name}**<br>({n_vars} vars, {n_clauses} clauses)"
        cell_cdcl = f"{glu_res}<br>{t_glu:.4f}s"
        cell_rc2 = f"OPT Unsat: {rc2_unsat}<br>{t_rc2:.4f}s" if rc2_unsat >= 0 else "Skipped"
        cell_pure_zero = f"Unsat: {pure_zero_unsat}<br>{t_pure_zero:.4f}s<br>({flips_pure_zero} flips)"
        cell_ho = f"Unsat: {ho_unsat}<br>{t_ho:.4f}s"
        cell_ho_walk = f"Unsat: {ho_walk_unsat}<br>**{t_total_ho_walk:.4f}s**<br>({flips_ho_walk} flips)"
        cell_pure_target = f"Unsat: {pure_target_unsat}<br>{t_pure_target:.4f}s<br>({flips_pure_target} flips)"
        
        row_str = f"| {cell_instance} | {cell_cdcl} | {cell_rc2} | {cell_pure_zero} | {cell_ho} | {cell_ho_walk} | {cell_pure_target} | {flips_saved_str} |"
        markdown_lines.append(row_str)
        
    report_content = "\n".join(markdown_lines)
    print("\n=== RAPPORT DES BENCHMARKS ===")
    print(report_content)
    
    # Save the report to a markdown file
    report_path = "/workspaces/3-SAT/MCMCHigherOrder/benchmark_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"\nRapport écrit avec succès dans {report_path} !")

if __name__ == "__main__":
    run_all_benchmarks()
