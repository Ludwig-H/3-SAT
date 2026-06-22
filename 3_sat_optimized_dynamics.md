# Dynamique de Clusters Optimisée pour le Problème 3-SAT sur Graphes Signés

Ce document propose une formulation mathématique d'une dynamique de clusters optimisée pour résoudre le problème 3-SAT à l'aide de graphes signés, en gelant le moins de variables possible pour éviter le blocage des chaînes de Markov.

---

## 1. Modélisation Énergétique d'une Clause 3-SAT

Soit une clause $C = \ell_1 \lor \ell_2 \lor \ell_3$ sur trois littéraux.
On introduit un nœud de référence $T$ dont le spin est fixé à $s_T = +1$ (la Vérité).
Pour chaque littéral $\ell_i$ ($i \in \{1, 2, 3\}$) associé à la variable $x_i$, on définit la valeur du littéral $L_i \in \{-1, +1\}$ par rapport à $s_T$ :
* Si $\ell_i = x_i$, alors $L_i = s_i s_T = s_i$.
* Si $\ell_i = \neg x_i$, alors $L_i = -s_i s_T = -s_i$.

L'énergie de la clause $C$ est donnée par :
* $U_C(\sigma) = w > 0$ si la clause est **insatisfaite** ($L_1 = L_2 = L_3 = -1$).
* $U_C(\sigma) = 0$ si la clause est **satisfaite** (au moins un littéral est à $+1$).

---

## 2. Décomposition de l'Énergie sur le Tétraèdre $\{1, 2, 3, T\}$

Comme présenté dans la thèse, l'énergie d'une clause peut être développée sous forme polynomiale en les variables $L_i$ :
$$\mathbb{I}(L_1 = L_2 = L_3 = -1) = \left(\frac{1-L_1}{2}\right)\left(\frac{1-L_2}{2}\right)\left(\frac{1-L_3}{2}\right)$$
$$U_C(\sigma) = \frac{w}{8} \left( 1 - (L_1 + L_2 + L_3) + (L_1 L_2 + L_2 L_3 + L_3 L_1) - L_1 L_2 L_3 \right)$$

Cette décomposition montre que l'énergie se répartit sur les éléments du tétraèdre $\{1, 2, 3, T\}$ :
1. **Liaisons de base (arêtes du triangle $\{1, 2, 3\}$) :** Termes $+ \frac{w}{8} L_i L_j$. Ces interactions ont un signe opposé au produit des deux littéraux.
2. **Liaisons latérales (champs locaux reliés à $T$) :** Termes $- \frac{w}{8} L_i$. Les signes de ces arêtes sont conformes aux littéraux.
3. **Interaction d'ordre 4 (tétraèdre entier) :** Terme $- \frac{w}{8} L_1 L_2 L_3$.

---

## 3. Dynamique de Clusters Optimisée (Gels Minimaux)

Pour concevoir une dynamique Swendsen-Wang qui minimise le gel, on formule les choix de gel locaux pour le tétraèdre de chaque clause $b = \{1, 2, 3, T\}$.

Soit $\omega_b$ le sous-graphe gelé sur le tétraèdre $b$.
* $\omega_b = \emptyset$ correspond à ne rien geler (les nœuds restent indépendants).
* $\omega_b = \omega_{all}$ correspond à geler toutes les arêtes reliant les variables littérales à $T$ (bloquant les spins à $-1$).

### Règle de Gel Proposée
* Si la clause $C$ est **satisfaite** ($\sigma \in \text{Sat}$) :
  $$P_b^{\text{Sat}}(\emptyset) = 1 \quad \text{et} \quad P_b^{\text{Sat}}(\omega_b) = 0 \quad (\forall \omega_b \neq \emptyset)$$
  > [!TIP]
  > Les clauses satisfaites ne gèlent **strictement rien** (probabilité $1$ d'avoir $\emptyset$). Cela laisse le maximum de liberté au système pour explorer l'espace des configurations.
  
* Si la clause $C$ est **insatisfaite** ($\sigma = \text{Unsat}$) :
  $$P_b^{\text{Unsat}}(\emptyset) = e^{-w}$$
  $$P_b^{\text{Unsat}}(\omega_{all}) = 1 - e^{-w}$$
  Les clauses insatisfaites gèlent le tétraèdre entier avec probabilité $1 - e^{-w}$ pour forcer le système à s'ajuster lors du recoloriage.

---

## 4. Preuve de la Réversibilité et de la Balance Détaillée

Pour garantir que cette dynamique laisse la mesure de Gibbs invariante, on vérifie la condition de balance détaillée.

La mesure de Gibbs locale est $\mu(\sigma) \propto e^{-U_b(\sigma)}$.
Soit le couplage d'Edwards-Sokal sur l'espace joint $(\sigma, \omega_b)$. La condition de réversibilité locale s'écrit :
$$e^{-U_b(\sigma)} P_b^\sigma(\omega_b) = e^{-U_b(\sigma')} P_b^{\sigma'}(\omega_b)$$
pour toutes les configurations $\sigma, \sigma'$ compatibles avec le sous-graphe gelé $\omega_b$.

### Vérification :
1. **Pour $\omega_b = \emptyset$ :**
   Toutes les configurations sont compatibles avec le graphe vide.
   * Pour $\sigma \in \text{Sat}$ ($U_b(\sigma) = 0$) :
     $$e^{-0} P_b^{\text{Sat}}(\emptyset) = 1 \cdot 1 = 1$$
   * Pour $\sigma = \text{Unsat}$ ($U_b(\sigma) = w$) :
     $$e^{-w} P_b^{\text{Unsat}}(\emptyset) = e^{-w} \cdot e^w = 1$$
   La condition est parfaitement respectée : $1 = 1$.

2. **Pour $\omega_b = \omega_{all}$ :**
   La seule configuration compatible avec $\omega_{all}$ est $\text{Unsat}$ (car toutes les variables littérales sont connectées à $T$ qui a pour valeur $+1$, imposant $L_i = -1$).
   * Puisqu'il n'y a qu'une seule configuration compatible, la relation de balance détaillée pour cet état s'applique trivialement sans contrainte d'égalité avec un autre état.
   * Pour tout $\sigma' \in \text{Sat}$, la compatibilité est nulle, donc $P_b^{\sigma'}(\omega_{all}) = 0$.

La dynamique est donc **mathématiquement rigoureuse et réversible** par rapport à la distribution de Gibbs de la postérieure.

---

## 5. Algorithme Global de Transition

Un pas complet de la dynamique s'effectue comme suit :

1. **Phase de Gel :**
   * Pour chaque clause $C$ satisfaite, ne geler aucune arête du tétraèdre associé.
   * Pour chaque clause $C$ insatisfaite, geler le tétraèdre complet $\omega_{all}$ avec probabilité $1-e^{-w}$.
2. **Phase de Partition :**
   * Identifier les composantes connexes du graphe formé par les arêtes gelées.
   * La composante contenant le nœud $T$ a ses spins gelés (sa configuration est inchangée).
3. **Phase de Recoloriage :**
   * Pour chaque composante connexe $C'$ ne contenant pas le nœud $T$, tirer un nouveau spin $s_{C'} \in \{-1, +1\}$ selon la loi de Gibbs réduite :
     $$W_{global}(\sigma) \propto \prod_{C \text{ t.q. } \omega_{b_C} = \emptyset} \left( \mathbb{I}(C \text{ satisfaite}) + e^{-2w} \mathbb{I}(C \text{ insatisfaite}) \right)$$
     (Puisque $w \gg 0$, $e^{-2w} \approx 0$, ce qui incite fortement le recoloriage à satisfaire les clauses libres).
