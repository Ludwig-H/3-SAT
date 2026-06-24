# MCMC Higher-Order pour 3-SAT

Ce document décrit une voie MCMC higher-order pour le problème 3-SAT. La
première partie reprend exactement la philosophie du schéma
`SpectralHigherOrder` jusqu'au transfert linéaire des poids d'arêtes vers des
triangles. À partir de là, on abandonne la relaxation spectrale et on revient à
une dynamique discrète sur spins, fondée sur :

1. un gel de type Swendsen-Wang sur les triangles transférés ;
2. un gel de type Swendsen-Wang sur les arêtes résiduelles ;
3. une optimisation explicite des flips de clusters obtenus ;
4. une mémoire de la meilleure configuration, comme dans WalkSAT.

Le point central est le suivant : le gel higher-order produit une partition de
grands blocs de spins cohérents avec la partie quadratique et triangulaire du
Hamiltonien, mais le choix des flips de ces blocs ne doit pas être laissé à un
simple Metropolis-Hastings local. Dans le contexte 3-SAT, il est plus pertinent
d'utiliser les clusters comme une grande variable de voisinage, puis de résoudre
un problème SAT/MaxSAT réduit sur les flips de clusters.

On notera ci-dessous :

- `u_sat > 0` le poids de pénalité d'une clause insatisfaite ;
- `beta >= 0` l'inverse de température de la dynamique de gel.

Si une implémentation utilise la lettre `u` pour l'inverse de température, il
faut éviter de la confondre avec le poids SAT `u_sat`.

---

## 1. Convention spin du problème 3-SAT

On considère une formule CNF avec variables booléennes

```math
x_1,\dots,x_N.
```

À chaque variable on associe un spin

```math
\sigma_i\in\{-1,+1\}.
```

On introduit aussi un spin de référence

```math
T\in\{-1,+1\},
```

qui est fixé à

```math
T=+1.
```

Le rôle de `T` est double :

1. il permet de représenter les champs locaux comme des arêtes signées vers un
   sommet de référence ;
2. il fixe la jauge globale : le cluster contenant `T` ne devra jamais être
   inversé.

Pour un littéral `l`, on note

```math
l=x_i \quad\Rightarrow\quad \eta_l=+1,
```

```math
l=\neg x_i \quad\Rightarrow\quad \eta_l=-1.
```

La valeur spin du littéral est

```math
L_l=\eta_l\sigma_i T.
```

Avec `T=+1`, le littéral est vrai si et seulement si

```math
L_l=+1.
```

Une clause

```math
C=(l_1\lor\cdots\lor l_k)
```

est insatisfaite si et seulement si

```math
L_{l_1}=\cdots=L_{l_k}=-1.
```

L'énergie SAT exacte est

```math
U_{\mathrm{SAT}}(\sigma)
= u_{\mathrm{sat}}
\sum_{C}\mathbf{1}\{C\text{ insatisfaite}\}.
```

Le but algorithmique est de minimiser cette quantité sur les spins originaux.
Les auxiliaires introduits plus bas ne sont que des variables internes.

---

## 2. Graphe signé étendu : variables, `T`, auxiliaires

Le graphe étendu contient :

1. les sommets des variables originales ;
2. le sommet de référence `T` ;
3. des sommets auxiliaires attachés aux clauses ternaires, ou à des classes de
   clauses ternaires partageant une même paire orientée.

Une arête signée entre deux sommets `a,b` porte :

```math
\varepsilon_{ab}\in\{-1,+1\},
\qquad
w_{ab}\ge 0.
```

Elle est satisfaite lorsque

```math
\sigma_a\sigma_b=\varepsilon_{ab}.
```

Son énergie est

```math
E_{ab}(\sigma)
=w_{ab}\mathbf{1}\{\sigma_a\sigma_b\ne\varepsilon_{ab}\}
=\frac{w_{ab}}{2}(1-\varepsilon_{ab}\sigma_a\sigma_b).
```

Cette convention est celle qui rend la compensation des arêtes opposées
immédiate.

### 2.1 Clauses unitaires

Pour une clause unitaire

```math
C=(l_1),
```

on a

```math
u_{\mathrm{sat}}\mathbf{1}\{L_1=-1\}
=\frac{u_{\mathrm{sat}}}{2}(1-L_1)
=\frac{u_{\mathrm{sat}}}{2}(1-\eta_1\sigma_1T).
```

On ajoute donc l'arête

```math
(\sigma_1,T)
```

de signe

```math
\varepsilon=\eta_1
```

et de poids

```math
w=u_{\mathrm{sat}}.
```

Cette arête reproduit exactement la pénalité de la clause unitaire.

### 2.2 Clauses binaires

Pour une clause binaire

```math
C=(l_1\lor l_2),
```

la pénalité exacte vaut

```math
u_{\mathrm{sat}}\mathbf{1}\{L_1=-1,L_2=-1\}
=\frac{u_{\mathrm{sat}}}{4}(1-L_1-L_2+L_1L_2).
```

À constante additive près, elle est représentée par trois arêtes de poids
`u_sat/2` :

```math
(\sigma_1,T)
\quad\text{de signe}\quad
\eta_1,
```

```math
(\sigma_2,T)
\quad\text{de signe}\quad
\eta_2,
```

```math
(\sigma_1,\sigma_2)
\quad\text{de signe}\quad
-\eta_1\eta_2.
```

La somme des trois énergies d'arêtes est

```math
\frac{u_{\mathrm{sat}}}{4}(3-L_1-L_2+L_1L_2),
```

qui diffère de la vraie pénalité binaire par la constante
`u_sat/2`. La minimisation est donc inchangée.

### 2.3 Clauses ternaires et auxiliaire

Pour une clause ternaire

```math
C=(l_1\lor l_2\lor l_3),
```

on introduit un auxiliaire

```math
s_C\in\{-1,+1\}.
```

L'encodage quadratique étendu utilisé est :

```math
E_C(\sigma,s_C)
= \frac{u_{\mathrm{sat}}}{4}
\Big[
(1-L_1)+(1-L_2)+(1-L_3)
```

```math
\qquad
+(1-s_CL_1)+(1-s_CL_2)+(1-s_CL_3)
+(1+s_C)
\Big]
```

```math
\qquad
+\frac{u_{\mathrm{sat}}}{4}(L_1L_2+L_1L_3+L_2L_3)
-\frac{5u_{\mathrm{sat}}}{4}.
```

Par énumération des huit valeurs possibles de `(L_1,L_2,L_3)`, on obtient :

```math
\min_{s_C\in\{-1,+1\}}E_C(\sigma,s_C)
=u_{\mathrm{sat}}\mathbf{1}\{L_1=L_2=L_3=-1\}.
```

L'encodage est donc exact pour l'optimisation après élimination locale de
l'auxiliaire.

Il correspond aux dix arêtes suivantes, toutes de poids `u_sat/2` :

1. trois arêtes variable-référence :

```math
(\sigma_i,T)
\quad\text{de signe}\quad
\eta_i ;
```

2. trois arêtes auxiliaire-variable :

```math
(s_C,\sigma_i)
\quad\text{de signe}\quad
\eta_i ;
```

3. une arête auxiliaire-référence :

```math
(s_C,T)
\quad\text{de signe}\quad
-1 ;
```

4. trois arêtes variable-variable :

```math
(\sigma_i,\sigma_j)
\quad\text{de signe}\quad
-\eta_i\eta_j.
```

Ces arêtes variable-variable sont indispensables : elles portent l'information
qui distingue le vrai OR 3-SAT d'une simple contrainte de plaquette orientée.

### 2.4 Mutualisation conservative des auxiliaires

Un auxiliaire par clause ternaire est toujours correct. On peut réduire leur
nombre en mutualisant certaines clauses, mais seulement avec une règle stricte :

```math
\boxed{
\text{mutualiser uniquement par classe de même paire orientée.}
}
```

Autrement dit, si plusieurs clauses contiennent exactement la même paire de
littéraux orientés `(a,b)`, elles peuvent partager le même certificat auxiliaire
associé à cette paire. En revanche, il ne faut pas contracter transitivement des
auxiliaires qui partagent seulement une variable ou des paires différentes. Cela
introduirait une contrainte logique absente de la formule originale.

La version conservative actuellement utilisée dans les prototypes
`SpectralHigherOrder` et `MCMCHigherOrder` choisit une seule paire canonique par
clause ternaire : on trie les trois littéraux par indice de variable, puis on
prend les deux premiers littéraux orientés. Deux clauses sont alors mutualisées
uniquement si ce quadruplet

```text
(variable_a, signe_a, variable_b, signe_b)
```

est exactement identique.

Cette règle évite bien la sur-contrainte transitive, mais elle peut manquer des
mutualisations valides. Par exemple, les clauses

```text
(x1 ∨ x3 ∨ x4), (x2 ∨ x3 ∨ x4), (¬x1 ∨ x3 ∨ x4)
```

partagent toutes la paire orientée exacte `(x3,+),(x4,+)`, mais cette paire
n'est pas la paire canonique de ces clauses.

Une amélioration sûre consiste donc à choisir, pour chaque clause ternaire, une
unique paire orientée parmi ses trois paires possibles, mais en privilégiant les
paires réellement partagées :

1. construire toutes les classes de paires orientées exactes ;
2. pour chaque clause, sélectionner la classe qui maximise le nombre de clauses
   couvertes, ou un score pondéré ;
3. en cas d'égalité, utiliser la paire canonique comme règle déterministe ;
4. garantir qu'une clause n'est affectée qu'à une seule classe auxiliaire.

Cette variante reste non transitive : deux clauses ne partagent un auxiliaire
que si elles sont affectées à la même paire orientée exacte. Elle augmente
potentiellement la mutualisation sans fusionner des événements logiques
différents.

---

## 3. Compensation des poids d'arêtes

Après addition de toutes les contributions, plusieurs arêtes peuvent porter sur
la même paire non ordonnée

```math
e=\{a,b\}.
```

Certaines contributions peuvent avoir des signes opposés. On doit alors les
compenser algébriquement avant toute dynamique.

On définit le poids signé agrégé :

```math
K_e
=\sum_{r\text{ contribution sur }e}\varepsilon_r w_r.
```

Si `K_e=0`, l'arête disparaît. Sinon :

```math
\varepsilon_e=\operatorname{sign}(K_e),
\qquad
W_e=|K_e|.
```

À constante additive près, l'énergie quadratique agrégée est :

```math
H_{\mathrm{edge}}(\sigma)
=\sum_{e=\{a,b\}}
\frac{W_e}{2}(1-\varepsilon_e\sigma_a\sigma_b).
```

Cette étape est mathématiquement nécessaire. Deux contraintes opposées sur une
même paire ne doivent pas être vues comme deux forces concurrentes dans la
dynamique : elles s'annulent partiellement ou totalement dans le Hamiltonien.

---

## 4. Transfert LP des poids vers les triangles

On cherche ensuite à transférer autant que possible les poids d'arêtes vers des
triangles signés. Un triangle est un triplet de sommets

```math
t=\{a,b,c\}
```

tel que les trois arêtes

```math
\{a,b\},\{b,c\},\{a,c\}
```

existent après compensation.

On note

```math
\partial t
```

l'ensemble de ses trois arêtes.

Pour chaque triangle admissible, on introduit un poids transféré

```math
\omega_t\ge 0.
```

La contrainte de conservation des poids d'arêtes est :

```math
\sum_{t\supset e}\omega_t\le W_e
\qquad\text{pour toute arête }e.
```

Le résidu sur l'arête `e` est :

```math
\rho_e
=W_e-\sum_{t\supset e}\omega_t
\ge 0.
```

Un programme linéaire naturel est :

```math
\max_{\omega_t\ge 0}
\sum_t \alpha_t\omega_t
```

sous les contraintes précédentes. Le choix `alpha_t=1` maximise la masse totale
transférée. C'est un objectif énergétique simple, mais pas nécessairement le
meilleur objectif algorithmique pour la dynamique de clusters. On peut choisir
des poids différents pour favoriser certains triangles :

```math
\alpha_t
=\alpha_{\mathrm{frust}}
\quad\text{si }t\text{ est frustré},
```

```math
\alpha_t
=\alpha_{\mathrm{unfrust}}
\quad\text{si }t\text{ est non frustré},
```

ou encore donner un bonus aux triangles issus directement des gadgets 3-SAT.

Le document spectral met aussi en évidence l'utilité des degrés d'arêtes

```math
d_e=\rho_e+\sum_{t\supset e}\omega_t.
```

Ils peuvent servir à normaliser ou pondérer le transfert. Dans la voie MCMC, il
faut toutefois rester prudent : une normalisation modifie l'objectif du LP, même
si l'énergie finale reste évaluée sur le Hamiltonien non normalisé. Le bon usage
est donc plutôt de choisir les coefficients `alpha_t` pour orienter le transfert
vers des triangles utiles à la dynamique.

En particulier, les triangles et arêtes incidentes au noeud de référence `T`
doivent être traités séparément. Le noeud `T` est épinglé ; s'il percole trop
vite, il absorbe les variables originales dans un cluster non flippable. Il est
donc souvent préférable d'utiliser un coefficient réduit pour les triangles
contenant `T` :

```math
\alpha_t \leftarrow \lambda_T\alpha_t,
\qquad 0\le \lambda_T\le 1,
\qquad T\in t,
```

ou même d'interdire temporairement ces triangles dans le LP de transfert lors
des phases de diversification. Cette pénalisation ne supprime pas les contraintes
vers `T` : elles restent présentes comme résidus ou comme termes du score SAT.
Elle évite seulement de transformer le champ de référence en gigantesque cluster
épinglé.

Le signe global d'un triangle est :

```math
p_t=\prod_{e\in\partial t}\varepsilon_e.
```

Si `p_t=+1`, le triangle est non frustré : il existe une configuration de spins
qui satisfait simultanément ses trois arêtes.

Si `p_t=-1`, le triangle est frustré : aucune configuration de spins ne peut
satisfaire ses trois arêtes ; le minimum local satisfait exactement deux arêtes
et en viole une.

Le Hamiltonien après transfert s'écrit :

```math
H_{\mathrm{edge}}(\sigma)
=
\sum_t\Phi_t(\sigma)+H_{\mathrm{res}}(\sigma),
```

avec

```math
\Phi_t(\sigma)
=
\sum_{e=\{i,j\}\in\partial t}
\frac{\omega_t}{2}(1-\varepsilon_e\sigma_i\sigma_j),
```

et

```math
H_{\mathrm{res}}(\sigma)
=
\sum_{e=\{i,j\}}
\frac{\rho_e}{2}(1-\varepsilon_e\sigma_i\sigma_j).
```

Ce transfert ne change pas l'énergie. Il ne fait que réorganiser le même
Hamiltonien en une partie triangulaire et une partie résiduelle.

---

## 5. Variables d'arêtes et structure locale des triangles

Pour analyser la dynamique de gel, on définit pour chaque arête effective

```math
e=\{i,j\}
```

la variable

```math
y_e=\varepsilon_e\sigma_i\sigma_j\in\{-1,+1\}.
```

Elle vaut `+1` si l'arête est satisfaite et `-1` si elle est insatisfaite. On
pose aussi

```math
q_e=\frac{1-y_e}{2}\in\{0,1\}.
```

Alors `q_e=1` est l'indicatrice d'insatisfaction de l'arête.

La contribution d'un triangle devient :

```math
\Phi_t(y)
=\omega_t\sum_{e\in\partial t}q_e.
```

Mais les trois variables d'arêtes d'un triangle ne sont pas libres. Pour tout
triangle,

```math
\prod_{e\in\partial t}y_e
=
\prod_{e\in\partial t}\varepsilon_e
=p_t.
```

Donc :

- si `p_t=+1`, le nombre d'arêtes insatisfaites dans le triangle est pair ;
- si `p_t=-1`, le nombre d'arêtes insatisfaites dans le triangle est impair.

Il en résulte :

- triangle non frustré : états locaux possibles à énergie minimale avec
  `0` arête insatisfaite ;
- triangle frustré : états locaux possibles à énergie minimale avec `1` arête
  insatisfaite ;
- dans les deux cas, l'écart entre l'état bas et l'état haut compatible vaut
  `2 omega_t`.

C'est précisément cette structure que la dynamique Swendsen-Wang triangulaire
doit exploiter.

La contrainte triangulaire n'est qu'une contrainte d'intégrabilité locale. Un
coloriage arbitraire des arêtes par `y_e` provient de spins de sommets seulement
si, pour tout cycle `C`,

```math
\prod_{e\in C} y_e
=
\prod_{e\in C}\varepsilon_e.
```

Les triangles imposent cette condition sur les cycles de longueur trois, mais un
graphe SAT creux contient aussi des cycles plus longs. Pour la voie MCMC, cette
observation sert surtout de diagnostic :

- un gel triangulaire qui respecte les parités locales peut malgré tout produire
  des clusters peu utiles si les cycles longs restent contradictoires ;
- les résidus `rho_e` ne doivent jamais être ignorés, car ils portent souvent
  l'information des contraintes qui ne participent pas aux triangles ;
- les statistiques de défauts d'arêtes `q_e` par triangle donnent un indicateur
  plus fin que la seule taille des clusters.

On peut suivre par exemple la fraction de triangles non frustrés ayant `0`, `2`
ou `3` arêtes insatisfaites, et la fraction de triangles frustrés ayant `1` ou
`3` arêtes insatisfaites. Une bonne configuration locale doit concentrer la
masse sur `0` pour les triangles non frustrés et sur `1` pour les triangles
frustrés.

---

## 6. Dynamique de gel higher-order

La configuration courante est un vecteur de spins sur le graphe étendu :

```math
\sigma\in\{-1,+1\}^{V_{\mathrm{ext}}}.
```

Elle contient les variables originales, le sommet `T` et les auxiliaires. Le
spin `T` est fixé à `+1` en permanence.

À chaque sweep, on tire des liaisons gelées, puis on prend les composantes
connexes de ces liaisons. Ces composantes sont les clusters.

### 6.1 Gel des arêtes résiduelles

Pour une arête résiduelle

```math
e=\{i,j\}
```

de poids `rho_e`, on regarde si elle est satisfaite :

```math
\varepsilon_e\sigma_i\sigma_j=+1.
```

Si elle est insatisfaite, on ne la gèle pas.

Si elle est satisfaite, on la gèle avec probabilité

```math
p_{\mathrm{edge}}(e)
=1-\exp(-\beta\rho_e).
```

Cette règle est la règle Swendsen-Wang usuelle pour une arête de pénalité

```math
\rho_e\mathbf{1}\{\text{arête insatisfaite}\}.
```

Dans notre convention d'énergie

```math
\frac{\rho_e}{2}(1-\varepsilon_e\sigma_i\sigma_j),
```

c'est bien `rho_e` qui est payé lorsqu'une arête est violée.

### 6.2 Gel des triangles non frustrés

Soit un triangle transféré `t` de poids `omega_t` avec

```math
p_t=+1.
```

Le minimum local a trois arêtes satisfaites :

```math
y_{e_1}=y_{e_2}=y_{e_3}=+1.
```

Si le triangle courant n'est pas dans cet état, on ne gèle aucune de ses arêtes
par la règle triangulaire.

S'il est dans cet état bas, on gèle ses trois arêtes simultanément avec
probabilité

```math
p_{\mathrm{tri}}(t)
=1-\exp(-2\beta\omega_t).
```

Sinon, on ne gèle rien.

La raison du facteur `2 omega_t` est que, sur un triangle non frustré, le
prochain niveau compatible a deux arêtes insatisfaites. L'écart d'énergie entre
le niveau bas et le niveau haut est donc :

```math
2\omega_t.
```

### 6.3 Gel des triangles frustrés

Soit un triangle transféré `t` de poids `omega_t` avec

```math
p_t=-1.
```

Le minimum local a exactement une arête insatisfaite et deux arêtes satisfaites.
Il existe donc trois états bas, selon l'arête qui porte la frustration.

Si le triangle courant a trois arêtes insatisfaites, on ne gèle rien.

S'il est dans un état bas, on note `S_t` l'ensemble de ses deux arêtes
satisfaites. On tire alors :

- avec probabilité `exp(-2 beta omega_t)`, aucune arête n'est gelée ;
- avec probabilité `1-exp(-2 beta omega_t)`, on choisit une arête de `S_t`
  uniformément et on la gèle.

Équivalemment, chacune des deux arêtes satisfaites est gelée avec probabilité

```math
\frac{1}{2}(1-\exp(-2\beta\omega_t)),
```

et jamais les deux simultanément par la règle triangulaire frustrée.

Cette règle exprime le fait que le triangle frustré ne doit pas forcer les trois
arêtes à être satisfaites. Il doit au contraire préserver la mobilité de la
frustration locale : l'arête insatisfaite peut se déplacer d'un état bas à un
autre après flips de clusters.

### 6.4 Construction des clusters

Toutes les arêtes gelées, qu'elles viennent des résidus ou des triangles, sont
ajoutées dans une structure union-find. Les composantes connexes obtenues sont :

```math
K_1,\dots,K_M.
```

Pour chaque sommet `v`, on note

```math
c(v)\in\{1,\dots,M\}
```

l'indice de son cluster.

Le cluster contenant `T` est spécial. On le note

```math
K_T.
```

Il est épinglé :

```math
K_T\text{ ne doit jamais être flippé.}
```

Cette contrainte n'est pas optionnelle. Elle maintient `T=+1` et fixe la jauge
de vérité. Si on autorise le cluster de `T` à flipper, on inverse la signification
globale de Vrai/Faux et on détruit la convention de lecture des littéraux.

---

## 7. Problème réduit sur les flips de clusters

Une fois les clusters construits, on introduit une variable de flip par cluster :

```math
z_a\in\{-1,+1\},
\qquad
a=1,\dots,M.
```

La convention est :

```math
z_a=+1 \quad\Longleftrightarrow\quad K_a\text{ n'est pas flippé},
```

```math
z_a=-1 \quad\Longleftrightarrow\quad K_a\text{ est flippé}.
```

Le cluster de `T` est fixé :

```math
z_{c(T)}=+1.
```

Après flips, le spin d'un sommet `v` devient :

```math
\sigma'_v=z_{c(v)}\sigma_v.
```

L'objectif exact serait de résoudre :

```math
\min_{z\in\{-1,+1\}^M,\ z_{c(T)}=+1}
U_{\mathrm{SAT}}(\sigma'(z)).
```

Comme les auxiliaires ne font pas partie de la formule SAT originale, il faut
distinguer deux objectifs possibles.

### 7.1 Objectif SAT original

On évalue uniquement les clauses originales sur les variables originales :

```math
U_{\mathrm{SAT}}^{\mathrm{orig}}(z)
=u_{\mathrm{sat}}
\sum_C
\mathbf{1}\{C\text{ insatisfaite sous }\sigma'(z)\}.
```

C'est l'objectif le plus important si le solveur est jugé sur le nombre de
clauses insatisfaites.

Après avoir choisi les flips, on peut réoptimiser localement les auxiliaires
pour le nouvel état des variables originales :

```math
s_C
\in
\arg\min_{s\in\{-1,+1\}}
E_C(\sigma',s).
```

Cette réoptimisation est locale, indépendante clause par clause ou certificat
par certificat, et ne change pas l'affectation SAT retournée.

### 7.2 Objectif étendu

On peut aussi minimiser le Hamiltonien étendu :

```math
H_{\mathrm{ext}}(\sigma'(z))
=
\sum_t\Phi_t(\sigma'(z))
+H_{\mathrm{res}}(\sigma'(z)).
```

Cet objectif est cohérent avec la dynamique de gel et inclut les auxiliaires.
Il est utile comme énergie interne de la chaîne, mais il peut diverger du score
SAT si les auxiliaires ne sont pas réoptimisés.

La recommandation pratique est :

```math
\boxed{
\text{choisir les flips avec l'objectif SAT original, puis réoptimiser les auxiliaires.}
}
```

On peut garder `H_ext` comme diagnostic ou comme terme secondaire, mais le
critère de réussite doit rester le nombre de clauses originales insatisfaites.

---

## 8. Réduction explicite d'une clause en variables de clusters

Soit une clause originale

```math
C=(l_1\lor\cdots\lor l_k),
\qquad k\le 3.
```

Avant flip, la valeur spin du littéral `l_r` est :

```math
L_r^0=\eta_r\sigma_{i_r}T.
```

Après flip du cluster contenant `i_r`, elle devient :

```math
L_r(z)
=z_{c(i_r)}L_r^0.
```

La clause est insatisfaite si et seulement si :

```math
z_{c(i_r)}L_r^0=-1
\qquad
\text{pour tout }r.
```

Donc chaque littéral impose, pour que la clause soit violée, une valeur
spécifique du flip de son cluster :

```math
z_{c(i_r)}=-L_r^0.
```

Cette observation donne une réduction MaxSAT très simple.

Pour chaque clause :

1. on collecte les contraintes de la forme `z_a = b` qui rendraient ses
   littéraux faux ;
2. si deux littéraux du même cluster imposent deux valeurs opposées de `z_a`,
   la clause est automatiquement satisfaite pour tous les flips ;
3. sinon la clause interdit une unique affectation des clusters distincts
   qu'elle touche.

Ainsi, une clause ternaire originale devient une contrainte réduite d'arité au
plus `3`, souvent `1` ou `2` lorsque plusieurs variables appartiennent au même
cluster.

Cette réduction est très importante : elle transforme le choix des flips de
clusters en un petit problème MaxSAT local, au lieu d'une suite de décisions
Metropolis-Hastings indépendantes.

---

## 9. Comment choisir les flips ?

Après gel, les clusters définissent un voisinage de grande taille autour de la
configuration courante. Il faut choisir les flips de ce voisinage. Plusieurs
options sont possibles.

### 9.1 Recoloriage Swendsen-Wang pur

Dans un échantillonneur Swendsen-Wang standard, on recolorie chaque cluster de
manière aléatoire, sous les contraintes imposées par les clusters gelés.

Avantage :

- c'est naturel pour échantillonner une mesure de Gibbs quand la construction
  FK est exacte.

Inconvénient :

- pour 3-SAT, on cherche d'abord une configuration de basse énergie, souvent
  une solution exacte ;
- le recoloriage aléatoire ignore la structure des clauses non satisfaites ;
- il gaspille l'information contenue dans le problème réduit sur clusters.

Cette option est donc utile comme référence de sampling, mais pas comme moteur
principal d'optimisation.

### 9.2 Metropolis-Hastings sur clusters

Une approche simple consiste à proposer un flip de cluster et à l'accepter avec

```math
\alpha=\min(1,\exp(-\beta_{\mathrm{MH}}\Delta U)).
```

Avantage :

- très facile à implémenter ;
- donne une dynamique de Markov contrôlée si l'objectif est l'échantillonnage.

Inconvénients dans 3-SAT :

- une proposition de flip isolé peut être très mauvaise alors qu'une combinaison
  de plusieurs flips serait excellente ;
- les barrières d'énergie sont fortes et discrètes ;
- une clause insatisfaite peut demander une coordination de clusters ;
- à basse température, la chaîne se bloque ;
- à haute température, elle oublie l'objectif.

Dans ce contexte, Metropolis-Hastings est souvent une mauvaise utilisation des
clusters : le gel a construit un voisinage combinatoire riche, puis MH n'en
explore qu'une dimension à la fois.

### 9.3 Descente gloutonne sur flips

On peut calculer pour chaque cluster le gain d'énergie associé à son flip, puis
flipper le meilleur cluster tant qu'il améliore l'énergie.

Avantages :

- rapide ;
- bon mécanisme d'intensification ;
- simple à maintenir avec des deltas de clauses.

Inconvénients :

- se bloque dans des optima locaux ;
- ne coordonne pas bien plusieurs flips interdépendants ;
- dépend fortement de l'ordre de mise à jour.

Cette option est utile comme post-traitement, mais trop myope comme stratégie
principale.

### 9.4 Énumération exacte si le nombre de clusters est petit

Si le nombre de clusters flippables est

```math
m=M-1
```

en excluant `K_T`, et si `m` est suffisamment petit, on peut énumérer tous les
flips :

```math
2^m
```

configurations.

En pratique, cela peut être raisonnable jusqu'à environ `m <= 25` ou `m <= 30`
selon l'implémentation et le budget temps.

Avantage :

- donne le meilleur flip possible dans le voisinage courant.

Inconvénient :

- explose exponentiellement ;
- inadapté quand la température de gel produit beaucoup de clusters.

### 9.5 MILP, MaxSAT ou QUBO réduit

Le problème réduit sur clusters est naturellement un MaxSAT pondéré de petites
clauses :

```math
\min_z
\sum_C w_C
\mathbf{1}\{z\text{ prend l'affectation interdite par }C\}.
```

On peut le confier à :

- un solveur MaxSAT ;
- un solveur MILP ;
- un solveur pseudo-booléen ;
- un QUBO avec variables auxiliaires pour les clauses d'arité `3`.

Avantage :

- exploite directement la structure logique réduite ;
- peut être très puissant si le nombre de clusters est modéré.

Inconvénients :

- dépend d'un solveur externe ou d'un backend plus lourd ;
- le coût par sweep peut devenir trop élevé ;
- le solveur exact peut faire perdre la dynamique si on l'appelle trop souvent.

Cette option est très intéressante en mode intensification périodique ou pour
certifier le meilleur mouvement dans un voisinage important.

### 9.6 WalkSAT réduit sur clusters

La stratégie la plus cohérente avec le contexte 3-SAT est d'utiliser un WalkSAT
ou min-conflicts sur les variables de clusters.

Principe :

1. on construit les clauses réduites induites par les clusters ;
2. on initialise `z_a=+1` pour tous les clusters, c'est-à-dire aucun flip ;
3. tant qu'il reste des clauses réduites violées et que le budget n'est pas
   épuisé :
   - choisir une clause réduite violée ;
   - avec une petite probabilité de bruit, flipper un cluster de cette clause au
     hasard ;
   - sinon flipper le cluster qui minimise le nombre de clauses réduites violées
     après le flip ;
4. garder le meilleur `z` rencontré pendant cette recherche locale.

Avantages :

- cible directement les clauses insatisfaites ;
- gère naturellement les discontinuités de 3-SAT ;
- coordonne plusieurs flips au fil de la recherche ;
- est beaucoup moins fragile que Metropolis-Hastings ;
- profite du fait que les clauses réduites ont arité au plus `3`.

Inconvénients :

- ce n'est pas un échantillonneur exact de Gibbs ;
- il faut maintenir des structures de clauses efficaces ;
- des redémarrages ou du bruit restent nécessaires.

Recommandation :

```math
\boxed{
\text{utiliser WalkSAT réduit sur clusters comme étape principale de recoloriage.}
}
```

Cette stratégie transforme la dynamique MCMC higher-order en un schéma de
large-neighborhood search : le MCMC génère des voisinages structurés, WalkSAT
résout approximativement le meilleur mouvement dans ces voisinages, et une
mémoire globale conserve la meilleure configuration.

---

## 10. Calibration de l'inverse de température

Le paramètre `beta` contrôle la taille des clusters :

- si `beta` est trop petit, presque rien ne gèle, les clusters sont minuscules ;
- si `beta` est trop grand, les clusters deviennent énormes et la mobilité
  chute, surtout si le cluster de `T` absorbe beaucoup de variables.

On veut choisir `beta` pour que le plus grand cluster atteigne une proportion
cible des points, par exemple :

```math
q_\star=0.10.
```

Il faut préciser ce que l'on mesure. La recommandation est :

```math
S_{\max}(\beta)
=
\frac{
\max_{K\ne K_T}|K\cap V_{\mathrm{orig}}|
}{
|V_{\mathrm{orig}}|
}.
```

On mesure donc la plus grande composante flippable en nombre de variables
originales. On suit séparément la taille du cluster de `T` :

```math
S_T(\beta)
=
\frac{|K_T\cap V_{\mathrm{orig}}|}{|V_{\mathrm{orig}}|}.
```

Si `S_T` devient trop grand, beaucoup de variables sont épinglées et la dynamique
perd en mobilité, même si `S_max` semble raisonnable.

### 10.1 Bisection stochastique

La taille moyenne des clusters est généralement croissante en `beta`. Comme le
gel est aléatoire, on utilise une estimation par quelques échantillons.

Procédure :

1. choisir un intervalle `[beta_min,beta_max]` ;
2. pour un `beta` candidat, tirer `R` gels depuis la configuration courante ;
3. calculer la médiane ou la moyenne tronquée de `S_max(beta)` ;
4. si cette valeur est inférieure à `q_star`, augmenter `beta` ;
5. si elle est supérieure à `q_star`, diminuer `beta`.

La médiane est souvent plus stable que la moyenne lorsque des clusters géants
apparaissent sporadiquement.

### 10.2 Adaptation au cours de la recherche

On peut recalibrer `beta` toutes les `A` itérations, plutôt qu'à chaque sweep.
Une mise à jour multiplicative simple est :

```math
\log\beta
\leftarrow
\log\beta
+\gamma(S_{\max}^{\mathrm{target}}-S_{\max}^{\mathrm{obs}}),
```

avec un petit pas `gamma > 0`, suivie d'un clamp dans un intervalle admissible.

Pour l'optimisation, une politique naturelle est :

- début : clusters modestes, `q_star` entre `0.05` et `0.10` ;
- milieu : clusters autour de `0.10` à `0.20` ;
- intensification : essayer ponctuellement des `q_star` plus grands, mais
  seulement avec une résolution réduite robuste sur les flips.

### 10.3 Diagnostics issus de l'espace des arêtes

Le document `SpectralHigherOrder` rappelle que les variables naturelles des
triangles sont les défauts d'arêtes

```math
q_e=\frac{1-y_e}{2}.
```

Même si l'algorithme MCMC reste dans l'espace discret des spins, ces variables
donnent de bons diagnostics de calibration. En plus de `S_max` et `S_T`, il faut
suivre :

1. la masse transférée totale `sum_t 3 omega_t` et la masse résiduelle
   `sum_e rho_e` ;
2. la fraction de cette masse portée par des triangles contenant `T` ;
3. la distribution locale de `sum_{e in partial t} q_e` séparément pour les
   triangles frustrés et non frustrés ;
4. le degré d'arête

```math
d_e=\rho_e+\sum_{t\supset e}\omega_t;
```

5. la part des arêtes de grand degré qui sont incidentes à `T`.

Ces quantités indiquent si le transfert LP construit des motifs higher-order
utiles ou s'il concentre la masse sur le champ de référence. Un symptôme
problématique est :

```text
S_T élevé, S_max faible, et forte masse transférée sur des triangles contenant T.
```

Dans ce cas, augmenter `beta` ne résout pas le problème : cela renforce surtout
le cluster épinglé. Il faut plutôt réduire le gel incident à `T`, pénaliser les
triangles contenant `T` dans le LP, ou exclure ces triangles pendant les phases de
diversification.

---

## 11. Algorithme recommandé

L'algorithme complet est le suivant.

### 11.1 Prétraitement

1. Lire la formule CNF.
2. Supprimer les tautologies.
3. Agréger les clauses identiques si l'on travaille en MaxSAT pondéré.
4. Appliquer éventuellement propagation unitaire et littéraux purs si l'on veut
   réduire le problème avant la dynamique. Il faut alors conserver les constantes
   d'énergie induites par les clauses déjà décidées.

### 11.2 Construction du Hamiltonien étendu

1. Créer les sommets des variables originales.
2. Créer le sommet `T`.
3. Encoder les clauses unitaires par des arêtes vers `T`.
4. Encoder les clauses binaires par les trois arêtes signées exactes.
5. Encoder les clauses ternaires avec les auxiliaires et les dix arêtes signées.
6. Mutualiser les auxiliaires par classe de même paire orientée exacte.
   La version conservative prend la paire canonique; une version plus agressive
   mais encore sûre choisit pour chaque clause sa meilleure paire partagée, sans
   affecter une clause à plusieurs certificats.

### 11.3 Compensation et transfert

1. Pour chaque paire de sommets, sommer les poids signés `K_e`.
2. Remplacer par une unique arête de signe `epsilon_e` et poids `W_e`, ou
   supprimer l'arête si `K_e=0`.
3. Énumérer les triangles admissibles.
4. Fixer les coefficients `alpha_t`, en distinguant au minimum :
   - triangles frustrés ;
   - triangles non frustrés ;
   - triangles contenant `T` ;
   - triangles issus directement des gadgets 3-SAT.
5. Résoudre le LP :

```math
\max_{\omega\ge 0}\sum_t\alpha_t\omega_t
\qquad
\text{s.c.}
\qquad
\sum_{t\supset e}\omega_t\le W_e.
```

6. Calculer les résidus :

```math
\rho_e=W_e-\sum_{t\supset e}\omega_t.
```

7. Reporter les diagnostics `masse transférée`, `masse résiduelle`,
   `masse contenant T`, et les degrés d'arêtes `d_e`.

### 11.4 Initialisation des spins

1. Initialiser les variables originales aléatoirement, par heuristique, ou à
   partir d'une meilleure configuration précédente.
2. Fixer `T=+1`.
3. Initialiser chaque auxiliaire par minimisation locale de son gadget.
4. Calculer le score SAT original.
5. Stocker cette configuration comme meilleur état si elle améliore le record.

### 11.5 Sweep higher-order

À chaque sweep :

1. calibrer ou mettre à jour `beta` pour viser une taille de cluster cible ;
2. tirer les gels d'arêtes résiduelles ;
3. tirer les gels triangulaires non frustrés et frustrés ;
4. construire les clusters par union-find ;
5. identifier le cluster `K_T` contenant `T` ;
6. mesurer `S_max`, `S_T` et les défauts triangulaires `q_e` ;
7. construire le problème réduit sur les flips des clusters flippables ;
8. résoudre ce problème réduit :
   - énumération exacte si le nombre de clusters est petit ;
   - sinon WalkSAT réduit sur clusters ;
   - éventuellement MILP/MaxSAT ponctuellement pour intensification ;
9. appliquer le meilleur vecteur de flips trouvé, avec `z_{K_T}=+1` ;
10. réoptimiser les auxiliaires localement ;
11. évaluer le vrai score SAT ;
12. mettre à jour la meilleure configuration globale si le score s'améliore ;
13. redémarrer ou réchauffer si aucune amélioration n'apparaît pendant trop
    longtemps.

### 11.6 Pseudocode

```text
input: CNF formula F, clause weight u_sat
output: best assignment found

G_ext = build_extended_signed_graph(F, T, auxiliaries)
G = compensate_signed_edges(G_ext)
Triangles = enumerate_triangles(G)
alpha = choose_triangle_transfer_weights(
    Triangles,
    bonus_frustrated = alpha_frust,
    bonus_gadget = alpha_gadget,
    penalty_contains_T = lambda_T
)
omega, rho = solve_triangle_transfer_lp(G, Triangles, alpha)
diagnostics = edge_space_diagnostics(G, Triangles, omega, rho, T)

sigma = initialize_original_spins()
sigma[T] = +1
optimize_auxiliaries_locally(sigma)

best_sigma = sigma
best_score = SAT_unsat_count(F, sigma)

beta = calibrate_beta_for_target_cluster_size(
    sigma, Triangles, omega, rho, target=0.10
)
observed_cluster_sizes = []
observed_pinned_sizes = []
observed_triangle_defects = []

for sweep in 1..S:
    frozen_edges = []

    for residual edge e=(i,j):
        if epsilon[e] * sigma[i] * sigma[j] == +1:
            beta_eff = beta * beta_T_factor if T in e else beta
            if rand() < 1 - exp(-beta_eff * rho[e]):
                frozen_edges.append(e)

    for triangle t:
        y = [epsilon[e] * sigma[i_e] * sigma[j_e] for e in boundary(t)]
        beta_eff = beta * beta_T_factor if T in t else beta

        if product_sign(t) == +1:
            if y == [+1,+1,+1]:
                if rand() < 1 - exp(-2 * beta_eff * omega[t]):
                    frozen_edges.extend(boundary(t))

        else:
            if exactly two entries of y are +1:
                if rand() < 1 - exp(-2 * beta_eff * omega[t]):
                    e = choose_one_satisfied_edge_uniformly(boundary(t), y)
                    frozen_edges.append(e)

    clusters = union_find(frozen_edges)
    pinned = cluster_containing(T)
    observed_cluster_sizes.append(
        get_largest_flippable_cluster_proportion(clusters, pinned, V_orig)
    )
    observed_pinned_sizes.append(
        get_pinned_cluster_proportion(clusters, pinned, V_orig)
    )
    observed_triangle_defects.append(
        get_triangle_defect_histogram(sigma, Triangles)
    )

    if sweep % adaptation_period == 0:
        beta = update_beta(
            beta,
            observed_cluster_sizes,
            observed_pinned_sizes,
            target=0.10
        )
        observed_cluster_sizes = []
        observed_pinned_sizes = []
        observed_triangle_defects = []

    reduced = build_reduced_MaxSAT_on_cluster_flips(
        F, sigma, clusters, pinned
    )

    if number_of_flippable_clusters(reduced) <= exact_threshold:
        z_best = exhaustive_cluster_flip_search(reduced)
    else:
        z_best = cluster_WalkSAT(
            reduced,
            start = all_plus,
            noise = p_noise,
            budget = B
        )

    apply_cluster_flips(sigma, clusters, z_best, pinned)
    sigma[T] = +1
    optimize_auxiliaries_locally(sigma)

    score = SAT_unsat_count(F, sigma)
    if score < best_score:
        best_score = score
        best_sigma = projection_to_original_variables(sigma)

    if best_score == 0:
        return best_sigma

return best_sigma
```

---

## 12. Pourquoi cette voie est plus adaptée que le spectral ici

La difficulté rencontrée par la voie spectrale higher-order vient du passage par
une relaxation continue des variables d'arêtes. Les contraintes de parité
triangulaire sont discrètes :

```math
\prod_{e\in\partial t}y_e=p_t.
```

Une relaxation quadratique ou linéaire peut respecter une version moyenne de ces
contraintes sans produire un coloriage d'arêtes intégrable en spins. Le retour
aux spins par synchronisation peut alors perdre l'information essentielle.

La voie MCMC higher-order évite cette rupture :

1. les spins restent discrets pendant toute la dynamique ;
2. les triangles frustrés sont traités comme frustrés, pas comme des triangles à
   satisfaire intégralement ;
3. les arêtes résiduelles ne sont pas oubliées ;
4. le noeud `T` fixe la jauge, mais son cluster doit rester surveillé pour ne
   pas absorber la mobilité ;
5. le choix final des flips cible directement les clauses SAT originales.

Le gel triangulaire n'est donc pas seulement une heuristique géométrique : il
sert à générer des voisinages dont la structure respecte les frustrations
locales du Hamiltonien.

Le document spectral reste toutefois utile pour la voie MCMC sur trois points.

1. Il rappelle que les triangles imposent des contraintes de parité sur les
   défauts d'arêtes :

```math
B_2^\top q \equiv b \pmod 2.
```

La dynamique MCMC doit donc être jugée non seulement par la taille des clusters,
mais aussi par la qualité locale des motifs `q_e` qu'elle préserve ou corrige.

2. Il introduit des confiances d'arêtes, par exemple

```math
c_e
=
\left(\rho_e+\sum_{t\supset e}\omega_t\right)
\cdot \text{confiance locale}.
```

Dans MCMC, ces confiances peuvent guider les redémarrages, les perturbations ou
la sélection de clauses dans le WalkSAT réduit.

3. Il insiste sur la projection finale vers les spins. Même si MCMC reste déjà
dans l'espace des spins, un redémarrage peut être construit à partir d'un
coloriage d'arêtes robuste : trier les arêtes par confiance, propager les spins
sur un arbre couvrant maximum, puis raffiner par WalkSAT. Cela donne une option
de diversification moins aveugle qu'un redémarrage aléatoire.

---

## 13. Statut probabiliste : sampler exact ou heuristique d'optimisation ?

Il faut distinguer deux objectifs.

Si l'on tire les gels selon les règles Swendsen-Wang et que l'on recolorie les
clusters selon la loi conditionnelle correcte, on vise une dynamique de Gibbs
pour le Hamiltonien transféré.

Mais l'algorithme proposé ici remplace le recoloriage aléatoire par une
optimisation des flips de clusters. Il ne s'agit donc plus d'un échantillonneur
Gibbs exact. C'est une heuristique d'optimisation de type :

```math
\text{MCMC pour générer des voisinages}
\quad+\quad
\text{recherche locale SAT pour choisir le meilleur mouvement}.
```

Ce choix est intentionnel. Pour résoudre 3-SAT, la qualité de la descente et la
capacité à conserver le meilleur état sont plus importantes que la fidélité à
une mesure de Gibbs à température fixée.

---

## 14. Mémoire de la meilleure configuration

Comme WalkSAT, l'algorithme doit conserver en permanence :

```math
\sigma_{\mathrm{best}},
\qquad
E_{\mathrm{best}},
\qquad
\#\mathrm{unsat}_{\mathrm{best}}.
```

Cette mémoire doit être mise à jour après chaque sweep, et aussi pendant le
WalkSAT réduit sur clusters si celui-ci trouve un `z` intermédiaire meilleur que
son état final.

Il ne faut pas supposer que la configuration courante est monotone en énergie.
Les gels aléatoires, le bruit WalkSAT et les redémarrages peuvent dégrader
temporairement l'état courant. La meilleure configuration globale est donc le
vrai résultat de l'algorithme.

On peut stocker :

- l'assignation des variables originales ;
- le nombre de clauses insatisfaites ;
- la liste des clauses insatisfaites ;
- le sweep de découverte ;
- la valeur de `beta` ;
- les tailles des clusters au moment de la découverte.

---

## 15. Détails d'implémentation importants

### 15.1 Structures de données

Les objets principaux doivent être stockés en listes creuses :

- liste des arêtes compensées `(i,j,epsilon,W)` ;
- liste des résidus `(i,j,epsilon,rho)` avec `rho > 0` ;
- liste des triangles `(e1,e2,e3,omega,product_sign)` ;
- incidence arête vers triangles pour le LP ;
- degré d'arête `d_e = rho_e + sum_{t superset e} omega_t` ;
- indicateur `contains_T` pour les arêtes et triangles incidents au noeud `T` ;
- incidence variable vers clauses originales ;
- incidence cluster vers clauses réduites.

Les matrices denses doivent être évitées. La dynamique n'a besoin que d'accès
locaux.

### 15.2 Union-find

Le gel produit naturellement une union-find :

```text
make_set(v) for all v
union(i,j) for each frozen edge
clusters = connected_components()
```

Il faut inclure `T` et les auxiliaires dans l'union-find, mais le score SAT
final ne se lit que sur les variables originales.

### 15.3 Auxiliaires

Les auxiliaires sont utiles pour l'encodage exact du Hamiltonien étendu, mais
ils ne doivent pas devenir une source de rigidité artificielle.

Après chaque choix de flips :

```math
s_C\leftarrow
\arg\min_s E_C(\sigma,s).
```

Si plusieurs auxiliaires sont mutualisés, on réoptimise le certificat commun
selon l'énergie totale des clauses qu'il représente.

Cette étape est peu coûteuse comparée au gel et à la résolution du problème
réduit.

### 15.4 Construction rapide du problème réduit

Pour chaque clause originale, on calcule les contraintes de violation en
variables de clusters. Exemple pour une clause ternaire :

```text
for literal l=(eta, variable i):
    a = cluster[i]
    required_value_for_violation[a] = - eta * sigma[i] * sigma[T]
```

Si le même cluster reçoit deux valeurs incompatibles, la clause est satisfaite
pour tout `z` et peut être ignorée dans le problème réduit.

Sinon, on ajoute une clause réduite qui pénalise exactement cette affectation
interdite.

### 15.5 Deltas WalkSAT

Le WalkSAT réduit doit maintenir :

- l'état courant des flips `z` ;
- pour chaque clause réduite, le nombre de littéraux de violation actuellement
  satisfaits ;
- la liste des clauses actuellement violées ;
- pour chaque cluster, les clauses réduites qu'il touche.

Ainsi, le coût d'un flip candidat est proportionnel au nombre de clauses
incidentes au cluster, pas au nombre total de clauses.

### 15.6 Diagnostics edge-space

Même si la dynamique travaille sur des spins de sommets, il faut maintenir des
diagnostics en variables d'arêtes :

```math
y_e=\varepsilon_e\sigma_i\sigma_j,
\qquad
q_e=\frac{1-y_e}{2}.
```

Pour chaque sweep, on peut calculer :

- histogramme de `sum q_e` sur les triangles non frustrés ;
- histogramme de `sum q_e` sur les triangles frustrés ;
- masse de résidus violés `sum_e rho_e q_e` ;
- masse triangulaire violée `sum_t omega_t sum_{e in partial t} q_e` ;
- part de ces masses portée par des arêtes ou triangles contenant `T`.

Ces métriques permettent de distinguer deux situations qui se ressemblent si
l'on regarde seulement le nombre de clauses insatisfaites :

1. la configuration est mauvaise parce que les défauts locaux sont mal placés ;
2. la configuration est localement cohérente, mais la dynamique manque de
   mobilité globale à cause de `K_T` ou de cycles longs.

Dans le second cas, augmenter l'intensification WalkSAT peut être moins efficace
qu'un redémarrage guidé par les arêtes de faible confiance.

### 15.7 Redémarrages

Si aucune amélioration du meilleur score n'est observée pendant `R` sweeps :

- diminuer temporairement `beta` pour casser les gros clusters ;
- augmenter le bruit WalkSAT ;
- repartir de `best_sigma` avec perturbation ;
- redémarrer aléatoirement une fraction des variables non épinglées par `T` ;
- ou construire un redémarrage guidé par les arêtes.

Les redémarrages doivent conserver `best_sigma`.

Un redémarrage guidé par les arêtes peut reprendre l'idée de projection du
document spectral :

1. calculer une confiance `c_e` à partir de `d_e` et de la stabilité récente de
   `y_e` ;
2. trier les arêtes par confiance décroissante ;
3. construire une forêt couvrante en évitant de connecter trop vite à `T` ;
4. propager les spins avec la règle

```math
\sigma_j=\varepsilon_e y_e\sigma_i ;
```

5. compléter les composantes non atteintes aléatoirement ;
6. réoptimiser les auxiliaires et lancer WalkSAT.

Cette procédure reste heuristique, mais elle exploite l'information higher-order
accumulée au lieu de repartir d'une configuration complètement aléatoire.

---

## 16. Cas limites

1. **Pas de triangles transférés.**  
   L'algorithme se réduit à une dynamique Swendsen-Wang sur arêtes résiduelles,
   suivie d'une optimisation WalkSAT sur clusters.

2. **Pas d'arêtes résiduelles.**  
   Le gel est entièrement triangulaire. C'est le cas idéal pour exploiter la
   structure higher-order.

3. **Cluster de `T` trop grand.**  
   Beaucoup de variables deviennent non flippables. Il faut réduire `beta`,
   réduire `beta_T_factor`, pénaliser les triangles contenant `T` dans le LP,
   ou exclure ces triangles pendant une phase de diversification. `S_T` doit
   être suivi comme un diagnostic séparé de `S_max`.

4. **Trop de clusters.**  
   Le gel est trop faible. Augmenter `beta` ou utiliser plus d'intensification
   WalkSAT.

5. **Un seul cluster flippable géant.**  
   Le problème réduit a peu de degrés de liberté. Diminuer `beta` ou viser une
   taille maximale plus basse.

6. **Clauses réduites constantes insatisfaites.**  
   Une clause peut devenir insatisfaite pour tous les flips si toutes ses
   variables sont dans des clusters épinglés ou si les degrés de liberté
   restants ne peuvent plus la satisfaire. Elle contribue alors une constante au
   score réduit.

7. **Auxiliaire dans le cluster de `T`.**  
   Ce n'est pas un problème en soi, mais il faut toujours réoptimiser les
   auxiliaires après l'étape de flip, car ils ne sont pas des variables de sortie.

8. **Forte masse triangulaire contenant `T`.**
   Le LP a probablement transféré une partie importante du champ de référence
   dans des triangles. La dynamique risque alors de fabriquer des clusters
   épinglés plutôt que des voisinages flippables. Diminuer le coefficient
   `alpha_t` des triangles contenant `T`, ou imposer un plafond de masse
   transférée incidente à `T`.

9. **Paires orientées partagées non canonique.**
   La mutualisation conservative peut laisser trop d'auxiliaires si les clauses
   partagent une paire orientée qui n'est pas la paire canonique choisie. Utiliser
   la variante "meilleure paire partagée" décrite en section 2.4.

---

## 17. Paramètres recommandés

Valeurs de départ raisonnables :

- cible de plus grand cluster flippable : `q_star = 0.10` ;
- plafond indicatif pour le cluster de `T` : `S_T <= 0.30` à `0.50` selon la
  densité ;
- facteur de gel incident à `T` : commencer avec `beta_T_factor = 0.05` à
  `0.20`, et tester `0` pour diagnostiquer la percolation parasite ;
- pénalité de transfert pour les triangles contenant `T` : commencer avec
  `lambda_T = 0` à `0.25` ;
- nombre d'échantillons pour calibrer `beta` : `R = 3` à `7` ;
- seuil d'énumération exacte : `m <= 25` ou `m <= 30` ;
- bruit WalkSAT réduit : entre `0.05` et `0.20` ;
- budget WalkSAT réduit par sweep : proportionnel au nombre de clauses réduites
  violées, avec un minimum fixe ;
- période d'adaptation de `beta` : toutes les `10` à `50` itérations ;
- intensification MaxSAT/MILP : seulement lorsque le meilleur score stagne ;
- activer la mutualisation "meilleure paire partagée" si le nombre d'auxiliaires
  ternaires reste élevé.

Ces paramètres doivent être considérés comme des points de départ. Le bon niveau
de gel dépend fortement de la densité de la formule, du nombre d'auxiliaires, de
la masse transférée aux triangles et de la taille du cluster de `T`.

---

## 18. Résumé conceptuel

La chaîne complète est :

```text
3-SAT
  -> spins variables + T
  -> gadgets auxiliaires exacts pour les clauses ternaires
  -> graphe signé étendu
  -> compensation des arêtes opposées
  -> choix des coefficients de transfert alpha_t
  -> LP de transfert des poids vers triangles
  -> résidus d'arêtes
  -> diagnostics edge-space (q_e, d_e, masse contenant T)
  -> gel Swendsen-Wang triangles + gel Swendsen-Wang edges
  -> clusters avec cluster(T) épinglé
  -> problème MaxSAT réduit sur flips de clusters
  -> résolution par énumération / WalkSAT réduit / MaxSAT ponctuel
  -> réoptimisation des auxiliaires
  -> mise à jour de la meilleure configuration
```

La différence essentielle avec la voie spectrale est que l'on ne quitte jamais
l'espace discret des spins. Les triangles ne servent pas à construire une
relaxation continue, mais à produire des clusters respectant la frustration
locale. Le choix des flips est ensuite traité comme un problème 3-SAT réduit,
ce qui est mieux adapté à la combinatoire du problème qu'un
Metropolis-Hastings cluster par cluster.
