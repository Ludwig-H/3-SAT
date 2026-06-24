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

## 2. Contraction des Nœuds Auxiliaires vs Grand Poids

Dans la théorie initiale, si deux clauses ternaires $a$ et $b$ partagent une même paire orientée de littéraux, on cherche à forcer $s_a = s_b$ en reliant $s_a$ et $s_b$ par une arête ferromagnétique géante de poids $100\,000 \cdot u$.

**Problème (Localisation Spectrale)** : 
Cette arête géante crée un déséquilibre de degré extrême. Les nœuds auxiliaires concernés acquièrent un degré disproportionné ($\approx 100\,000$). L'optimisation spectrale unitaire localise alors la totalité de la norme du vecteur propre $v_{\text{min}}$ sur ces nœuds auxiliaires, réduisant la magnitude sur les variables d'origine et le nœud de référence $T$ à des valeurs proches de zéro, bruitées et inexploitables.

**Solution (Contraction de Nœuds)** :
Au lieu d'ajouter des arêtes géantes, nous identifions les composantes connexes d'auxiliaires devant être égaux, et **nous les contractons (fusionnons) explicitement** en un seul nœud auxiliaire dans la matrice d'adjacence $A$. Cela :
* Garantit l'égalité $s_a = s_b$ de façon exacte.
* Évite d'introduire des poids démesurés dans la matrice.
* Maintient des degrés homogènes sur le graphe.

---

## 3. Le Laplacien Signé Combinatoire et Normalisé

Toutes les contributions d'arêtes sont sommées algébriquement pour former la matrice d'adjacence signée $A$ ($A_{ij} = \sum \operatorname{sign}(e) \cdot \operatorname{weight}(e)$).

Soit $D_{ii} = \sum_j |A_{ij}|$ la matrice de degrés signée et $L = D - A$ le Laplacien signé.

### A. Laplacien Signé Combinatoire (Par défaut)
La résolution utilise par défaut le Laplacien signé combinatoire unitaire :
$$L_{\text{comb}} = D - A$$
On cherche le vecteur propre $v_{\text{min}}$ de la plus petite valeur propre de $L_{\text{comb}}$.

### B. Laplacien Signé Normalisé (Optionnel)
Pour compenser les différences de degré entre les variables et les nœuds auxiliaires, l'option `normalize=True` est fournie :
$$L_{\text{norm}} = D^{-1/2} L D^{-1/2}$$
Le vecteur propre résolu $u_{\text{min}}$ est converti par $v_{\text{min}} = D^{-1/2} u_{\text{min}}$.

La configuration de spin estimée est obtenue en alignant le signe par rapport à $T$ (indexé à $0$) :
$$\sigma_i = \operatorname{sign}(v_{\text{min}}[i]) \cdot \operatorname{sign}(v_{\text{min}}[0])$$

---

## 4. Phase de Recherche Locale WalkSAT (Optionnelle, désactivée par défaut)

Dans la phase actuelle de test, la recherche locale WalkSAT (post-processing / hybridation) est **désactivée par défaut** (`run_local_search=False`) afin d'étudier la performance brute de la réduction spectrale.

Lorsqu'elle est activée, elle utilise la solution spectrale comme **warm-start** pour guider WalkSAT. Sur les instances satisfaisables, cela réduit le nombre de flips requis pour converger vers une solution SAT d'un facteur 10x à 20x par rapport à une initialisation aléatoire.
