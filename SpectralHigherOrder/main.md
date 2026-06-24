# Spectral Higher Order pour 3-SAT

Ce document décrit une extension "higher-order" du solveur spectral signé pour
3-SAT. L'objectif est de conserver l'encodage exact par graphe signé étendu
(`variables + T + auxiliaires`), puis de transférer autant que possible l'énergie
des arêtes vers des triangles, comme dans la dynamique MCMC triangulaire. On
obtient ensuite une relaxation spectrale dans l'espace des arêtes (`edge-space`)
avant de reconstruire une configuration de spins sur les sommets.

La chaîne proposée est la suivante :

1. Encoder la formule 3-SAT comme un Hamiltonien quadratique signé sur un graphe
   étendu.
2. Agréger et compenser les poids signés des arêtes.
3. Transférer de manière optimisée une partie des poids d'arêtes vers des
   triangles isotropes signés, en conservant des résidus sur certaines arêtes.
4. Construire un Hamiltonien dans l'espace des arêtes, avec variables
   `y_e` indiquant si une contrainte d'arête est satisfaite.
5. Ajouter un terme triangulaire de type Hodge/parité qui encode la cohérence
   locale des triangles.
6. Calculer robustement une prédiction `y_e`.
7. Projeter `y_e` vers des spins de sommets `sigma_i` par synchronisation signee
   `Z_2`, puis évaluer la vraie énergie SAT.

Le point important est que l'objet spectral higher-order ne remplace pas
l'exactitude combinatoire du problème SAT. Il fournit une relaxation plus riche
que le Laplacien signé de sommets, parce qu'elle agit directement sur les
arêtes satisfaites/insatisfaites, c'est-a-dire sur les objets que la dynamique
triangulaire MCMC manipule.

---

## 1. Convention spin et littéraux

Soit une formule CNF avec variables booléennes

```math
x_1,\dots,x_N.
```

On associe à chaque variable un spin

```math
\sigma_i \in \{-1,+1\}.
```

On introduit aussi un spin de référence

```math
T \in \{-1,+1\},
```

qui sera fixé à

```math
T=+1.
```

Pour un littéral `l`, on note :

```math
l = x_i      \quad \Rightarrow \quad \eta_l=+1,
```

```math
l = \neg x_i \quad \Rightarrow \quad \eta_l=-1.
```

La valeur spin du littéral est

```math
L_l = \eta_l \sigma_i T.
```

Avec `T=+1`, le littéral est vrai si et seulement si

```math
L_l=+1.
```

Une clause

```math
C=(l_1 \lor \cdots \lor l_k)
```

est insatisfaite si et seulement si

```math
L_{l_1}=\cdots=L_{l_k}=-1.
```

L'énergie SAT de poids uniforme `u>0` est

```math
U_{\mathrm{SAT}}(\sigma)
= u \sum_{C} \mathbf{1}\{C \text{ insatisfaite}\}.
```

Toutes les constantes additives introduites ci-dessous peuvent être ignorées pour
la minimisation, mais elles doivent être suivies si l'on veut comparer des
valeurs absolues d'énergie.

---

## 2. Arêtes signées et Laplacien signé usuel

Une arête signée entre deux spins `a,b` est définie par :

```math
\varepsilon_{ab}\in\{-1,+1\}, \qquad w_{ab}\ge 0.
```

Elle est satisfaite lorsque

```math
\sigma_a \sigma_b = \varepsilon_{ab}.
```

Son énergie est

```math
E_{ab}
= w_{ab}\mathbf{1}\{\sigma_a\sigma_b\ne\varepsilon_{ab}\}
= \frac{w_{ab}}{2}(1-\varepsilon_{ab}\sigma_a\sigma_b).
```

Si on pose

```math
A_{ab} = \varepsilon_{ab}w_{ab},
```

et

```math
D_{aa}=\sum_b |A_{ab}|,
```

alors le Laplacien signé combinatoire est

```math
L_{\mathrm{sgn}} = D-A.
```

Pour un vecteur réel `z`,

```math
\frac12 z^\top L_{\mathrm{sgn}} z
= \sum_{\{a,b\}} \frac{w_{ab}}{2}(z_a-\varepsilon_{ab}z_b)^2.
```

Sur les spins `z_a=\sigma_a`, cela vaut

```math
\frac12 \sigma^\top L_{\mathrm{sgn}}\sigma
= \sum_{\{a,b\}} w_{ab}(1-\varepsilon_{ab}\sigma_a\sigma_b).
```

Cette quantité est deux fois la somme des énergies d'arêtes ci-dessus. Le
facteur constant ne change pas la minimisation.

---

## 3. Encodage exact des clauses dans le graphe étendu

Le graphe étendu contient :

1. les variables originales `x_i`,
2. le noeud de référence `T`,
3. des noeuds auxiliaires pour les clauses ternaires, ou pour des groupes de
   clauses ternaires qui partagent une même paire orientée.

On construit une liste d'arêtes signées. Les arêtes opposées sur une même paire
seront ensuite compensées.

### 3.1 Clauses unitaires

Soit une clause unitaire

```math
C=(l_1).
```

Elle est insatisfaite si `L_1=-1`, donc

```math
u\mathbf{1}\{L_1=-1\}
= \frac{u}{2}(1-L_1)
= \frac{u}{2}(1-\eta_1\sigma_1 T).
```

On ajoute donc une arête

```math
(\sigma_1,T)
```

de signe

```math
\varepsilon=\eta_1
```

et de poids `u`.

Avec la convention d'énergie d'arête

```math
\frac{w}{2}(1-\varepsilon\sigma_a\sigma_b),
```

le poids `w=u` reproduit exactement la pénalité unitaire.

### 3.2 Clauses binaires

Soit

```math
C=(l_1\lor l_2).
```

La pénalité est

```math
u\mathbf{1}\{L_1=-1,L_2=-1\}
= \frac{u}{4}(1-L_1-L_2+L_1L_2).
```

Elle s'encode, à constante additive près, par les trois arêtes suivantes :

```math
(\sigma_1,T) \quad \text{signe } \eta_1,\quad \text{poids } u/2,
```

```math
(\sigma_2,T) \quad \text{signe } \eta_2,\quad \text{poids } u/2,
```

```math
(\sigma_1,\sigma_2) \quad
\text{signe } -\eta_1\eta_2,\quad \text{poids } u/2.
```

En effet, la somme des trois énergies d'arêtes vaut

```math
\frac{u}{4}(3-L_1-L_2+L_1L_2),
```

qui diffère de l'énergie SAT binaire par la constante `u/2`.

### 3.3 Clauses ternaires

Soit

```math
C=(l_1\lor l_2\lor l_3).
```

On introduit un spin auxiliaire

```math
s_C\in\{-1,+1\}.
```

L'énergie étendue utilisée dans le solveur spectral signé est

```math
E_C(\sigma,s_C)
= \frac{u}{4}\Big[
(1-L_1)+(1-L_2)+(1-L_3)
+(1-s_CL_1)+(1-s_CL_2)+(1-s_CL_3)
+(1+s_C)
\Big]
```

```math
\qquad
+\frac{u}{4}(L_1L_2+L_1L_3+L_2L_3)
-\frac{5u}{4}.
```

Par énumération des huit valeurs de `(L_1,L_2,L_3)`, on vérifie :

```math
\min_{s_C\in\{-1,+1\}} E_C(\sigma,s_C)
= u\mathbf{1}\{L_1=L_2=L_3=-1\}.
```

Donc l'encodage est exact pour la minimisation après élimination de
l'auxiliaire.

Cette énergie correspond aux 10 arêtes suivantes, toutes de poids `u/2` :

1. trois arêtes variable-référence :

```math
(\sigma_i,T) \quad \text{signe } \eta_i,
```

2. trois arêtes auxiliaire-variable :

```math
(s_C,\sigma_i) \quad \text{signe } \eta_i,
```

3. une arête auxiliaire-référence :

```math
(s_C,T) \quad \text{signe } -1,
```

4. trois arêtes variable-variable :

```math
(\sigma_i,\sigma_j) \quad \text{signe } -\eta_i\eta_j.
```

Les trois arêtes variable-variable sont essentielles pour passer du gadget
"plaquette orientée satisfaite dans un seul état" au vrai OR 3-SAT, qui est
satisfait dès qu'au moins un littéral est vrai.

---

## 4. Mutualisation des auxiliaires

On peut garder un auxiliaire par clause ternaire. C'est toujours correct mais
pas toujours optimal. Si plusieurs clauses partagent la même paire orientée de
littéraux, elles peuvent partager un certificat.

Par exemple, des clauses de la forme

```math
(a \lor b \lor c_r), \qquad r\in R,
```

où `a` et `b` sont les mêmes littéraux orientés, peuvent utiliser un certificat
commun qui indique si la paire `(a,b)` est satisfaite.

La règle sûre est :

```math
\boxed{
\text{mutualiser uniquement par classe de même paire orientée.}
}
```

Il ne faut pas contracter transitivement des auxiliaires qui partagent seulement
une variable, ou qui partagent des paires orientées différentes. Sinon on force
des certificats locaux à devenir identiques alors qu'ils ne représentent pas le
même événement logique.

Dans l'implémentation actuelle, on choisit une paire canonique unique par clause
ternaire, puis on fusionne uniquement les clauses qui ont exactement cette même
paire canonique. Cette règle est conservative : elle évite la sur-contrainte
transitive.

---

## 5. Agrégation et compensation des arêtes

Après avoir ajouté toutes les contributions de toutes les clauses, plusieurs
arêtes peuvent porter sur la même paire de noeuds. Elles peuvent avoir des signes
opposés.

Pour chaque paire non ordonnée

```math
e=\{a,b\},
```

on somme les poids signés :

```math
K_e
= \sum_{\text{contributions } r \text{ sur } e}
\varepsilon_r w_r.
```

Si

```math
K_e=0,
```

l'arête disparaît.

Sinon on définit :

```math
\varepsilon_e = \operatorname{sign}(K_e),
```

```math
W_e = |K_e|.
```

L'énergie quadratique agrégée est donc

```math
H_{\mathrm{edge}}(\sigma)
= \sum_{e=\{a,b\}} \frac{W_e}{2}
(1-\varepsilon_e\sigma_a\sigma_b)
```

à constante additive près.

Cette compensation est mathématiquement importante. Deux contraintes opposées
sur la même paire ne doivent pas créer deux arêtes concurrentes dans le solveur
spectral : elles doivent d'abord s'annuler algébriquement.

---

## 6. Transfert optimise des arêtes vers les triangles

On cherche ensuite à transférer une partie des poids `W_e` vers des triangles,
comme dans la dynamique MCMC triangulaire.

Un triangle est un triplet de noeuds

```math
t=\{a,b,c\}
```

tel que les trois arêtes

```math
e_{ab},e_{bc},e_{ac}
```

existent avec poids non nul après compensation.

On note

```math
\partial t = \{e_{ab},e_{bc},e_{ac}\}.
```

On introduit une variable de transfert

```math
\omega_t\ge 0.
```

La contrainte de conservation des poids d'arêtes est

```math
\sum_{t\supset e}\omega_t \le W_e
\qquad \text{pour toute arête } e.
```

Le résidu sur l'arête `e` est alors

```math
\rho_e
= W_e - \sum_{t\supset e}\omega_t
\ge 0.
```

Un programme linéaire naturel est :

```math
\max_{\omega_t\ge 0}
\sum_t \alpha_t \omega_t
```

sous les contraintes

```math
\sum_{t\supset e}\omega_t \le W_e.
```

Le choix le plus simple est `alpha_t=1`. On peut aussi pondérer les triangles
selon leur intérêt algorithmique :

```math
\alpha_t =
\begin{cases}
\alpha_{\mathrm{frust}}, & \text{triangle frustré},\\
\alpha_{\mathrm{unfrust}}, & \text{triangle non frustré},
\end{cases}
```

ou favoriser les triangles issus directement des gadgets 3-SAT.

Le produit des signes du triangle est

```math
p_t
= \prod_{e\in\partial t}\varepsilon_e.
```

Si `p_t=+1`, le triangle est non frustré : il existe une configuration de spins
qui satisfait les trois arêtes.

Si `p_t=-1`, le triangle est frustré : aucune configuration de spins ne peut
satisfaire les trois arêtes simultanément; le minimum local satisfait deux
arêtes et en viole une.

Le transfert conserve l'énergie, au sens suivant. La partie transférée sur un
triangle `t` est

```math
\Phi_t(\sigma)
= \sum_{e=\{i,j\}\in\partial t}
\frac{\omega_t}{2}
(1-\varepsilon_e\sigma_i\sigma_j).
```

La partie résiduelle est

```math
H_{\mathrm{res}}(\sigma)
= \sum_e \frac{\rho_e}{2}
(1-\varepsilon_e\sigma_i\sigma_j).
```

Ainsi,

```math
H_{\mathrm{edge}}(\sigma)
= \sum_t \Phi_t(\sigma) + H_{\mathrm{res}}(\sigma)
```

à constante additive près, si les poids transférés et résiduels sont définis par
les contraintes ci-dessus.

La différence avec le Laplacien signé classique n'est donc pas l'énergie brute :
c'est la manière de la relaxer et de l'arrondir.

---

## 7. Passage dans l'espace des arêtes

Pour chaque arête signée effective

```math
e=\{i,j\},
```

on définit une variable d'arête

```math
y_e = \varepsilon_e\sigma_i\sigma_j \in \{-1,+1\}.
```

Elle vaut :

```math
y_e=+1 \quad \Longleftrightarrow \quad
\text{l'arête } e \text{ est satisfaite},
```

```math
y_e=-1 \quad \Longleftrightarrow \quad
\text{l'arête } e \text{ est insatisfaite}.
```

En posant

```math
p_e = \frac{1-y_e}{2}\in\{0,1\},
```

`p_e` est l'indicatrice d'insatisfaction de l'arête.

Dans ces variables, la partie résiduelle devient simplement

```math
H_{\mathrm{res}}(y)
= \sum_e \rho_e p_e
= \sum_e \frac{\rho_e}{2}(1-y_e).
```

Les résidus sont donc des champs locaux sur les variables d'arêtes : ils poussent
les arêtes résiduelles vers l'état satisfait `y_e=+1`.

La partie triangulaire transférée devient

```math
\Phi_t(y)
= \omega_t\sum_{e\in\partial t} p_e
= \frac{\omega_t}{2}
\sum_{e\in\partial t}(1-y_e).
```

Pour un triangle non frustré (`p_t=+1`), les configurations intégrables de
plus basse énergie ont

```math
\sum_{e\in\partial t}p_e=0.
```

Pour un triangle frustré (`p_t=-1`), les configurations intégrables de plus basse
énergie ont

```math
\sum_{e\in\partial t}p_e=1.
```

C'est exactement la structure exploitée par la dynamique MCMC triangulaire :
dans un triangle frustré, elle ne cherche pas à satisfaire les trois arêtes;
elle reconnaît que le bon état local satisfait deux arêtes et en viole une.

---

## 8. Contraintes d'intégrabilité

Un coloriage arbitraire des arêtes par `y_e` ne provient pas nécessairement de
spins de sommets.

On définit

```math
r_e = \varepsilon_e y_e.
```

Si `y_e` vient de spins, alors

```math
r_{ij} = \sigma_i\sigma_j.
```

Donc pour tout cycle

```math
C=(e_1,\dots,e_k),
```

on doit avoir

```math
\prod_{e\in C} r_e = +1.
```

En termes de `y_e`, cela devient

```math
\prod_{e\in C} y_e
= \prod_{e\in C}\varepsilon_e.
```

Pour un triangle `t`, la contrainte locale est

```math
\prod_{e\in\partial t} y_e = p_t,
```

où

```math
p_t=\prod_{e\in\partial t}\varepsilon_e.
```

En variables d'insatisfaction `p_e=(1-y_e)/2`, cette condition s'écrit comme une
contrainte de parité :

```math
\sum_{e\in\partial t} p_e
\equiv b_t \pmod 2,
```

avec

```math
b_t = \frac{1-p_t}{2}
=
\begin{cases}
0, & p_t=+1,\\
1, & p_t=-1.
\end{cases}
```

Ainsi :

```math
p_t=+1 \quad \Rightarrow \quad
\text{nombre pair d'arêtes insatisfaites dans } t,
```

```math
p_t=-1 \quad \Rightarrow \quad
\text{nombre impair d'arêtes insatisfaites dans } t.
```

La contrainte de triangle est donc un cas local de la contrainte globale sur
tous les cycles.

---

## 9. Terme de Hodge/parité sur les triangles

On introduit une matrice d'incidence arête-triangle

```math
B_2 \in \{0,1\}^{|E|\times |T_\triangle|},
```

où

```math
(B_2)_{e,t}=1
\quad \Longleftrightarrow \quad
e\in\partial t.
```

Ici on utilise une incidence non orientée, adaptée aux variables de parité
`p_e`. Pour des cochaînes additives orientées classiques, on utiliserait les
signes d'orientation `-1,+1`; mais pour les spins `Z_2`, l'objet exact est la
parité modulo 2.

La contrainte exacte locale est

```math
B_2^\top p \equiv b \pmod 2,
```

où `b_t=(1-p_t)/2`.

Cette équation est le Hodge `Z_2` du problème : les défauts d'arêtes `p_e`
doivent avoir comme bord les frustrations triangulaires `b_t`.

Pour obtenir un calcul spectral ou quadratique réel, on remplace la contrainte
modulo 2 par une relaxation affine :

```math
H_{\mathrm{Hodge}}(p)
= \sum_t \lambda_t
\left(
\sum_{e\in\partial t}p_e - b_t
\right)^2.
```

En notation matricielle :

```math
H_{\mathrm{Hodge}}(p)
= (B_2^\top p - b)^\top
\Lambda
(B_2^\top p - b),
```

avec

```math
\Lambda=\operatorname{diag}(\lambda_t).
```

Un choix naturel est

```math
\lambda_t = \omega_t.
```

Ce terme doit être interprété avec précision :

1. La contrainte exacte est modulo 2.
2. Le terme quadratique réel favorise la branche de basse énergie :
   `0` arête insatisfaite pour un triangle non frustré, `1` arête
   insatisfaite pour un triangle frustré.
3. Il pénalise aussi les états de même parité mais de plus haute énergie,
   par exemple `2` arêtes insatisfaites dans un triangle non frustré ou
   `3` arêtes insatisfaites dans un triangle frustré.

Cette relaxation est donc plus proche de l'objectif de minimisation SAT que le
pur Hodge modulo 2, car elle distingue les branches de basse et haute énergie.

---

## 10. Hamiltonien edge-space complet

Le Hamiltonien discret dans l'espace des arêtes peut être écrit sous la forme

```math
H_{\mathrm{EO}}(p)
=
\underbrace{
\sum_t \omega_t
\sum_{e\in\partial t}p_e
}_{\text{énergie triangulaire transférée exacte}}
+
\underbrace{
\sum_e \rho_e p_e
}_{\text{résidus d'arêtes}}
+
\underbrace{
\kappa
(B_2^\top p-b)^\top\Lambda(B_2^\top p-b)
}_{\text{relaxation Hodge/parité}}
```

avec

```math
p_e\in\{0,1\}.
```

Le premier terme conserve l'énergie transférée.

Le deuxième terme conserve les résidus non transférés.

Le troisième terme n'est pas une énergie supplémentaire du Hamiltonien SAT
original. C'est une pénalisation algorithmique qui favorise les motifs d'arêtes
compatibles avec les triangles MCMC de basse énergie. Le paramètre `kappa`
contrôle la force de cette régularisation higher-order.

Une forme continue relaxée est :

```math
p_e\in[0,1],
```

et

```math
\min_{p\in[0,1]^{|E|}} H_{\mathrm{EO}}(p).
```

Cette formulation est un programme quadratique convexe si `kappa>=0` et
`Lambda` est positive. Elle peut être résolue par QP, par gradient projeté, ou
par une version spectrale augmentée.

---

## 11. Version Laplacienne augmentée

Pour obtenir un objet de type Laplacien, on introduit une variable de référence

```math
R=1.
```

On travaille avec le vecteur augmenté

```math
\tilde p = (p,R).
```

Le terme Hodge affine

```math
(B_2^\top p-b)^\top\Lambda(B_2^\top p-b)
```

s'écrit comme une forme quadratique :

```math
\tilde p^\top
\begin{pmatrix}
B_2\Lambda B_2^\top & -B_2\Lambda b\\
-b^\top\Lambda B_2^\top & b^\top\Lambda b
\end{pmatrix}
\tilde p.
```

La partie

```math
L_{\triangle}=B_2\Lambda B_2^\top
```

est le terme de Hodge sur les arêtes.

Les résidus peuvent être ajoutés comme des champs vers l'état satisfait. En
variables `y_e`, le résidu est

```math
\frac{\rho_e}{2}(1-y_e).
```

Une relaxation quadratique équivalente sur les spins binaires `y_e` consiste à
connecter chaque noeud-arête `e` au noeud de référence `R_y=+1` :

```math
\frac{\rho_e}{2}(y_e-R_y)^2.
```

Pour `y_e\in\{-1,+1\}`, cela vaut :

```math
0 \quad \text{si } y_e=+1,
```

```math
2\rho_e \quad \text{si } y_e=-1.
```

Le facteur `2` peut être absorbé dans l'échelle des poids.

On obtient donc deux représentations équivalentes pour l'implémentation :

1. une QP en variables `p_e in [0,1]`;
2. un Laplacien augmenté en variables centrées `y_e in [-1,+1]` avec noeud de
   référence.

La QP est généralement plus claire mathématiquement. Le Laplacien augmenté est
plus proche du solveur spectral signé existant.

---

## 12. Calcul robuste de `y_e`

Une procédure robuste ne devrait pas se limiter à prendre le signe d'un seul
vecteur propre. La relaxation higher-order peut avoir plusieurs directions
quasi dégénérées.

Une procédure recommandée est :

### 12.1 Résolution continue

Résoudre l'une des relaxations suivantes.

Option A : programme quadratique borné

```math
\min_{0\le p\le 1}
\sum_t \omega_t\sum_{e\in\partial t}p_e
+\sum_e \rho_ep_e
+\kappa(B_2^\top p-b)^\top\Lambda(B_2^\top p-b).
```

Option B : relaxation spectrale augmentée en `y`

```math
\min_{\tilde y}
\tilde y^\top L_{\mathrm{EO}}\tilde y,
\qquad
R_y=+1,
```

où `L_EO` contient :

1. les couplages triangulaires edge-edge,
2. le terme Hodge,
3. les champs résiduels vers le noeud de référence.

Option C : sous-espace spectral

Calculer les `k` plus petits vecteurs propres pertinents de `L_EO`, puis
chercher des arrondis dans leur span.

### 12.2 Scores et confiance

Si la relaxation donne `p_e in [0,1]`, on définit :

```math
\hat y_e = \operatorname{sign}(1-2p_e),
```

et une confiance

```math
c_e = |1-2p_e|.
```

Si la relaxation donne directement une coordonnée réelle `z_e`, on prend :

```math
\hat y_e = \operatorname{sign}(z_e),
```

```math
c_e = |z_e|.
```

Il est utile de renormaliser les confiances, par exemple :

```math
c_e \leftarrow
\left(\rho_e+\sum_{t\supset e}\omega_t\right)
\cdot |1-2p_e|.
```

Ainsi, une arête est considérée fiable si :

1. elle est fortement pondérée dans le Hamiltonien;
2. sa relaxation est loin de l'indécision `p_e=1/2`.

### 12.3 Arrondi par seuils multiples

Au lieu de fixer le seuil à `1/2`, on teste plusieurs seuils :

```math
\tau\in\mathcal T \subset [0,1],
```

et on définit

```math
\hat y_e^{(\tau)}
=
\begin{cases}
+1, & p_e\le \tau,\\
-1, & p_e>\tau.
\end{cases}
```

Chaque candidat `\hat y^{(\tau)}` est ensuite projeté vers des spins `sigma`
et évalué sur la vraie formule SAT.

Cette étape est analogue au sweep cut dans le clustering spectral.

### 12.4 Réparation locale dans l'espace des arêtes

Après arrondi, on peut améliorer `y` en effectuant des flips locaux d'arêtes :

```math
y_e \leftarrow -y_e,
```

acceptés s'ils diminuent :

```math
H_{\mathrm{EO}}(y).
```

Il faut garder en tête que `y` n'est pas nécessairement intégrable. Cette
réparation locale sert seulement à produire une prédiction d'arêtes plus
cohérente avant projection vers les sommets.

---

## 13. Projection de `y_e` vers les spins `sigma_i`

La prédiction d'arêtes `\hat y_e` ne provient pas nécessairement d'une
configuration de sommets. Il faut donc la projeter.

On définit :

```math
\hat r_e = \varepsilon_e \hat y_e.
```

Si `\hat y` était parfaitement intégrable, on aurait

```math
\hat r_{ij}=\sigma_i\sigma_j.
```

La projection naturelle est donc :

```math
\max_{\sigma_i\in\{-1,+1\}}
\sum_{e=\{i,j\}} c_e \hat r_e \sigma_i\sigma_j.
```

Équivalemment :

```math
\min_{\sigma_i\in\{-1,+1\}}
\sum_{e=\{i,j\}} c_e
\mathbf{1}\{\sigma_i\sigma_j\ne \hat r_e\}.
```

C'est une synchronisation signée `Z_2`, ou un problème de défrustration
pondérée.

### 13.1 Projection spectrale

Construire une matrice signée

```math
R_{ij}=c_{ij}\hat r_{ij}.
```

Puis

```math
D_{ii}=\sum_j |R_{ij}|,
```

```math
L_{\mathrm{sync}}=D-R.
```

On calcule le plus petit vecteur propre de `L_sync`, ou de sa version
normalisée :

```math
L_{\mathrm{sync,norm}}
=D^{-1/2}L_{\mathrm{sync}}D^{-1/2}.
```

Ensuite :

```math
\hat\sigma_i=\operatorname{sign}(v_i).
```

Le noeud `T` doit être fixé :

```math
\hat\sigma_T=+1.
```

En pratique, il vaut mieux imposer `T=+1` par condition de Dirichlet ou par
champ très fort, plutôt que de simplement réaligner le vecteur propre après
coup.

### 13.2 Projection par propagation sur composantes

Une alternative plus combinatoire :

1. trier les arêtes par confiance décroissante;
2. construire un arbre couvrant maximum par composante;
3. propager les spins le long de l'arbre avec la règle

```math
\sigma_j = \hat r_{ij}\sigma_i;
```

4. utiliser les arêtes restantes pour corriger localement les contradictions.

Cette méthode est rapide et fournit souvent un bon point de départ pour une
recherche locale.

### 13.3 Raffinement local

Après projection, on raffine `sigma` directement dans l'espace des sommets en
minimisant :

```math
U_{\mathrm{SAT}}(\sigma)
```

ou l'énergie quadratique étendue avec les auxiliaires réoptimisés.

Des options naturelles :

1. WalkSAT warm-start;
2. flips de spins pondérés par gain SAT;
3. décimation spectrale répétée;
4. CDCL avec polarités initiales guidées par `sigma`.

---

## 14. Rôle des auxiliaires dans la projection

Le graphe étendu contient des noeuds auxiliaires. La synchronisation `Z_2` peut
leur attribuer des spins, mais il ne faut pas les traiter comme des variables
physiques finales.

La sortie SAT est uniquement :

```math
(\sigma_1,\dots,\sigma_N).
```

Une fois les variables originales reconstruites, chaque auxiliaire doit être :

1. ignoré pour l'affectation finale;
2. ou réoptimisé localement selon son gadget;
3. ou recalculé comme certificat de la clause/groupe qu'il représente.

Pour une clause ternaire isolée, on prend :

```math
s_C\in
\operatorname*{argmin}_{s\in\{-1,+1\}}
E_C(\sigma,s).
```

La vraie énergie à reporter est toujours le nombre de clauses SAT
insatisfaites, pas l'énergie du graphe relaxé.

---

## 15. Comparaison avec le Laplacien signé de sommets

Le Laplacien signé de sommets relaxe directement :

```math
\min_{\sigma}
\sum_e \frac{W_e}{2}
(1-\varepsilon_e\sigma_i\sigma_j).
```

Il ne voit les triangles que via leurs arêtes.

La voie edge-space ajoute une couche :

```math
\sigma
\longmapsto
y_e=\varepsilon_e\sigma_i\sigma_j.
```

Les triangles deviennent alors des contraintes directes entre variables
d'arêtes :

```math
\prod_{e\in\partial t} y_e = p_t,
```

ou

```math
B_2^\top p \equiv b \pmod 2.
```

Cela encode explicitement l'information que la dynamique MCMC triangulaire
utilise : dans un triangle frustré, le bon état local n'est pas "tout
satisfaire", mais "satisfaire deux arêtes sur trois".

Le prix à payer est l'étape de projection :

```math
y \longmapsto \sigma.
```

Cette étape est indispensable, car un coloriage d'arêtes peut violer des cycles
globaux même s'il satisfait beaucoup de contraintes triangulaires locales.

---

## 16. Algorithme complet proposé

### Entrée

Une formule CNF 3-SAT, éventuellement avec clauses de taille 1, 2 et 3 après
prétraitement.

### Étape 1 : prétraitement logique

1. propagation unitaire sûre;
2. suppression des littéraux purs;
3. suppression des tautologies;
4. normalisation des clauses;
5. comptage des clauses vides créées par les fixations.

### Étape 2 : graphe signé étendu

1. créer les noeuds variables;
2. ajouter `T`;
3. créer ou mutualiser les auxiliaires ternaires;
4. ajouter les arêtes signées des clauses unitaires, binaires et ternaires.

### Étape 3 : compensation

Pour chaque paire de noeuds :

```math
K_e=\sum_r \varepsilon_r w_r.
```

Si `K_e=0`, supprimer l'arête. Sinon :

```math
W_e=|K_e|,\qquad \varepsilon_e=\operatorname{sign}(K_e).
```

### Étape 4 : transfert LP vers triangles

1. construire une liste de triangles candidats;
2. résoudre

```math
\max_{\omega\ge 0}\sum_t\alpha_t\omega_t
```

sous

```math
\sum_{t\supset e}\omega_t\le W_e;
```

3. définir

```math
\rho_e=W_e-\sum_{t\supset e}\omega_t.
```

### Étape 5 : edge-space

Créer une variable d'arête

```math
y_e\in\{-1,+1\}
```

et

```math
p_e=\frac{1-y_e}{2}.
```

Pour chaque triangle :

```math
b_t=\frac{1-\prod_{e\in\partial t}\varepsilon_e}{2}.
```

### Étape 6 : Hodge/parité

Construire `B_2` et le terme :

```math
(B_2^\top p-b)^\top\Lambda(B_2^\top p-b).
```

Résoudre une relaxation :

```math
\min_{0\le p\le 1}
\sum_t\omega_t\sum_{e\in\partial t}p_e
+\sum_e\rho_ep_e
+\kappa(B_2^\top p-b)^\top\Lambda(B_2^\top p-b).
```

### Étape 7 : arrondi robuste de `y`

1. calculer les confiances `c_e`;
2. tester plusieurs seuils;
3. éventuellement effectuer une réparation locale dans l'espace des arêtes.

### Étape 8 : synchronisation `Z_2`

Pour chaque candidat `y`, calculer

```math
\hat r_e=\varepsilon_e\hat y_e.
```

Résoudre :

```math
\max_{\sigma\in\{\pm1\}^{V}}
\sum_e c_e\hat r_e\sigma_i\sigma_j.
```

Fixer toujours

```math
\sigma_T=+1.
```

### Étape 9 : extraction SAT

1. garder les spins des variables originales;
2. réoptimiser ou ignorer les auxiliaires;
3. évaluer le nombre réel de clauses SAT insatisfaites;
4. garder le meilleur candidat;
5. lancer WalkSAT ou une recherche locale si nécessaire.

---

## 17. Points de vigilance

### 17.1 Exactitude

L'encodage par graphe signé étendu est exact pour la minimisation après
élimination des auxiliaires.

Le transfert vers triangles conserve l'énergie si les résidus sont conservés.

La relaxation Hodge/parité n'est pas une preuve de satisfaisabilité. C'est une
régularisation algorithmique higher-order.

### 17.2 Triangles locaux versus cycles globaux

Les triangles imposent une cohérence locale :

```math
\prod_{e\in\partial t}y_e=p_t.
```

Mais la reconstruction de spins exige une cohérence sur tous les cycles :

```math
\prod_{e\in C}y_e=\prod_{e\in C}\varepsilon_e.
```

Si le complexe triangulaire remplit tous les cycles, les contraintes de
triangles suffisent presque. Dans un graphe SAT creux, il restera généralement
des cycles longs non remplis. La synchronisation `Z_2` est donc indispensable.

### 17.3 Résidus

Une arête non transférée ne doit pas disparaître. Son résidu

```math
\rho_e
```

doit apparaître comme champ local dans l'espace des arêtes :

```math
\rho_e p_e
```

ou, en variables `y`,

```math
\frac{\rho_e}{2}(1-y_e).
```

Sans ce terme, le modèle higher-order oublierait toutes les contraintes qui ne
participent pas à des triangles transférés.

### 17.4 Normalisation

Les poids peuvent être très hétérogènes. Il peut être utile de normaliser :

```math
\lambda_t = \frac{\omega_t}{\sqrt{d_{e_1}d_{e_2}d_{e_3}}},
```

ou d'utiliser des degrés d'arêtes :

```math
d_e = \rho_e+\sum_{t\supset e}\omega_t.
```

La normalisation améliore souvent la stabilité numérique, mais elle modifie
l'objectif énergétique exact. Il faut donc toujours réévaluer les candidats sur
la vraie énergie SAT.

---

## 18. Résumé conceptuel

Le solveur spectral signé classique travaille sur les sommets :

```math
\sigma_i.
```

Le solveur higher-order proposé travaille d'abord sur les arêtes :

```math
y_e=\varepsilon_e\sigma_i\sigma_j.
```

Les triangles MCMC deviennent alors des contraintes naturelles de parité :

```math
B_2^\top p \equiv b \pmod 2.
```

La relaxation Hodge réelle

```math
(B_2^\top p-b)^\top\Lambda(B_2^\top p-b)
```

injecte cette information triangulaire dans le calcul spectral.

Les résidus d'arêtes restent des champs locaux :

```math
\rho_ep_e.
```

Enfin, la synchronisation `Z_2`

```math
\max_\sigma\sum_e c_e\varepsilon_e\hat y_e\sigma_i\sigma_j
```

projette le coloriage d'arêtes vers une configuration de variables SAT.

Cette approche est l'analogue spectral le plus naturel de la dynamique MCMC
triangulaire : elle ne se contente pas de sommer des arêtes dans un Laplacien de
sommets, mais spectralise directement les contraintes satisfaites ou
insatisfaites, puis réintègre le résultat dans l'espace des variables.
