# Benchmarks Publics de Problèmes 3-SAT Réels (Industriels & Applicatifs)

Dans l'étude et la résolution pratique du problème 3-SAT, il est crucial de distinguer les instances **générées aléatoirement** (Random 3-SAT) des instances **issues d'applications réelles** (Industrial/Application 3-SAT). Les premières servent principalement aux études théoriques de transition de phase, tandis que les secondes possèdent une structure sous-jacente très riche (notamment une forte modularité) exploitée par les résolveurs modernes et les approches basées sur le clustering.

---

## 1. Origine et Encodage des Instances Réelles en 3-SAT

Les problèmes du monde réel ne sont généralement pas modélisés sous forme de 3-SAT pure à l'origine. Ils sont d'abord formulés sous forme de circuits logiques ou de formules CNF (Conjunctive Normal Form) générales avec des clauses de tailles arbitraires. 

Pour les évaluer avec un résolveur 3-SAT, on utilise des transformations préservant l'équisatisfaisabilité :
* **La Transformation de Tseitin** : Introduit des variables intermédiaires pour chaque porte d'un circuit logique, produisant des clauses de taille maximale 3 ou 4.
* **Réduction standard CNF $\rightarrow$ 3-SAT** : Les clauses de longueur $k > 3$ sont découpées en insérant des variables auxiliaires chaînées ($k-2$ clauses de taille 3).

> [!IMPORTANT]
> Contrairement aux instances aléatoires, cette étape de réduction préserve la structure modulaire locale (les communautés de variables), ce qui rend le clustering spectral particulièrement efficace sur ces instances.

---

## 2. Grandes Familles de Benchmarks Réels / Applicatifs

Les benchmarks applicatifs proviennent de compétitions internationales (comme la **SAT Competition**) ou de bibliothèques académiques. Les principales familles sont :

### A. Vérification de Matériel (Hardware Verification) & Bounded Model Checking (BMC)
* **Description** : Vérification de propriétés sur des circuits séquentiels (microprocesseurs, contrôleurs). On déroule les transitions d'états sur un horizon $K$ et on traduit le circuit sous forme de formule CNF.
* **Benchmarks clés** : 
  - Les instances issues de la suite d'outils **AIGER** (utilisées dans les compétitions de Model Checking HWMCC).
  - Les circuits de benchmark **ISCAS-85** et **ISCAS-89** (miters d'équivalence logique).

### B. Vérification de Logiciels (Software Verification)
* **Description** : Analyse statique de code source C/C++ ou Java via des outils comme **CBMC** (C Bounded Model Checker) pour détecter des dépassements de tampon, des pointeurs nuls ou des assertions fausses.
* **Benchmarks clés** :
  - La suite d'instances de la compétition de vérification de logiciels **SV-COMP**.

### C. Cryptanalyse (Cryptographic Attacks)
* **Description** : Attaques par force brute algébrique sur des chiffrements symétriques (calcul de clé à partir de paires clair/chiffré) ou attaques en pré-image sur des fonctions de hachage.
* **Benchmarks clés** :
  - **Chiffrements par flot** : Bivium, HiTag2, Grain.
  - **Chiffrements par bloc** : DES, AES (versions simplifiées ou à tours réduits).
  - **Fonctions de hachage** : Pré-images partielles de MD5, SHA-1 et SHA-256 (générées par des outils d'encodage comme *Transalg*).

### D. Planification et Ordonnancement (AI Planning & Scheduling)
* **Description** : Recherche d'un plan d'actions pour atteindre un objectif à partir d'un état initial dans des environnements contraints.
* **Benchmarks clés** :
  - Les instances **SATPlan** issues de la compétition internationale de planification (IPC - International Planning Competition).

---

## 3. Où Accéder à ces Benchmarks Publics ?

Plusieurs dépôts centralisent ces instances au format standard DIMACS CNF :

1. ** SAT Competition Archives (2002–2024)** :
   * C'est la référence absolue. Chaque année, la compétition publie des centaines de nouvelles instances réelles (Industrial Track).
   * **Accès public** : Dépôt global disponible sur **[Zenodo](https://doi.org/10.5281/zenodo.1147575)** (contient les jeux de données labellisés de toutes les compétitions passées).
   * **Site officiel** : [satcompetition.github.io](https://satcompetition.github.io/)

2. **SATLIB (The Satisfiability Library)** :
   * Bibliothèque historique très structurée contenant des sections dédiées aux applications réelles (BMC, planification, coloration de graphes réels).
   * **Accès public** : [www.satlib.org](http://www.satlib.org/)

3. **G4SATBench** :
   * Un benchmark récent (2023) conçu pour le Machine Learning sur graphes de formules SAT. Il contient plus de 100 000 formules industrielles parsées sous forme de graphes bipartis variables-clauses.
   * **Accès public** : Disponible sur GitHub via les publications de recherche sur l'apprentissage profond appliqué à SAT.

---

## 4. Comparaison Structurale : Aléatoire vs Réel

| Propriété | Random 3-SAT | Réel (Tseitin / Industrial) |
| :--- | :--- | :--- |
| **Graphe Variable-Clause** | Graphe biparti aléatoire (Erdős-Rényi-like) | Graphe à structure de communautés (Scale-free / Power-law) |
| **Modularité ($Q$)** | Très faible ($Q \approx 0$) | Très élevée ($Q \ge 0.7$) |
| **Variables auxiliaires** | Aucune | Nombreuses (définissant les portes intermédiaires) |
| **Efficacité du Clustering** | Inefficace (pas de partition naturelle) | **Trés efficace** (isole les composants fonctionnels du problème) |

---

## 5. État de l'Art et Baselines Implémentables en Python

Pour évaluer un nouveau résolveur sur ces benchmarks réels, deux approches de baselines (l'une pragmatique utilisant l'état de l'art, l'autre "from scratch" didactique) sont recommandées en Python :

### A. La Baseline État de l'Art Pragmatique : `PySAT` (CDCL)
Les résolveurs industriels modernes reposent sur l'architecture **CDCL** (*Conflict-Driven Clause Learning*), qui apprend des clauses de conflit lors des retours sur trace (*backtracking*). Il est inutile de réimplémenter un CDCL complexe en Python pur. 
* **Solution** : Utiliser la bibliothèque Python `pysat` (`pip install python-sat`), qui fournit des wrappers directs vers les solveurs C++ de l'état de l'art (comme **Glucose**, **MiniSat**, ou **Lingeling**).
* **Usage en Python** :
  ```python
  from pysat.solvers import Glucose3
  
  # Initialisation du solveur CDCL avec une liste de clauses
  with Glucose3(bootstrap_with=list_of_clauses) as solver:
      if solver.solve():
          print("SAT:", solver.get_model())
      else:
          print("UNSAT")
  ```

### B. La Baseline Algorithmique "From Scratch" : DPLL avec Heuristique MOMs
Si l'on souhaite implémenter soi-même un algorithme de résolution en Python pur (par exemple pour le comparer à la dynamique de clusters), un algorithme **DPLL** (*Davis-Putnam-Logemann-Loveland*) avec des optimisations structurelles est la baseline idéale :
1. **Propagation Unitaire (Unit Propagation)** : Essentielle pour les instances réelles (issues de Tseitin) qui comportent de longues chaînes d'implication logique.
2. **Élimination des Littéraux Purs (Pure Literal Elimination)** : Simplifie la formule en fixant les variables n'apparaissant que sous une seule polarité.
3. **Heuristique MOMs** (*Maximum Occurrence in clauses of Minimum size*) : Pour choisir la variable de branchement suivante. Elle calcule pour chaque variable $`x`$ un score basé sur sa fréquence dans les clauses de taille minimale non satisfaites :
   ```math
   f(x) = (n(x) + n(\neg x)) \cdot 2^k + n(x) \cdot n(\neg x)
   ```
   où $`n(x)`$ (resp. $`n(\neg x)`$) est le nombre d'occurrences du littéral dans les clauses les plus courtes, et $`k`$ est un paramètre de réglage. Cette heuristique est idéale pour le 3-SAT car elle cible spécifiquement les clauses de taille 2 (générées après instanciation d'une variable) pour forcer au plus vite des propagations unitaires et réduire l'arbre de recherche.
