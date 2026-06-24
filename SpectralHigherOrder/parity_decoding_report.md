# Rapport : remplacer la relaxation QP par un décodage de parité

Ce rapport analyse la faiblesse principale de l'implémentation higher-order
actuelle et propose une correction mathématique plus fidèle : remplacer la
relaxation additive continue par un problème de décodage de syndrome pondéré sur
les arêtes.

Le point central est simple : les triangles ne portent pas une contrainte
continue de somme, mais une contrainte de parité modulo 2.

---

## 1. Contexte

Dans la formulation higher-order, chaque arête signée effective

```math
e=\{i,j\}
```

porte un signe

```math
\varepsilon_e\in\{-1,+1\}
```

et un poids

```math
W_e\ge 0.
```

Pour une configuration de spins de sommets

```math
\sigma_i\in\{-1,+1\},
```

on définit la variable d'arête

```math
y_e=\varepsilon_e\sigma_i\sigma_j.
```

Elle indique si l'arête est satisfaite :

```math
y_e=+1 \quad \Longleftrightarrow \quad e \text{ satisfaite},
```

```math
y_e=-1 \quad \Longleftrightarrow \quad e \text{ insatisfaite}.
```

On introduit ensuite l'indicatrice d'insatisfaction

```math
p_e=\frac{1-y_e}{2}\in\{0,1\}.
```

Ainsi :

```math
p_e=0 \quad \Longleftrightarrow \quad e \text{ satisfaite},
```

```math
p_e=1 \quad \Longleftrightarrow \quad e \text{ insatisfaite}.
```

Après transfert LP des arêtes vers les triangles, on dispose :

1. de poids triangulaires `omega_t`;
2. de résidus d'arêtes `rho_e`;
3. d'un ensemble de triangles `t`, chacun contenant trois arêtes.

Le problème pratique est de prédire un motif d'arêtes insatisfaites `p`, puis de
le projeter vers des spins `sigma`.

---

## 2. Le défaut de la relaxation QP actuelle

L'implémentation actuelle remplace la contrainte triangulaire discrète par une
relaxation quadratique continue :

```math
\min_{0\le p_e\le 1}
\sum_e W_e p_e
+
\kappa\sum_t \omega_t
\left(
\sum_{e\in\partial t}p_e-b_t
\right)^2.
```

Ici

```math
b_t=\frac{1-\prod_{e\in\partial t}\varepsilon_e}{2}.
```

Donc :

```math
b_t=0
```

pour un triangle non frustré, et

```math
b_t=1
```

pour un triangle frustré.

Cette relaxation semble naturelle, mais elle change la nature du problème. Elle
dit :

```math
\sum_{e\in\partial t}p_e \approx b_t
```

dans les réels, alors que la vraie contrainte combinatoire est :

```math
\sum_{e\in\partial t}p_e \equiv b_t \pmod 2.
```

Cette différence est déterminante.

---

## 3. Exemple fondamental : triangle frustré isolé

Considérons un triangle frustré avec trois arêtes de poids 1. La contrainte
discrète correcte est :

```math
p_1+p_2+p_3 \equiv 1 \pmod 2.
```

Les états de plus basse énergie sont donc :

```math
(1,0,0),\quad (0,1,0),\quad (0,0,1).
```

Ils correspondent à "une seule arête insatisfaite", c'est-à-dire exactement la
physique d'un triangle frustré.

La relaxation QP actuelle résout plutôt :

```math
\min_{0\le p_i\le 1}
p_1+p_2+p_3
+
\kappa(p_1+p_2+p_3-1)^2.
```

Par symétrie, le minimum intérieur vérifie

```math
p_1=p_2=p_3=a.
```

On obtient :

```math
3a = 1-\frac{1}{2\kappa},
```

donc

```math
a=\frac13-\frac{1}{6\kappa}.
```

Pour `kappa=1`, cela donne :

```math
p_1=p_2=p_3=\frac16.
```

Quand `kappa` tend vers l'infini, cela donne :

```math
p_1=p_2=p_3\to \frac13.
```

Donc augmenter `kappa` ne crée jamais le choix discret

```math
(1,0,0),
```

mais renforce au contraire une solution fractionnaire symétrique.

Cette observation explique pourquoi les résultats pratiques sont mauvais : la
relaxation répartit la frustration au lieu de choisir quelle arête sacrifier.

---

## 4. Le bon objet : un syndrome `Z_2`

Pour chaque triangle

```math
t=\{e_1,e_2,e_3\},
```

le produit des signes d'arêtes vaut

```math
s_t=\prod_{e\in\partial t}\varepsilon_e.
```

On définit :

```math
b_t=\frac{1-s_t}{2}.
```

La condition exacte d'intégrabilité locale est :

```math
\prod_{e\in\partial t}y_e=s_t.
```

En variables `p_e=(1-y_e)/2`, elle devient :

```math
\sum_{e\in\partial t}p_e\equiv b_t\pmod 2.
```

Si l'on note `B_2` la matrice incidence arêtes-triangles non orientée, la
contrainte s'écrit :

```math
B_2^\top p = b \pmod 2.
```

Cette équation est un problème de syndrome :

```math
H p = b \pmod 2,
```

où

```math
H = B_2^\top \bmod 2.
```

La tâche n'est donc pas un QP continu, mais un décodage binaire pondéré.

---

## 5. Formulation discrète recommandée

La formulation naturelle est :

```math
\min_{p_e\in\{0,1\}}
\sum_e \lambda_e p_e
```

sous contrainte :

```math
B_2^\top p = b \pmod 2.
```

Le poids `lambda_e` doit représenter le coût de rendre l'arête `e`
insatisfaite. Un choix raisonnable est :

```math
\lambda_e=\rho_e+\sum_{t\supset e}\omega_t.
```

où :

1. `rho_e` est le résidu d'arête non transféré;
2. `sum_{t \supset e} omega_t` est la masse triangulaire qui utilise cette
   arête.

Cette formulation corrige les deux défauts principaux :

1. un triangle frustré ne peut plus produire `p=(1/6,1/6,1/6)`;
2. `p=0` est interdit dès qu'un syndrome frustré doit être expliqué.

Le modèle devient :

```text
choisir un ensemble minimal d'arêtes à violer
tel que chaque triangle ait la bonne parité de violations.
```

C'est exactement la structure higher-order cherchée.

---

## 6. Relation avec la synchronisation `Z_2`

Une fois `p` obtenu, on pose :

```math
y_e=1-2p_e.
```

Puis :

```math
r_e=\varepsilon_e y_e.
```

Si `y` est globalement intégrable, il existe des spins `sigma_i` tels que :

```math
r_{ij}=\sigma_i\sigma_j.
```

En pratique, les contraintes triangulaires ne remplissent pas nécessairement tous
les cycles du graphe. Il faut donc encore projeter vers les sommets par :

```math
\max_{\sigma_i\in\{\pm1\}}
\sum_{e=\{i,j\}} c_e r_e \sigma_i\sigma_j.
```

Cette étape reste nécessaire. Mais elle reçoit maintenant un motif `y` beaucoup
plus discret et plus cohérent localement que celui produit par le QP.

---

## 7. Résolution exacte par MILP

Pour les petites et moyennes instances, le problème de syndrome pondéré peut être
résolu exactement par MILP.

Pour chaque triangle `t`, on impose :

```math
\sum_{e\in\partial t}p_e - b_t = 2z_t.
```

avec :

```math
p_e\in\{0,1\},
```

et

```math
z_t\in\mathbb{Z}.
```

Comme un triangle a trois arêtes, on peut borner `z_t`. Si `b_t=0`, alors :

```math
\sum p_e \in \{0,2\},
```

donc :

```math
z_t\in\{0,1\}.
```

Si `b_t=1`, alors :

```math
\sum p_e \in \{1,3\},
```

donc :

```math
z_t\in\{0,1\}.
```

Dans les deux cas, un binaire auxiliaire suffit :

```math
\sum_{e\in\partial t}p_e = b_t + 2z_t,
\qquad z_t\in\{0,1\}.
```

Le MILP est :

```math
\min \sum_e \lambda_e p_e
```

sous :

```math
\sum_{e\in\partial t}p_e - 2z_t = b_t,
```

```math
p_e,z_t\in\{0,1\}.
```

Cette formulation est exacte pour les contraintes triangulaires locales.

---

## 8. Résolution approchée par belief propagation min-sum

Pour les grandes instances, le MILP exact peut devenir trop coûteux. La méthode
naturelle est alors le min-sum belief propagation sur le graphe facteur :

```text
variables : p_e
facteurs  : triangles t
contrainte: xor(p_e, e in t) = b_t
coût      : lambda_e p_e
```

Chaque variable `p_e` est binaire.

Chaque facteur triangulaire impose :

```math
p_{e_1}\oplus p_{e_2}\oplus p_{e_3}=b_t.
```

### 8.1 Messages variable vers facteur

Le message de l'arête `e` vers le triangle `t` est une paire de coûts :

```math
m_{e\to t}(0),\quad m_{e\to t}(1).
```

Il vaut :

```math
m_{e\to t}(x)
= \lambda_e x
+ \sum_{t'\ni e,\ t'\ne t} m_{t'\to e}(x).
```

On normalise après chaque mise à jour en soustrayant :

```math
\min_x m_{e\to t}(x).
```

### 8.2 Messages facteur vers variable

Pour un triangle

```math
t=\{e_1,e_2,e_3\},
```

le message vers `e_1` est :

```math
m_{t\to e_1}(x_1)
=
\min_{x_2,x_3\in\{0,1\}}
\left[
m_{e_2\to t}(x_2)
+m_{e_3\to t}(x_3)
\right]
```

sous la contrainte :

```math
x_1\oplus x_2\oplus x_3=b_t.
```

Comme il n'y a que deux autres variables, cette minimisation coûte constant.

### 8.3 Décision finale

Après itérations, le coût marginal de l'arête `e` est :

```math
M_e(x)=\lambda_e x+\sum_{t\ni e}m_{t\to e}(x).
```

On décide :

```math
\hat p_e =
\begin{cases}
0, & M_e(0)\le M_e(1),\\
1, & M_e(1)<M_e(0).
\end{cases}
```

Si le syndrome n'est pas satisfait, on peut :

1. relancer avec damping différent;
2. fixer les arêtes les plus confiantes et résoudre les ambiguës localement;
3. corriger les syndromes restants par flips locaux.

Le coût de chaque itération est linéaire dans le nombre d'incidences
triangle-arête, donc `O(|T|)`.

---

## 9. Variante LP : polytope de parité local

Il existe aussi une relaxation linéaire plus fidèle que le QP actuel : le
polytope de parité local.

Pour chaque triangle `t`, on introduit une distribution locale

```math
\mu_t(x_1,x_2,x_3)
```

portée seulement par les configurations satisfaisant :

```math
x_1\oplus x_2\oplus x_3=b_t.
```

On impose :

```math
\sum_x \mu_t(x)=1,
```

```math
\mu_t(x)\ge 0,
```

et les marginales doivent être cohérentes avec les variables globales :

```math
p_e=\sum_x x_e\mu_t(x)
\qquad \text{pour } e\in\partial t.
```

On minimise :

```math
\sum_e \lambda_e p_e.
```

Cette relaxation garde la géométrie discrète locale des triangles. Elle peut
encore être fractionnaire globalement, mais elle ne remplace pas une contrainte
XOR par une simple somme réelle.

---

## 10. Alternative continue non convexe

Si l'on veut conserver une approche spectrale ou différentiable, il faut
remplacer la contrainte additive par une contrainte multiplicative sur les
variables `y_e`.

On peut minimiser :

```math
E(y)
=
-\sum_e \lambda_e y_e
+
\kappa\sum_t\omega_t
\left(
\prod_{e\in\partial t}y_e-s_t
\right)^2
+
\gamma\sum_e(1-y_e^2)^2
```

avec :

```math
y_e\in[-1,1].
```

Le terme

```math
\left(
\prod_{e\in\partial t}y_e-s_t
\right)^2
```

impose la vraie parité multiplicative des triangles.

Le terme

```math
(1-y_e^2)^2
```

pousse les variables vers `-1` ou `+1`.

Cette approche est non convexe, donc elle nécessite :

1. plusieurs redémarrages;
2. un recuit sur `gamma`;
3. une homotopie depuis une solution spectrale;
4. une évaluation finale sur la vraie énergie SAT.

Elle est moins propre que le décodage de syndrome, mais elle est beaucoup plus
fidèle que le QP actuel.

---

## 11. Pipeline recommandé

La correction la plus cohérente serait :

```text
1. Graphe signé étendu
2. Compensation des arêtes
3. Transfert LP vers triangles + résidus
4. Construction du syndrome H p = b mod 2
5. Décodage pondéré :
   - MILP exact pour petites instances
   - min-sum BP pour grandes instances
   - LP parity polytope si l'on veut une relaxation convexe plus fidèle
6. y_e = 1 - 2p_e
7. Synchronisation Z_2 vers sigma_i
8. Réoptimisation des auxiliaires
9. Évaluation SAT réelle
10. WalkSAT ou CDCL warm-start
```

Ce pipeline conserve la logique higher-order jusque dans la phase d'arrondi.
Il évite de seuiller indépendamment des arêtes qui devraient être décidées par
motifs de parité locaux.

---

## 12. Pourquoi cette voie est mathématiquement meilleure

Le QP actuel relaxe :

```math
\sum p_e \equiv b_t \pmod 2
```

en :

```math
\sum p_e \approx b_t.
```

Cette relaxation confond :

1. parité;
2. cardinalité;
3. moyenne continue.

Le décodage de syndrome conserve la structure exacte :

```math
H p = b \pmod 2.
```

Il transforme donc le coeur du problème higher-order en un problème bien connu :

```text
trouver le motif de défauts de poids minimal qui explique un syndrome.
```

Cette formulation est difficile en général, mais elle est le bon problème. Elle
permet ensuite d'utiliser des approximations adaptées, comme min-sum BP, plutôt
qu'une relaxation qui échoue déjà sur le triangle frustré élémentaire.

---

## 13. Recommandation finale

La prochaine version du code devrait remplacer `solve_edge_space_qp` par un
module de décodage de parité :

```python
decode_edge_parity_syndrome(
    edges,
    triangles,
    signs,
    lambda_edges,
    method="minsum",
)
```

qui retourne :

```python
p_hat, y_hat, confidence
```

Ensuite seulement, on applique :

```python
project_edge_spins_to_vertices(...)
```

Le gain attendu n'est pas seulement numérique. Il est structurel : les triangles
frustrés seront traités comme des contraintes XOR locales, et non comme des
contraintes additives molles. C'est la correction mathématique la plus directe
des deux premiers problèmes observés dans l'implémentation actuelle.
