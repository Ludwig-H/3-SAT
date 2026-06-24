import json
import os

def create_mcmc_notebook():
    mcmc_code_path = "/workspaces/3-SAT/MCMCHigherOrder/mcmc_higher_order.py"
    notebook_path = "/workspaces/3-SAT/MCMCHigherOrder/mcmc_higher_order.ipynb"
    
    # Read the mcmc_higher_order.py file
    if os.path.exists(mcmc_code_path):
        with open(mcmc_code_path, "r", encoding="utf-8") as f:
            mcmc_source_code = f.read()
    else:
        raise FileNotFoundError(f"Source file not found: {mcmc_code_path}")

    # Define cells
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Solveur MCMC Higher-Order pour 3-SAT\n",
                "\n",
                "Ce notebook implémente et évalue un solveur MCMC \"higher-order\" pour le problème 3-SAT, basé sur le document de spécification [main.md](file:///workspaces/3-SAT/MCMCHigherOrder/main.md).\n",
                "\n",
                "## 1. Principes Mathématiques et Algorithmiques\n",
                "L'approche MCMC Higher-Order conserve des spins discrets tout au long de la dynamique :\n",
                "1. **Graphe Signé Étendu** : Encodage exact des clauses unitaires, binaires et ternaires (avec des variables auxiliaires).\n",
                "2. **Compensation** : Fusion et compensation algébrique des poids signés d'arêtes opposées.\n",
                "3. **Transfert LP** : Résolution d'un programme linéaire pour maximiser le transfert d'énergie des arêtes vers les triangles.\n",
                "4. **Dynamique Swendsen-Wang Higher-Order** : Gel probabiliste des arêtes résiduelles et des triangles (frustrés et non frustrés).\n",
                "5. **Union-Find & Partitionnement** : Construction de clusters de spins cohérents, en fixant le cluster contenant le spin de référence $T$.\n",
                "6. **Problème Réduit sur Flips de Clusters** : Résolution locale (exacte ou via WalkSAT réduit) pour décider des flips de chaque cluster.\n",
                "7. **Réoptimisation locale des auxiliaires** et conservation de la meilleure configuration SAT globale."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "source": [
                "# Installation de python-sat si nécessaire\n",
                "!pip install -q python-sat"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Implémentation du Solveur MCMC Higher-Order\n",
                "Voici l'implémentation complète du solveur, lue directement depuis `mcmc_higher_order.py`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "source": [
                mcmc_source_code
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Évaluation sur une Instance de Circuit Miter\n",
                "Nous générons un problème 3-SAT de type Circuit Miter et lançons le solveur MCMC Higher-Order pour vérifier son bon fonctionnement."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "source": [
                "def convert_to_3sat(num_vars, clauses):\n",
                "    final_cnf = []\n",
                "    next_var = num_vars + 1\n",
                "    for c in clauses:\n",
                "        if len(c) <= 3:\n",
                "            final_cnf.append(c)\n",
                "        else:\n",
                "            curr = c\n",
                "            while len(curr) > 3:\n",
                "                aux = next_var\n",
                "                next_var += 1\n",
                "                final_cnf.append([curr[0], curr[1], aux])\n",
                "                curr = [-aux] + curr[2:]\n",
                "            final_cnf.append(curr)\n",
                "    return next_var - 1, final_cnf\n",
                "\n",
                "def generate_miter_circuit_3sat(n_inputs=15, n_gates=60, diff=\"Facile\", seed=42):\n",
                "    random.seed(seed)\n",
                "    clauses = []\n",
                "    next_var = n_inputs + 1\n",
                "    gates1 = []\n",
                "    gates2 = []\n",
                "    current_vars = list(range(1, n_inputs + 1))\n",
                "    for _ in range(n_gates):\n",
                "        gtype = random.choice([\"AND\", \"OR\", \"XOR\"])\n",
                "        in1 = random.choice(current_vars)\n",
                "        in2 = random.choice(current_vars)\n",
                "        out = next_var\n",
                "        next_var += 1\n",
                "        gates1.append((gtype, out, in1, in2))\n",
                "        current_vars.append(out)\n",
                "    output1 = current_vars[-1]\n",
                "    \n",
                "    n_mutations = 1 if diff == \"Facile\" else (2 if diff == \"Moyen\" else 4)\n",
                "    mutated_indices = set(random.sample(range(n_gates), min(n_mutations, n_gates)))\n",
                "    var_offset = next_var - (n_inputs + 1)\n",
                "    \n",
                "    for i, (gtype, out, in1, in2) in enumerate(gates1):\n",
                "        out2 = out + var_offset\n",
                "        in1_2 = in1 if in1 <= n_inputs else in1 + var_offset\n",
                "        in2_2 = in2 if in2 <= n_inputs else in2 + var_offset\n",
                "        if i in mutated_indices:\n",
                "            new_type = \"OR\" if gtype == \"AND\" else \"AND\"\n",
                "            gates2.append((new_type, out2, in1_2, in2_2))\n",
                "        else: \n",
                "            gates2.append((gtype, out2, in1_2, in2_2))\n",
                "            \n",
                "    output2 = current_vars[-1] + var_offset\n",
                "    next_var = output2 + 1\n",
                "    for g1, g2 in [(gates1, \"\"), (gates2, \"_2\")]:\n",
                "        for gtype, out, in1, in2 in g1:\n",
                "            if gtype == \"AND\":\n",
                "                clauses.append([in1, -out])\n",
                "                clauses.append([in2, -out])\n",
                "                clauses.append([-in1, -in2, out])\n",
                "            elif gtype == \"OR\":\n",
                "                clauses.append([-in1, out])\n",
                "                clauses.append([-in2, out])\n",
                "                clauses.append([in1, in2, -out])\n",
                "            elif gtype == \"XOR\":\n",
                "                clauses.append([-in1, -in2, -out])\n",
                "                clauses.append([in1, in2, -out])\n",
                "                clauses.append([-in1, in2, out])\n",
                "                clauses.append([in1, -in2, out])\n",
                "                \n",
                "    miter_out = next_var\n",
                "    clauses.append([-output1, -output2, -miter_out])\n",
                "    clauses.append([output1, output2, -miter_out])\n",
                "    clauses.append([-output1, output2, miter_out])\n",
                "    clauses.append([output1, -output2, miter_out])\n",
                "    clauses.append([miter_out])\n",
                "    return convert_to_3sat(miter_out, clauses)\n",
                "\n",
                "n_vars, clauses = generate_miter_circuit_3sat(12, 40, \"Facile\", seed=42)\n",
                "print(f\"Miter généré : {n_vars} variables, {len(clauses)} clauses.\")"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "source": [
                "best_spins, t_ho, ho_unsat = solve_3sat_mcmc_higher_order(n_vars, clauses, max_sweeps=100, verbose=True)\n",
                "print(f\"\\nRésultat MCMC Higher-Order Seul : {ho_unsat} clauses insatisfaites en {t_ho:.4f}s.\")"
            ]
        }
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1)
    print(f"Jupyter Notebook créé avec succès dans {notebook_path} !")

if __name__ == "__main__":
    create_mcmc_notebook()
