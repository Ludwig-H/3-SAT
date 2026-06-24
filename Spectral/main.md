# Solveur Spectral Signé pour le Problème 3-SAT

Ce dossier contient la formulation théorique et l'implémentation d'un solveur pour le problème 3-SAT basé sur le **clustering spectral signé**. 

Contrairement aux approches hybrides (qui conservent une partie orientée dans le Hamiltonien traitée par Metropolis-Hastings), l'idée ici est d'**éliminer totalement la partie orientée**. Grâce à l'introduction systématique de variables auxiliaires et à leur couplage rigoureux, la totalité du problème combinatoire 3-SAT est encodée sous forme d'un **graphe pondéré signé quadratique** sur l'ensemble des variables d'origine, d'un spin de référence $T$ (fixé à $+1$ après jauge) et de spins auxiliaires.

---

## 1. Modélisation Mathématique de l'Encodage

Soit une formule SAT contenant $N$ variables $x_1, \dots, x_N$ et un ensemble de clauses $\mathcal{C}$ de poids $u > 0$. Les variables de spins d'origine sont $\sigma_i \in \{-1, +1\}$. Le spin de référence est $T \in \{-1, +1\}$ (fixé à $+1$ après jauge).

Pour chaque littéral d'une clause, on note sa polarité $\eta \in \{-1, +1\}$ ($\eta = 1$ s'il est positif, $\eta = -1$ s'il est négatif). La valeur du littéral orienté est $L_i = \eta_i \sigma_i T$.

### A. Clauses de taille 1 (Unitaires)
Une clause unitaire $L_1$ de poids $u$ impose $L_1 = 1$. L'énergie d'insatisfaction vaut :
$$E_1 = u\left(1 - \mathbf{1}_{L_1=1}\right) = \frac{u}{2} - \frac{u}{2}\eta_1 \sigma_1 T$$
À constante d'énergie près, elle s'encode par **une seule arête** :
* Entre la variable $x_1$ et $T$, de signe $\eta_1$ et de poids $u$.

### B. Clauses de taille 2 (Binaires)
Une clause binaire $L_1 \lor L_2$ de poids $u$ est insatisfaite uniquement si $L_1 = L_2 = -1$. L'énergie associée s'écrit de façon exacte sous forme quadratique :
$$E_2 = u\left(1 - \mathbf{1}_{L_1=1 \text{ ou } L_2=1}\right) = u\left(\frac{1}{4} - \frac{L_1}{4} - \frac{L_2}{4} + \frac{L_1 L_2}{4}\right)$$
En développant en spins, on obtient :
$$E_2 \equiv -\frac{u}{4}\eta_1 \sigma_1 T - \frac{u}{4}\eta_2 \sigma_2 T + \frac{u}{4}\eta_1\eta_2 \sigma_1 \sigma_2$$
À constante près, elle s'encode exactement par **3 arêtes signées directes (chacune de poids $u/2$)** sur les nœuds $\{x_1, x_2, T\}$ :
1. Une arête entre $x_1$ et $T$ de signe $\eta_1$.
2. Une arête entre $x_2$ et $T$ de signe $\eta_2$.
3. Une arête entre $x_1$ et $x_2$ de signe $-\eta_1 \eta_2$ (antiferromagnétique relative au produit des polarités).

### C. Clauses de taille 3 (Ternaires)
Une clause ternaire $L_1 \lor L_2 \lor L_3$ de poids $u$ est insatisfaite si $L_1 = L_2 = L_3 = -1$.
Nous introduisons un **spin auxiliaire $s_a \in \{-1, +1\}$** qui agit comme un certificat local de satisfaction. L'énergie s'écrit sous forme de spins étendus :
$$E_3(\sigma, s_a) \equiv -\frac{u}{4}(L_1+L_2+L_3) - \frac{u}{4}s_a(L_1+L_2+L_3) + \frac{u}{4}s_a T + \frac{u}{4}(L_1 L_2 + L_2 L_3 + L_1 L_3)$$
Après minimisation sur $s_a$, on retrouve exactement l'énergie de la clause.
En spins, elle s'encode par **10 arêtes signées (toutes de poids $u/2$)** reliant les nœuds $\{x_1, x_2, x_3, s_a, T\}$ :
1. **3 arêtes variables-référence $(x_i, T)$** : signe $\eta_i$, poids $u/2$.
2. **3 arêtes auxiliaire-variables $(s_a, x_i)$** : signe $\eta_i$, poids $u/2$.
3. **1 arête auxiliaire-référence $(s_a, T)$** : signe $-1$ (antiferromagnétique), poids $u/2$.
4. **3 arêtes quadratiques entre les variables d'origine $(x_i, x_j)$** : signe $-\eta_i \eta_j$ (antiferromagnétiques relatives), poids $u/2$.

---

## 2. Mutualisation et Contraction des Auxiliaires

Si deux clauses ternaires $a$ et $b$ partagent une même paire orientée de littéraux (par exemple, $x_i = +$ et $x_j = +$), leurs spins auxiliaires correspondants $s_a$ et $s_b$ certifient le même état local.

Pour forcer ces deux variables à coïncider et à fusionner dans l'espace spectral, nous introduisons une **arête de contraction dure** :
* Une arête **ferromagnétique** ($+$) entre $s_a$ et $s_b$ de poids infini :
  $$W_{s_a s_b} = 100\,000 \cdot u$$

Cette arête force l'égalité $s_a \approx s_b$ dans la réduction spectrale. Cela permet notamment d'annuler automatiquement les forces opposées (par exemple, si la variable $z$ est attirée de manière ferromagnétique par $s_a$ et antiferromagnétique par $s_b$, les deux forces s'annulent de façon naturelle car les composantes correspondantes du vecteur propre convergent).

---

## 3. Résolution par Clustering Spectral Signé

Toutes les contributions d'arêtes sont sommées algébriquement pour former la matrice d'adjacence signée $A$ :
$$A_{ij} = \sum_{\text{arêtes } e=(i,j)} \operatorname{sign}(e) \cdot \operatorname{weight}(e)$$

On définit :
1. **La matrice de degrés signés $D$** (somme des valeurs absolues des poids) :
   $$D_{ii} = \sum_j |A_{ij}|$$
2. **Le Laplacien signé $L_{\text{signed}}$** :
   $$L_{\text{signed}} = D - A$$

Le problème de clustering signé se résout en trouvant le vecteur propre $v_{\text{min}}$ correspondant à la plus petite valeur propre de $L_{\text{signed}}$. 
Nous projetons ensuite les variables sur la configuration optimale $\sigma$ en alignant le signe par rapport à la référence $T$ (indexé à $0$) :
$$\sigma_i = \operatorname{sign}(v_{\text{min}}[i]) \cdot \operatorname{sign}(v_{\text{min}}[0])$$

Le solveur évalue $\sigma$ et son opposé $-\sigma$ sur la formule CNF initiale, et conserve le candidat qui minimise le nombre de clauses insatisfaites.
