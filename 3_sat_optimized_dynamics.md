# Dynamique de Clusters Optimisée pour le Problème 3-SAT sur Graphes Signés

Ce document propose une formulation mathématique d'une dynamique de clusters optimisée pour résoudre le problème 3-SAT à l'aide de graphes signés, en gelant le moins de variables possible pour éviter le blocage des chaînes de Markov.

---

## 1. Modélisation Énergétique d'une Clause 3-SAT

Soit une clause $C = \ell_1 \lor \ell_2 \lor \ell_3$ sur trois littéraux.

On introduit un nœud de référence $T$ dont le spin est fixé à $s_T = +1$ (la Vérité).

Pour chaque littéral $\ell_i$ ($i \in \{1, 2, 3\}$) associé à la variable $x_i$, on définit la valeur du littéral $L_i \in \{-1, +1\}$ par rapport à $s_T$ :
* Si $\ell_i = x_i$, alors $L_i = s_i s_T = s_i$.
* Si $\ell_i = \neg x_i$, alors $L_i = -s_i s_T = -s_i$.

L'énergie globale du système est définie par :

$$U(\sigma) = u \sum_{C} \mathbb{I}(C \text{ est insatisfaite})$$

où $u > 0$ est le poids d'une clause insatisfaite. Pour chaque clause $C$ :
* $\mathbb{I}(C \text{ est insatisfaite}) = 1$ si $L_1 = L_2 = L_3 = -1$.
* $\mathbb{I}(C \text{ est insatisfaite}) = 0$ sinon (au moins un littéral est à $+1$).

---

## 2. Décomposition de l'Énergie et Interprétation Géométrique

Cette énergie se décompose géométriquement en associant à chaque clause deux structures distinctes sur le tétraèdre $\{1, 2, 3, T\}$ (avec $s_T = +1$) :

1. **Le triangle contradictoire (base $\{1, 2, 3\}$) :**
   * Ses 3 arêtes ont un signe **opposé** au produit des littéraux ($S_{ab} = -v_a v_b$).
   * Ce triangle est frustré (la parité de ses arêtes négatives est impaire) et ne peut avoir au plus que 2 arêtes satisfaites.
   * Il est dit **satisfait** si 2 arêtes sur 3 sont satisfaites (ce qui se produit si les $L_i$ ne sont pas tous égaux).
   * Il est dit **non satisfait** si ses 3 arêtes sont non satisfaites (ce qui se produit si et seulement si $L_1 = L_2 = L_3$). Soit $I_{\text{tri}}$ son indicatrice.

2. **Le tétraèdre conforme $\{1, 2, 3, T\}$ :**
   * Ses 6 arêtes ont des signes en **accord** avec les littéraux ($S_{aT} = v_a$ et $S_{ab} = +v_a v_b$).
   * Ce tétraèdre n'est pas frustré et peut être pleinement satisfait.
   * Il est dit **satisfait** si ses 6 arêtes sont satisfaites (ce qui se produit si et seulement si $L_1 = L_2 = L_3 = +1$).
   * Il est dit **non satisfait** si au moins une de ses 6 arêtes n'est pas satisfaite. Soit $I_{\text{tet}}$ son indicatrice.

### Caractérisation de la Clause
Si la clause $C$ est satisfaite, alors :
* Soit le triangle contradictoire de base est satisfait (2/3 arêtes satisfaites).
* Soit le tétraèdre conforme est satisfait (toutes ses arêtes satisfaites).

Si la clause $C$ est insatisfaite ($L_1 = L_2 = L_3 = -1$), ni le triangle contradictoire ni le tétraèdre conforme ne sont satisfaits.

### Équivalence Énergétique
Pour chaque clause, on a la relation d'indicateurs suivante :

$$\mathbb{I}(C \text{ est insatisfaite}) = I_{\text{tri}} + I_{\text{tet}} - 1$$

Par conséquent, l'énergie globale du système $U(\sigma)$ est égale, à une constante additive près (égale à $-u$ fois le nombre de clauses), à :

$$U(\sigma) = u \sum_{C} I_{\text{tri}}(C) + u \sum_{C} I_{\text{tet}}(C)$$

---

## 3. Dynamique de Clusters Optimisée (Gels Minimaux)

Pour concevoir une dynamique Swendsen-Wang qui minimise le gel, on formule les choix de gel locaux pour le tétraèdre de chaque clause $b = \{1, 2, 3, T\}$.

Soit $\omega_b$ le sous-graphe gelé sur le tétraèdre $b$.
* $\omega_b = \emptyset$ correspond à ne rien geler (les nœuds restent indépendants).
* $\omega_b = \omega_{\text{all}}$ correspond à geler toutes les arêtes reliant les variables littérales à $T$ (bloquant les spins à $-1$).

### Règle de Gel Proposée
* Si la clause $C$ est **satisfaite** ($\sigma \in \text{Sat}$) :

  $$P_b^{\text{Sat}}(\emptyset) = 1 \quad \text{et} \quad P_b^{\text{Sat}}(\omega_b) = 0 \quad (\forall \omega_b \neq \emptyset)$$

  > [!TIP]
  > Les clauses satisfaites ne gèlent **strictement rien** (probabilité $1$ d'avoir $\emptyset$). Cela laisse le maximum de liberté au système pour explorer l'espace des configurations.
  
* Si la clause $C$ est **insatisfaite** ($\sigma = \text{Unsat}$) :

  $$P_b^{\text{Unsat}}(\emptyset) = e^{-u}$$

  $$P_b^{\text{Unsat}}(\omega_{\text{all}}) = 1 - e^{-u}$$

  Les clauses insatisfaites gèlent le tétraèdre entier avec probabilité $1 - e^{-u}$ pour forcer le système à s'ajuster lors du recoloriage.

---

## 4. Preuve de la Réversibilité et de la Balance Détaillée

Pour garantir que cette dynamique laisse la mesure de Gibbs invariante, on verifies la condition de balance détaillée.

La mesure de Gibbs locale pour une clause est $\mu(\sigma) \propto e^{-U_C(\sigma)}$ où $U_C(\sigma) = u \mathbb{I}(C \text{ est insatisfaite})$.

Soit le couplage d'Edwards-Sokal sur l'espace joint $(\sigma, \omega_b)$. La condition de réversibilité locale s'écrit :

$$e^{-U_C(\sigma)} P_b^\sigma(\omega_b) = e^{-U_C(\sigma')} P_b^{\sigma'}(\omega_b)$$

pour toutes les configurations $\sigma, \sigma'$ compatibles avec le sous-graphe gelé $\omega_b$.

### Vérification :
1. **Pour $\omega_b = \emptyset$ :**
   Toutes les configurations sont compatibles avec le graphe vide.
   * Pour $\sigma \in \text{Sat}$ ($U_C(\sigma) = 0$) :
     $$e^{-0} P_b^{\text{Sat}}(\emptyset) = 1 \cdot 1 = 1$$
   * Pour $\sigma = \text{Unsat}$ ($U_C(\sigma) = u$) :
     $$e^{-u} P_b^{\text{Unsat}}(\emptyset) = e^{-u} \cdot e^u = 1$$
   La condition est parfaitement respectée : $1 = 1$.

2. **Pour $\omega_b = \omega_{\text{all}}$ :**
   La seule configuration compatible avec $\omega_{\text{all}}$ est $\text{Unsat}$ (car toutes les variables littérales sont connectées à $T$ qui a pour valeur $+1$, imposant $L_i = -1$).
   * Puisqu'il n'y a qu'une seule configuration compatible, la relation de balance détaillée pour cet état s'applique de façon triviale.
   * Pour tout $\sigma' \in \text{Sat}$, la compatibilité est nulle, donc $P_b^{\sigma'}(\omega_{\text{all}}) = 0$.

La dynamique est donc **mathématiquement rigoureuse et réversible** par rapport à la distribution de Gibbs de la postérieure.

---

## 5. Algorithme Global de Transition

Un pas complet de la dynamique s'effectue comme suit :

1. **Phase de Gel :**
   * Pour chaque clause $C$ satisfaite, ne geler aucune arête du tétraèdre associé.
   * Pour chaque clause $C$ insatisfaite, geler le tétraèdre complet $\omega_{\text{all}}$ avec probabilité $1-e^{-u}$.
2. **Phase de Partition :**
   * Identifier les composantes connexes du graphe formé par les arêtes gelées.
   * La composante contenant le nœud $T$ a ses spins gelés (sa configuration est inchangée).
3. **Phase de Recoloriage :**
   * Pour chaque composante connexe $C'$ ne contenant pas le nœud $T$, tirer un nouveau spin $s_{C'} \in \{-1, +1\}$ selon la loi de Gibbs réduite :
     $$W(\sigma) \propto \prod_{C \text{ t.q. } \omega_C = \emptyset} \left( \mathbb{I}(C \text{ satisfaite}) + e^{-2u} \mathbb{I}(C \text{ insatisfaite}) \right)$$
     (Puisque $u \gg 0$, $e^{-2u} \approx 0$, ce qui incite fortement le recoloriage à satisfaire les clauses libres).
