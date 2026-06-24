# Solveur Spectral Signé pour le Problème 3-SAT

Ce dossier contient la formulation théorique et l'implémentation d'un solveur pour le problème 3-SAT basé sur le **clustering spectral signé**.

Contrairement aux approches hybrides standard, l'idée ici est d'**éliminer totalement la partie orientée**. Grâce à l'introduction systématique de variables auxiliaires et à leur couplage rigoureux, le problème combinatoire 3-SAT est encodé sous forme d'un **graphe pondéré signé quadratique** sur l'ensemble des variables d'origine, d'un spin de référence $T$ (fixé à $+1$) et de spins auxiliaires.

---

## 1. Modélisation Mathématique de l'Encodage

Soit une formule SAT contenant $N$ variables $x_1, \dots, x_N$ et un ensemble de clauses $\mathcal{C}$ de poids $u > 0$. Les variables de spins d'origine sont $\sigma_i \in \{-1, +1\}$. Le spin de référence $T \in \{-1, +1\}$ est fixé à $+1$.
La valeur du littéral orienté est $L_i = \eta_i \sigma_i T$, où $\eta_i \in \{-1, +1\}$ est la polarité du littéral.

L'énergie exacte d'insatisfaction vaut :

### A. Clauses de taille 1 (Unitaires)
$$E_1 = u\left(1 - \mathbf{1}_{L_1=1}\right) = \frac{u}{2} - \frac{u}{2} L_1$$
Elle s'encode par **une seule arête** :
* Entre la variable $x_1$ et $T$, de signe $\eta_1$ et de poids $u$.

### B. Clauses de taille 2 (Binaires)
$$E_2 = u\left(1 - \mathbf{1}_{L_1=1 \text{ ou } L_2=1}\right) = \frac{u}{4}\left(1 - L_1 - L_2 + L_1 L_2\right)$$
Elle s'encode exactement par **3 arêtes signées directes** sur les nœuds $\{x_1, x_2, T\}$ :
1. Une arête entre $x_1$ et $T$ de signe $\eta_1$, de poids $u/2$.
2. Une arête entre $x_2$ et $T$ de signe $\eta_2$, de poids $u/2$.
3. Une arête entre $x_1$ et $x_2$ de signe $-\eta_1 \eta_2$, de poids $u/2$.

### C. Clauses de taille 3 (Ternaires)
Nous introduisons un **spin auxiliaire $s_a \in \{-1, +1\}$** qui agit comme un certificat local de satisfaction :
$$E_3(\sigma, s_a) = \frac{u}{4}\left[ (1 - L_1) + (1 - L_2) + (1 - L_3) + (1 - s_a L_1) + (1 - s_a L_2) + (1 - s_a L_3) + (1 + s_a) \right] + \frac{u}{4}(L_1 L_2 + L_2 L_3 + L_1 L_3) - \frac{5}{4}u$$
Après minimisation sur $s_a \in \{-1, 1\}$, l'énergie vaut $0$ si la clause est satisfaite, et $u$ si elle ne l'est pas.
Elle s'encode par **10 arêtes signées (chacune de poids $u/2$)** reliant les nœuds $\{x_1, x_2, x_3, s_a, T\}$ :
1. **3 arêtes variables-référence $(x_i, T)$** : signe $\eta_i$, poids $u/2$.
2. **3 arêtes auxiliaire-variables $(s_a, x_i)$** : signe $\eta_i$, poids $u/2$.
3. **1 arête auxiliaire-référence $(s_a, T)$** : signe $-1$ (antiferromagnétique), poids $u/2$.
4. **3 arêtes quadratiques entre les variables d'origine $(x_i, x_j)$** : signe $-\eta_i \eta_j$, poids $u/2$.

---

## 2. Contraction des Nœuds Auxiliaires et Évitement de la Sur-contrainte Transitive

Dans la théorie initiale, si deux clauses ternaires $a$ et $b$ partagent une même paire orientée de littéraux, on cherche à forcer $s_a = s_b$ en les reliant par une arête ferromagnétique dure de poids géant ($100\,000 \cdot u$) ou en les contractant.

### A. Le Piège de la Sur-contrainte Transitive
Si l'on contracte les variables auxiliaires dès qu'elles partagent **au moins une** paire orientée commune, on crée une sur-contrainte transitive destructrice :
* Si la clause $i$ partage la paire $P_1$ avec la clause $j$ ($s_i \approx s_j$), et partage la paire $P_2$ avec la clause $k$ ($s_i \approx s_k$).
* Cela force transitivement $s_j \approx s_k$, alors même que les clauses $j$ et $k$ ne partagent aucune paire.
Comme chaque clause ternaire possède 3 paires, cette relation d'équivalence transitive va rapidement fusionner presque toutes les variables auxiliaires du graphe en un nombre très réduit de composants géants de valeurs identiques. Cela détruit le rôle de certificat local des variables auxiliaires et dégrade fortement la résolution.

### B. La Solution : Contraction par Paire Canonique Unique
Pour éliminer ce problème, nous définissons pour chaque clause ternaire une **paire canonique unique** (par exemple en triant les littéraux par index de variables et en sélectionnant les deux premiers). 

Nous n'effectuons la contraction ($s_i \approx s_j$) **que si et seulement si** les clauses partagent la **même paire canonique unique**. Cela garantit :
* Une affectation stricte et non ambiguë de chaque variable auxiliaire à un certificat de paire spécifique.
* L'absence totale de liens transitifs indésirables entre des paires différentes.
* Le maintien de la structure locale du problème combinatoire CNF.

---

## 3. Optimisation de la Résolution Spectrale : Calcul Ciblé ($k=1$)

Le calcul complet de tous les vecteurs propres d'une matrice $N \times N$ est une opération très lourde ($\mathcal{O}(N^3)$). Or, le problème ne requiert que le vecteur propre correspondant à la plus petite valeur propre. Nous utilisons donc des algorithmes itératifs hautement optimisés pour cibler uniquement le premier vecteur propre ($k=1$).

### A. Résolution sur CPU (SciPy Lanczos)
Nous convertissons le Laplacien signé en une matrice creuse et utilisons le solveur de Lanczos de SciPy :
```python
scipy.sparse.linalg.eigsh(L, k=1, sigma=-1e-5, which='LM')
```
L'utilisation du mode *shift-invert* (`sigma=-1e-5`, `which='LM'`) permet de cibler directement et de manière très stable la valeur propre la plus proche de 0 (qui est la plus petite). Cette méthode s'exécute en temps quasi-linéaire sur des matrices creuses.

### B. Résolution sur GPU (PyTorch LOBPCG)
Si un GPU est disponible, nous utilisons l'algorithme LOBPCG (Locally Optimal Block Preconditioned Conjugate Gradient) via PyTorch :
```python
torch.lobpcg(L_cuda, k=1, largest=False, X=X)
```
Cet algorithme itératif est spécialement conçu pour trouver les plus petites valeurs propres de grandes matrices symétriques sur GPU avec un coût mémoire et de calcul minimal.

### C. Choix du Laplacien
* **Laplacien Signé Combinatoire (Par défaut)** :
  $$L_{\text{comb}} = D - A$$
* **Laplacien Signé Normalisé (Optionnel)** :
  $$L_{\text{norm}} = D^{-1/2} L D^{-1/2}$$

---

## 4. Phase de Recherche Locale WalkSAT (Optionnelle, désactivée par défaut)

Dans la phase actuelle de test, la recherche locale WalkSAT (post-processing / hybridation) est **désactivée par défaut** (`run_local_search=False`) afin d'étudier la performance brute de la réduction spectrale.

Lorsqu'elle est activée, elle utilise la solution spectrale comme **warm-start** pour guider WalkSAT. Sur les instances satisfaisables, cela réduit le nombre de flips requis pour converger vers une solution SAT d'un facteur 10x à 20x par rapport à une initialisation aléatoire.
