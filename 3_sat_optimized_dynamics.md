# Dynamique de Clusters Optimisée pour le Problème SAT Réel sur Graphes Signés

Ce document présente une formulation mathématique rigoureuse et précise d'un algorithme de résolution du problème SAT général (contenant des clauses de taille 1, 2 et 3) adapté aux cas d'applications réels. Cet algorithme repose sur un prétraitement récursif des clauses unitaires, un double transfert d'énergie (intégrant les couplages des clauses de taille 2), une dynamique de Markov hybride combinant un gel de type Swendsen-Wang (sur la partie isotrope et quadratique) et des acceptations de type Metropolis-Hastings (sur la partie orientée et les champs locaux), suivie d'une phase de clustering spectral.

---

## 1. Modélisation Énergétique des Clauses SAT

Soit une formule SAT contenant $`N`$ variables $`x_1, \dots, x_N`$ et un ensemble de clauses $`\mathcal{C}`$. La configuration de spins du système est notée $`\sigma \in \lbrace -1, +1 \rbrace^N`$, où le spin $`s_i = \sigma_i`$ correspond à la variable $`x_i`$ ($`+1`$ pour Vrai, $`-1`$ pour Faux).

Pour chaque littéral $`\ell`$ d'une clause, on note $`s_i`$ sa variable sous-jacente et sa polarité $`\eta \in \lbrace -1, +1 \rbrace`$ définie par :

$$
\eta = 1 - 2 \cdot \mathbf{1}(\ell = \neg x_i)
$$


La valeur du littéral est $`L = \eta s_i`$. Une clause $`C`$ contenant des littéraux $`L_{C,1}, \dots, L_{C,k}`$ (avec $`k \in \lbrace 1, 2, 3 \rbrace`$) est insatisfaite si et seulement si tous ses littéraux valent $`-1`$. L'énergie globale du système est la somme des pénalités $`u > 0`$ associées aux clauses insatisfaites :

$$
U(\sigma) = u \sum_{C \in \mathcal{C}} \mathbf{1}\left(\forall j \in \lbrace 1, \dots, |C| \rbrace, \, L_{C,j} = -1\right)
$$


---

## 2. Décomposition de l'Énergie selon la Taille des Clauses

Chaque clause est projetée sous forme de couplages (arêtes), de structures d'ordre supérieur (triangles) ou de champs locaux.

### 2.1. Clauses de taille 1 (Unitaires : $`C = \ell_1`$ avec multiplicité $`m`$)
Pour $`m`$ occurrences de la même clause unitaire, l'indicatrice d'insatisfaction cumulée vaut :

$$
m \cdot \mathbf{1}(L_1 = -1) = m \left(\frac{1 - \eta_1 s_1}{2}\right) = \frac{m}{2} - \frac{m \eta_1}{2} s_1
$$

Elle se traduit par :
* Un décalage constant d'énergie de $`m \cdot u / 2`$ (ignoré).
* Un **champ magnétique local** (champ orienté) agissant sur le spin $`s_1`$ proportionnel à $`m`$ :

$$
h_1^{\mathrm{unit}} = m \cdot \frac{u \eta_1}{2}
$$


### 2.2. Clauses de taille 2 (Binaires : $`C = \ell_1 \lor \ell_2`$)
L'indicatrice d'insatisfaction vaut :

$$
\mathbf{1}(L_1 = -1 \text{ et } L_2 = -1) = \frac{1 - \eta_1 s_1}{2} \cdot \frac{1 - \eta_2 s_2}{2} = \frac{1}{4} - \frac{\eta_1}{4} s_1 - \frac{\eta_2}{4} s_2 + \frac{\eta_1 \eta_2}{4} s_1 s_2
$$


À une constante d'énergie près, la clause binaire est encodée par :
1. **Une arête non orientée (couplage spin-spin)** entre $`s_1`$ et $`s_2`$ de poids $`u/4`$ et de **polarité inverse** de celle des littéraux :

$$
W_{12}^{\mathrm{bin}} = - \frac{u \eta_1 \eta_2}{4}
$$

*(Exemple : si $`\eta_1 = \eta_2 = 1`$ (positifs), le couplage est de $`+u/4`$, ce qui est antiferromagnétique, favorisant des spins opposés pour éviter la configuration insatisfaite $`(-1, -1)`$).*
2. **Une arête orientée (champs magnétiques locaux)** agissant comme une force de rappel de poids $`u/4`$ favorisant l'alignement des spins avec leurs littéraux respectifs :

$$
h_1^{\mathrm{bin}} = \frac{u \eta_1}{4}, \quad h_2^{\mathrm{bin}} = \frac{u \eta_2}{4}
$$


### 2.3. Clauses de taille 3 (Ternaires : $`C = \ell_1 \lor \ell_2 \lor \ell_3`$)
L'indicatrice d'insatisfaction $`\mathbf{1}(L_1 = L_2 = L_3 = -1)`$ est décomposée en :
1. **Un triangle contradictoire (partie isotrope)** représentant la frustration topologique :

$$
I_{\mathrm{tri}}(C) = \mathbf{1}(L_1 = L_2 = L_3)
$$

2. **Un triangle orienté (partie orientée)** :

$$
I_{\mathrm{ori}}(C) = 1 - \mathbf{1}(L_1 = L_2 = L_3 = 1)
$$

De sorte que :

$$
\mathbf{1}(L_1 = L_2 = L_3 = -1) = I_{\mathrm{tri}}(C) + I_{\mathrm{ori}}(C) - 1
$$


---

## 3. Double Transfert d'Énergie et Compensation de la Frustration

### Premier Transfert : Des structures isotropes vers le graphe d'interactions
On regroupe toutes les arêtes non orientées et les triangles contradictoires sur le graphe de couplage quadratique initial :
1. **Contributions des 3-clauses** : Chaque triangle contradictoire $`C`$ sur $`\lbrace i_1, i_2, i_3 \rbrace`$ est projeté sur ses trois arêtes constitutives $`\lbrace i_j, i_k \rbrace`$ avec un poids $`u/2`$ et une polarité de jauge :

$$
W_{i_j i_k}^{(C), \mathrm{tri}} = - \eta_{j} \eta_{k} \frac{u}{2}
$$

2. **Contributions des 2-clauses** : Chaque clause binaire $`C`$ sur $`\lbrace i_1, i_2 \rbrace`$ ajoute directement son couplage quadratique :

$$
W_{i_1 i_2}^{(C), \mathrm{bin}} = - \eta_{1} \eta_{2} \frac{u}{4}
$$


En sommant les contributions de toutes les clauses sur chaque paire de variables $`\lbrace i, j \rbrace`$, on obtient le poids d'arête global initial :

$$
W_{ij} = \sum_{C \in \mathcal{C}_3 \,:\, \lbrace i,j \rbrace \subset C} W_{ij}^{(C), \mathrm{tri}} + \sum_{C \in \mathcal{C}_2 \,:\, \lbrace i,j \rbrace = C} W_{ij}^{(C), \mathrm{bin}}
$$


Les clauses de polarités opposées s'annulent mutuellement dans cette somme (compensation de la frustration).

### Second Transfert : Des arêtes vers les triangles isotropes
On résout le programme d'optimisation linéaire (LP) pour transférer le maximum possible de l'énergie des arêtes $`W_{ij}`$ vers des triangles isotropes non orientés à 3 spins :

$$
\max_{\omega} \sum_{t} \omega_t
$$

sous les contraintes de poids résiduels positifs pour chaque arête $`\lbrace i, j \rbrace`$ :

$$
\sum_{t \supset \lbrace i,j \rbrace} \omega_t \le |W_{ij}|
$$

Cela définit les poids des triangles isotropes $`\omega_t \ge 0`$ et le poids final des arêtes résiduelles :

$$
W_{ij}^{\mathrm{res}} = W_{ij} - \mathrm{sign}(W_{ij}) \sum_{t \supset \lbrace i,j \rbrace} \omega_t
$$


---

## 4. La Dynamique Markovienne Hybride

Le Hamiltonian global se divise en deux parties pour l'échantillonnage :

$$
U(\sigma) = U_{\mathrm{iso}}(\sigma) + U_{\mathrm{ori}}(\sigma)
$$

* **La partie isotrope/symétrique** ($`U_{\mathrm{iso}}`$) comprend les arêtes résiduelles $`W_{ij}^{\mathrm{res}}`$ et les triangles isotropes $`\omega_t`$.
* **La partie orientée/champs locaux** ($`U_{\mathrm{ori}}`$) comprend les triangles orientés $`I_{\mathrm{ori}}(C)`$, les champs locaux des clauses binaires $`h_i^{\mathrm{bin}}`$, et les champs locaux des clauses unitaires $`h_i^{\mathrm{unit}}`$.

### Étape 1 : Phase de Gel de Swendsen-Wang (Partie Isotrope)
On forme des clusters gelés sur la partie isotrope :
1. **Sur les arêtes résiduelles $`e = \lbrace i, j \rbrace`$** : Si elle est satisfaite ($`s_i s_j \mathrm{sign}(W_e^{\mathrm{res}}) > 0`$), on la gèle avec probabilité :

$$
p_{\mathrm{gel}}(e) = 1 - e^{-|W_e^{\mathrm{res}}|}
$$

2. **Sur les triangles isotropes $`t`$** : On applique le gel corrélé triangulaire :
   * **Triangle attractif** : Si les 3 arêtes sont satisfaites, on les gèle ensemble avec probabilité $`1 - e^{-2\omega_t}`$. Sinon, on ne gèle rien.
   * **Triangle frustré** : Si le triangle est dans son état de basse énergie (2 arêtes satisfaites), on gèle l'une d'elles équiprobablement avec probabilité $`\frac{1}{2}(1 - e^{-2\omega_t})`$. Sinon, on ne gèle rien.

Cette étape définit une partition des variables actives en clusters gelés $`\lbrace K_1, \dots, K_M \rbrace`$.

### Étape 2 : Recoloriage par Metropolis-Hastings (Partie Orientée et Champs)
Pour chaque cluster $`K_m`$, on propose d'inverser globalement l'état de ses spins ($`\sigma_i \leftarrow -\sigma_i`$ pour tout $`i \in K_m`$).
Le flip du cluster $`K_m`$ est accepté selon le critère de Metropolis-Hastings basé sur la variation de la partie orientée globale (incluant les champs locaux) :

$$
\alpha(K_m) = \min\left(1, e^{-\Delta U_{\mathrm{ori}}}\right)
$$

où :

$$
U_{\mathrm{ori}}(\sigma) = u \sum_{C \in \mathcal{C}_3} I_{\mathrm{ori}}(C) - \sum_{i=1}^{N_{\mathrm{red}}} h_i^{\mathrm{tot}} s_i
$$

avec $`h_i^{\mathrm{tot}} = \sum_{C \in \mathcal{C}_2} h_i^{(C), \mathrm{bin}} + \sum_{C \in \mathcal{C}_1} h_i^{(C), \mathrm{unit}}`$ la somme de tous les champs magnétiques orientés s'appliquant sur la variable $`x_i`$.

---

## 5. Description Algorithmique Complète

L'algorithme de résolution se déroule comme suit :

1. **Pré-traitement récursif des clauses unitaires** :
   Pour chaque variable $`x_i`$ apparaissant dans une clause unitaire $`[l]`$ :
    * On calcule son énergie sous l'assignation recommandée $`l = 1`$ (bénéfice d'énergie de $`m \cdot u`$, où $`m`$ est la multiplicité de cette clause unitaire).
    * On identifie l'ensemble des clauses $`C_{\mathrm{opp}}`$ dans lesquelles $`x_i`$ apparaît sous sa forme inversée $`\neg l`$. Soit $`k = |C_{\mathrm{opp}}|`$ le nombre total de ces clauses.
    * **Condition d'assignation forcée** : Si $`m > k`$, alors l'assignation de force $`l=1`$ garantit une amélioration stricte de l'énergie minimale dans le pire des cas (bénéfice d'énergie minimal de $`(m - k) \cdot u > 0`$).
      * Si cette condition est satisfaite, on assigne de force le spin à sa valeur satisfaisante, on supprime la variable et ses clauses satisfaites, on raccourcit les autres et on recommence récursivement (propagation unitaire).
      * Si la condition n'est pas satisfaite, on n'assigne pas la variable. La clause unitaire est conservée et sera encodée sous la forme d'un champ magnétique local $`h_i^{\mathrm{unit}}`$ d'amplitude proportionnelle à sa multiplicité $`m`$ lors de l'initialisation du solveur.

2. **Élimination des littéraux purs et des variables orphelines** :
   On applique la réduction habituelle des littéraux purs sur le reste des variables et des clauses de manière récursive.

3. **Initialisation et double transfert d'énergie** :
   * Les clauses binaires restantes sont converties en couplages quadratiques dans $`W_{ij}`$ et en champs locaux $`h_i^{\mathrm{bin}}`$.
   * Les clauses ternaires restantes sont décomposées en triangles contradictoires (projetés sur $`W_{ij}`$) et triangles orientés.
   * Résolution du LP pour transférer le maximum possible de $`W_{ij}`$ vers les triangles isotropes $`T_{\mathrm{iso}}`$ et obtenir $`W_{ij}^{\mathrm{res}}`$.

4. **Échantillonnage MCMC Hybride** :
   Sur les spins actifs, exécuter les cycles de gel de Swendsen-Wang (partie isotrope et quadratique) suivis des inversions de clusters Metropolis-Hastings acceptées selon $`U_{\mathrm{ori}}`$ (partie orientée et champs totaux).

5. **Clustering Spectral Signé** :
   Calcul de la covariance empirique $`\hat{\Gamma}`$ sur les étapes échantillonnées post-burn-in, construction du Laplacien signé $`L_{\mathrm{signed}} = D - \hat{\Gamma}`$, et partition spectrale basée sur le signe du vecteur propre de plus petite valeur propre.

6. **Sélection et recomposition** :
   Évaluation des énergies globales avec les variables fixées au prétraitement, et sélection du meilleur candidat.
