# Dynamique de Clusters Optimisée pour le Problème 3-SAT sur Graphes Signés

Ce document présente une formulation mathématique rigoureuse et précise d'un algorithme de résolution du problème 3-SAT. Cet algorithme repose sur un double transfert d'énergie, une dynamique de Markov hybride combinant un gel de type Swendsen-Wang (sur la partie isotrope) et des acceptations de type Metropolis-Hastings (sur la partie orientée), suivie d'une phase de clustering spectral sur la matrice de corrélation spin-spin empirique.

---

## 1. Modélisation Énergétique d'une Clause 3-SAT

Soit une formule 3-SAT contenant $N$ variables $x_1, \dots, x_N$ et un ensemble de clauses $\mathcal{C}$. Chaque clause $C \in \mathcal{C}$ porte sur trois littéraux :

$$
C = \ell_{C,1} \lor \ell_{C,2} \lor \ell_{C,3}
$$

où chaque littéral $\ell_{C,k}$ correspond à une variable sous-jacente $x_{i_k}$ ($i_k \in \{1, \dots, N\}$) sous forme directe ($x_{i_k}$) ou inversée ($\neg x_{i_k}$).

On introduit un nœud de référence additionnel virtuel $T$ représentant l'état « Vrai » (True), dont le spin est fixé à $s_T = +1$. La configuration de spins du système est notée $\sigma \in \{-1, +1\}^N$, avec $s_i = \sigma_i$ le spin de la variable $x_i$.

Pour chaque littéral $\ell_{C,k}$, on définit sa valeur $L_{C,k} \in \{-1, +1\}$ par rapport à la configuration $\sigma$ :

$$
L_{C,k} = \begin{cases} s_{i_k} & \text{si } \ell_{C,k} = x_{i_k} \\ -s_{i_k} & \text{si } \ell_{C,k} = \neg x_{i_k} \end{cases}
$$

L'énergie de Gibbs globale de la formule 3-SAT est donnée par :

$$
U(\sigma) = u \sum_{C \in \mathcal{C}} \mathbb{1}(C \text{ est insatisfaite})
$$

où $u > 0$ est la pénalité associée à chaque clause insatisfaite. Une clause $C$ est insatisfaite si et seulement si $L_{C,1} = L_{C,2} = L_{C,3} = -1$.

---

## 2. Décomposition de l'Énergie en Structures Géométriques

Pour chaque clause $C$, la pénalité d'insatisfaction est décomposée géométriquement sur le tétraèdre $\{i_1, i_2, i_3, T\}$ en deux composantes distinctes :

1. **Le triangle contradictoire** (base $\{i_1, i_2, i_3\}$) :
   Les arêtes ont un signe opposé au produit des littéraux ($S_{jk} = -\eta_j \eta_k$ où $L_{C,j} = \eta_j s_{i_j}$). Ce triangle est intrinsèquement frustré. Son indicatrice d'insatisfaction vaut :
   
$$
I_{\mathrm{tri}}(C) = \mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3})
$$

   c'est-à-dire que tous les littéraux ont la même valeur (soit tous vrais, soit tous faux).

2. **Le tétraèdre conforme (triangle orienté)** :
   Cette structure inclut le nœud virtuel $T$. Son indicatrice d'insatisfaction vaut :
   
$$
I_{\mathrm{tet}}(C) = 1 - \mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3} = +1)
$$

   c'est-à-dire qu'il est insatisfait sauf si tous les littéraux de la clause sont à $+1$.

L'indicateur d'insatisfaction de la clause $C$ est lié à ces structures par la relation :

$$
\mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3} = -1) = I_{\mathrm{tri}}(C) + I_{\mathrm{tet}}(C) - 1
$$

À une constante additive près (égale à $-u |\mathcal{C}|$), le Hamiltonian global s'exprime comme :

$$
U(\sigma) = \sum_{C \in \mathcal{C}} U_C^{\mathrm{tri}}(\sigma) + \sum_{C \in \mathcal{C}} U_C^{\mathrm{ori}}(\sigma)
$$

où :
* $U_C^{\mathrm{tri}}(\sigma) = u I_{\mathrm{tri}}(C) = u \mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3})$
* $U_C^{\mathrm{ori}}(\sigma) = u I_{\mathrm{tet}}(C) = u \left(1 - \mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3} = +1)\right)$

---

## 3. Le Double Transfert d'Énergie et l'Annulation de la Frustration

### Premier Transfert : Des Triangles Contradictoires vers les Arêtes
Pour chaque clause $C$, l'énergie du triangle contradictoire $U_C^{\mathrm{tri}}(\sigma)$ est redistribuée sur ses trois arêtes constitutives $\{i_j, i_k\}$. Chaque arête reçoit une contribution de poids $u/2$ avec le signe approprié :

$$
W_{i_j i_k}^{(C)} = - \eta_j \eta_k \frac{u}{2}
$$

où $\eta_j$ est le signe du littéral $j$ ($+1$ pour direct, $-1$ pour inversé).

En sommant les contributions de toutes les clauses sur chaque paire de variables $\{i, j\}$, on obtient le poids global de l'arête :

$$
W_{ij} = \sum_{C \in \mathcal{C} \,:\, \{i,j\} \subset C} W_{ij}^{(C)}
$$

> [!NOTE]
> De nombreuses variables apparaissant dans des clauses différentes avec des polarités opposées, leurs contributions énergétiques $W_{ij}^{(C)}$ de signes contraires se compensent et s'annulent mutuellement dans la somme. Cette compensation élimine une part importante de la frustration globale du système.

### Second Transfert : Des Arêtes vers les Triangles Isotropes
Afin de maximiser les corrélations de gel globales, on redistribue à nouveau la plus grande fraction possible de l'énergie des arêtes $W_{ij}$ vers des triangles isotropes non orientés.
On cherche un ensemble de poids de triangles $\omega_t \ge 0$ pour chaque triangle $t = \{a, b, c\}$ du graphe en résolvant le programme d'optimisation linéaire suivant :

$$
\max_{\omega} \sum_{t} \omega_t
$$

sous les contraintes, pour chaque arête $\{i, j\}$ :

$$
\sum_{t \supset \{i,j\}} \omega_t \le |W_{ij}|
$$

et pour chaque triangle $t = \{a, b, c\}$, la cohérence des signes doit être respectée (le produit des signes des arêtes du triangle doit être $+1$, de sorte que le triangle soit non frustré).

Une fois les poids de triangles optimaux $\omega_t$ calculés, on définit :
* Les triangles isotropes $T_{\mathrm{iso}}$ avec leurs poids $\omega_t > 0$.
* Les poids résiduels des arêtes $W_{ij}^{\mathrm{res}}$ sur l'ensemble d'arêtes $E_{\mathrm{res}}$ :
  
$$
W_{ij}^{\mathrm{res}} = \mathrm{sign}(W_{ij}) \left( |W_{ij}| - \sum_{t \supset \{i,j\}} \omega_t \right)
$$

Le Hamiltonian du système est réécrit de manière équivalente sous la forme :

$$
U(\sigma) = \sum_{e \in E_{\mathrm{res}}} \psi_{W_e^{\mathrm{res}}}(\sigma) + \sum_{t \in T_{\mathrm{iso}}} U_t^{\mathrm{iso}}(\sigma) + \sum_{C \in \mathcal{C}} U_C^{\mathrm{ori}}(\sigma)
$$

où :
* $\psi_{W_e^{\mathrm{res}}}(\sigma) = |W_e^{\mathrm{res}}| \mathbb{1}(s_i \neq \mathrm{sign}(W_e^{\mathrm{res}}) s_j)$ est le potentiel de l'arête résiduelle.
* $U_t^{\mathrm{iso}}(\sigma) = 2 \omega_t \mathbb{1}(\sigma \text{ ne satisfait pas } t)$ est le potentiel du triangle isotrope.
* $U_C^{\mathrm{ori}}(\sigma) = u \left(1 - \mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3} = +1)\right)$ est l'énergie du triangle orienté (tétraèdre).

---

## 4. La Dynamique Markovienne Hybride

La structure hybride de l'énergie permet de construire une dynamique de transition extrêmement efficace en deux étapes.

### Étape 1 : Phase de Gel de Swendsen-Wang (Partie Isotrope)
On applique la dynamique de gel sur les composantes isotropes de l'énergie ($E_{\mathrm{res}}$ et $T_{\mathrm{iso}}$) :
1. **Sur les arêtes résiduelles $e \in E_{\mathrm{res}}$** :
   Si l'arête $e = \{i, j\}$ est satisfaite par la configuration courante $\sigma$ (c'est-à-dire $s_i s_j \mathrm{sign}(W_e^{\mathrm{res}}) > 0$), on la gèle avec la probabilité :
   
$$
p_{\mathrm{gel}}(e) = 1 - e^{-|W_e^{\mathrm{res}}|}
$$

   Si elle n'est pas satisfaite, elle n'est pas gelée.

2. **Sur les triangles isotropes $t \in T_{\mathrm{iso}}$** :
   On applique la règle de gel locale corrélée issue de la dynamique triangulaire :
   * Si le triangle est entièrement satisfait (basse énergie), on gèle toutes ses arêtes avec probabilité $a_{\omega_t} = 1 - e^{-2\omega_t}$, et aucune avec probabilité $b_{\omega_t} = e^{-2\omega_t}$.
   * Si le triangle est insatisfait, on ne gèle aucune de ses arêtes.

Cette étape de gel définit une partition des variables $V$ en un ensemble de clusters gelés $\mathcal{K} = \{K_1, K_2, \dots, K_M\}$.

### Étape 2 : Recoloriage par Metropolis-Hastings (Partie Orientée)
Les clusters de variables $\mathcal{K}$ doivent être recoloriés. Puisque $K = 2$, chaque cluster $K_m$ peut être soit conservé dans son état actuel, soit inversé globalement ($s_i \leftarrow -s_i$ pour tout $i \in K_m$).

Pour chaque cluster $K_m$, on propose le flip de tous ses spins. Soit $\sigma^{(0)}$ la configuration courante et $\sigma^{(1)}$ la configuration candidate avec le cluster $K_m$ inversé. La transition est acceptée selon un critère de Metropolis-Hastings basé exclusivement sur la variation de la partie orientée de l'énergie :

$$
\alpha(K_m) = \min\left(1, e^{-\Delta U^{\mathrm{ori}}}\right)
$$

avec :

$$
\Delta U^{\mathrm{ori}} = U^{\mathrm{ori}}(\sigma^{(1)}) - U^{\mathrm{ori}}(\sigma^{(0)})
$$

où $U^{\mathrm{ori}}(\sigma) = u \sum_{C \in \mathcal{C}} \left(1 - \mathbb{1}(L_{C,1} = L_{C,2} = L_{C,3} = +1)\right)$.

---

## 5. Description Complète de l'Algorithme

L'algorithme global de résolution se déroule comme suit :

1. **Initialisation et double transfert d'énergie** :
   * Construire le graphe de départ en décomposant les clauses en triangles contradictoires et orientés.
   * Transférer l'énergie $U_C^{\mathrm{tri}}$ vers les poids d'arêtes initiaux $W_{ij}$.
   * Résoudre le problème d'optimisation linéaire pour transférer le maximum de poids vers les triangles isotropes $T_{\mathrm{iso}}$, et obtenir les arêtes résiduelles $E_{\mathrm{res}}$.

2. **Échantillonnage MCMC** :
   Partir d'une configuration aléatoire $\sigma^{(0)}$. Pour chaque étape $s \in \{1, \dots, S_{\text{steps}}\}$ :
   * Appliquer la phase de gel de Swendsen-Wang pour former les clusters $\mathcal{K}$.
   * Pour chaque cluster $K_m \in \mathcal{K}$, appliquer l'étape de Metropolis-Hastings avec l'énergie orientée $U^{\mathrm{ori}}$.
   * Stocker la configuration résultante $\sigma^{(s)}$.

3. **Calcul de la matrice de corrélation empirique** :
   À l'aide des configurations échantillonnées, calculer l'estimateur empirique de la matrice de covariance (corrélation spin-spin) $\hat{\Gamma} \in \mathbb{R}^{N \times N}$ :
   
$$
\hat{\Gamma}_{ij} = \hat{\mathbb{E}}[\sigma_i \sigma_j] - \hat{\mathbb{E}}[\sigma_i] \hat{\mathbb{E}}[\sigma_j]
$$

   où :
   
$$
\hat{\mathbb{E}}[f(\sigma)] = \frac{1}{S_{\text{steps}}} \sum_{s=1}^{S_{\text{steps}}} f(\sigma^{(s)})
$$

4. **Clustering Spectral Signé** :
   On applique un clustering spectral à deux communautés sur la matrice de corrélation $\hat{\Gamma}$.
   * Définir la matrice des degrés absolus $D \in \mathbb{R}^{N \times N}$ :
     
$$
D_{ii} = \sum_{j=1}^N |\hat{\Gamma}_{ij}|
$$

   * Construire le Laplacien signé :
     
$$
L_{\mathrm{signed}} = D - \hat{\Gamma}
$$

   * Calculer le vecteur propre $v_2 \in \mathbb{R}^N$ correspondant à la deuxième plus petite valeur propre de $L_{\mathrm{signed}}$ (ou de sa version normalisée $D^{-1/2} L_{\mathrm{signed}} D^{-1/2}$).
   * Déterminer la partition résultante $\sigma^{\mathrm{spectral}} \in \{-1, +1\}^N$ par :
     
$$
\sigma_i^{\mathrm{spectral}} = \mathrm{sign}(v_{2, i})
$$

5. **Sélection de la configuration optimale** :
   Puisque l'overlap est défini modulo une permutation globale ($\sigma \leftrightarrow -\sigma$), on évalue l'énergie 3-SAT initiale $U(\sigma)$ pour $\sigma^{\mathrm{spectral}}$ et $-\sigma^{\mathrm{spectral}}$.
   On renvoie la configuration $\sigma^*$ minimisant cette énergie :
   
$$
\sigma^* = \operatorname{argmin}_{\sigma \in \{\sigma^{\mathrm{spectral}}, -\sigma^{\mathrm{spectral}}\}} U(\sigma)
$$

