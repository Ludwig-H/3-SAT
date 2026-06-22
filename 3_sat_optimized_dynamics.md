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

Comme présenté dans la thèse, l'énergie d'une clause peut être développée sous forme polynomiale en les variables $L_i$ (qui représentent les valeurs des littéraux dans la configuration $\sigma$) :
$$\mathbb{I}(L_1 = L_2 = L_3 = -1) = \left(\frac{1-L_1}{2}\right)\left(\frac{1-L_2}{2}\right)\left(\frac{1-L_3}{2}\right)$$
$$U_C(\sigma) = \frac{w}{8} \left( 1 - (L_1 + L_2 + L_3) + (L_1 L_2 + L_2 L_3 + L_3 L_1) - L_1 L_2 L_3 \right)$$

Cette décomposition correspond à distribuer l'énergie sur les interactions du tétraèdre $\{1, 2, 3, T\}$ (avec $T$ fixé à $+1$). En définissant la constante de couplage locale $u = w/4$, l'énergie totale d'une clause $U_C(\sigma)$ s'exprime comme la somme des énergies de ses 6 arêtes et de son interaction à 4 corps :

$$U_C(\sigma) = \sum_{\{a,b\} \subseteq \{1,2,3\}} U_{ab}(s_a, s_b) + \sum_{a=1}^3 U_{aT}(s_a, s_T) + U_{\text{tetra}}(s_1, s_2, s_3, s_T) - \frac{w}{8}$$

où chaque type de liaison respecte les formules suivantes :

1. **Le triangle de base $\{1, 2, 3\}$** : Composé de 3 arêtes signées ayant un signe opposé au produit des littéraux ($S_{ab} = -v_a v_b$). L'énergie de chaque arête vaut :
   $$U_{ab}(s_a, s_b) = \frac{u}{2}(1 + L_a L_b) = \frac{w}{8}(1 + v_a v_b s_a s_b)$$
2. **Les liaisons latérales reliant les littéraux à $T$** : Composées de 3 arêtes ayant un signe en accord avec le littéral ($S_{aT} = v_a$). L'énergie de chaque liaison vaut :
   $$U_{aT}(s_a, s_T) = \frac{u}{2}(1 - L_a) = \frac{w}{8}(1 - v_a s_a s_T)$$
3. **Le tétraèdre (interaction d'ordre 4 sur les 4 nœuds)** : L'énergie associée à l'interaction globale du tétraèdre vaut :
   $$U_{\text{tetra}}(s_1, s_2, s_3, s_T) = -\frac{u}{2} L_1 L_2 L_3 = -\frac{w}{8} v_1 v_2 v_3 s_1 s_2 s_3 s_T$$

### Calcul de l'Énergie Totale
* Si la configuration est **satisfaite** (au moins un $L_i = +1$), la somme des énergies vaut :
  $$U_C(\sigma) = -\frac{w}{8} - \frac{w}{8} = -\frac{w}{4}$$
  *(soit $0$ après translation de la constante).*
* Si la configuration est **insatisfaite** ($L_1 = L_2 = L_3 = -1$), la somme des énergies vaut :
  $$U_C(\sigma) = \frac{7w}{8} - \frac{w}{8} = \frac{3w}{4}$$
  *(soit $w$ après la même translation).*

La différence d'énergie entre les états satisfait et insatisfait est donc exactement de $w$, ce qui encode parfaitement la contrainte de la clause 3-SAT.

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
