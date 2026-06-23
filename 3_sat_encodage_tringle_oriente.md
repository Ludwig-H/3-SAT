# Encodage d'un Triangle Orienté 3-SAT par Arêtes, Triangles et Noeuds Auxiliaires

Ce document étudie l'encodage d'une plaquette orientée de type

$$
H_a(x,y,z)=u_a\left(1-\mathbf{1}_{x=y=z=+}\right),
$$

ou, en jauge générale,

$$
H_a(\sigma_i,\sigma_j,\sigma_k)
=u_a\left(1-\mathbf{1}_{\tau_i\sigma_i T=+,\ \tau_j\sigma_j T=+,\ \tau_k\sigma_k T=+}\right).
$$

L'objectif n'est pas seulement de représenter formellement cette énergie, mais de le faire dans un langage compatible avec la dynamique de clusters déjà utilisée : arêtes signées, éventuel noeud de référence $T$, regroupement de poids d'arêtes, puis transfert partiel vers des triangles isotropes.

Le point important est le suivant :

* sans variable auxiliaire, une plaquette orientée vraie à un seul état contient nécessairement un terme cubique ;
* avec une variable auxiliaire, on obtient un encodage exact pour la minimisation ;
* si plusieurs plaquettes portent sur le même triplet de variables, il faut d'abord les agréger : un seul auxiliaire suffit pour le coefficient cubique résiduel du triplet ;
* cet encodage permet ensuite de sommer et de compenser les arêtes signées, mais il doit être utilisé avec prudence dans la dynamique pour ne pas créer un gel artificiel des variables auxiliaires.

---

## 1. Conventions

Les spins prennent leurs valeurs dans

$$
\sigma_i \in \{-1,+1\}.
$$

Le noeud $T$ est un spin de référence fixé, que l'on peut prendre égal à $+1$ après jauge :

$$
T=+1.
$$

Une arête signée entre deux spins $p,q$ de signe $\varepsilon_{pq}\in\{-1,+1\}$ et de poids $w_{pq}\geq 0$ est satisfaite lorsque

$$
\sigma_p\sigma_q=\varepsilon_{pq}.
$$

Son énergie est

$$
E_{pq}^{\varepsilon}(w)
=w\,\mathbf{1}_{\sigma_p\sigma_q\neq \varepsilon}
=\frac{w}{2}\left(1-\varepsilon\sigma_p\sigma_q\right).
$$

Ainsi, deux arêtes opposées sur la même paire se compensent algébriquement. En effet,

$$
w_+\mathbf{1}_{\sigma_p\sigma_q\neq +1}
+w_-\mathbf{1}_{\sigma_p\sigma_q\neq -1}
=\mathrm{const}
-\frac{1}{2}(w_+-w_-)\sigma_p\sigma_q.
$$

Donc, à constante près, elles se remplacent par une seule arête signée de poids

$$
|w_+-w_-|
$$

et de signe

$$
\operatorname{sign}(w_+-w_-).
$$

Pour une plaquette orientée $a=\{i,j,k\}$, on note les spins orientés

$$
r_i=\tau_i\sigma_i T,\qquad
r_j=\tau_j\sigma_j T,\qquad
r_k=\tau_k\sigma_k T,
$$

où $\tau_i,\tau_j,\tau_k\in\{-1,+1\}$ sont les signes du motif satisfaisant. La plaquette est satisfaite si et seulement si

$$
r_i=r_j=r_k=+1.
$$

Dans la jauge pure $+++$, on a simplement

$$
r_i=x,\qquad r_j=y,\qquad r_k=z.
$$

---

## 2. Obstruction sans variable auxiliaire

La plaquette orientée élémentaire est

$$
H(x,y,z)=u\left(1-\mathbf{1}_{x=y=z=+}\right).
$$

Comme

$$
\mathbf{1}_{x=y=z=+}
=\frac{1}{8}(1+x)(1+y)(1+z),
$$

on obtient

$$
H(x,y,z)
=\frac{u}{8}\left(7-x-y-z-xy-xz-yz-xyz\right).
$$

Le terme cubique

$$
-\frac{u}{8}xyz
$$

est donc indispensable.

Or, après fixation de $T=+1$, toute somme d'arêtes signées entre les sommets

$$
\{x,y,z,T\}
$$

engendre seulement des termes de degré au plus $2$ :

$$
1,\ x,\ y,\ z,\ xy,\ xz,\ yz.
$$

De même, une face latérale de type $(x,y,T)$ ne dépend, une fois $T$ fixé, que de $x$ et $y$. Elle ne peut donc pas engendrer le monôme $xyz$.

Conclusion : une plaquette orientée vraie dans un unique état ne peut pas être encodée exactement par des arêtes et des triangles latéraux sur les seuls noeuds $\{x,y,z,T\}$.

Il faut soit accepter une vraie interaction cubique, soit introduire une variable auxiliaire.

---

## 3. Gadget exact de minimisation avec un auxiliaire

Pour la minimisation, un seul noeud auxiliaire suffit pour une plaquette isolée.

Si plusieurs plaquettes portent sur le même triplet de variables, la construction locale "un auxiliaire par plaquette" reste correcte, mais elle n'est pas optimale. Dans ce cas, on doit d'abord agréger les plaquettes du triplet et n'introduire qu'un auxiliaire pour le terme cubique résiduel. Cette règle est détaillée en section 6.1.

On introduit un spin auxiliaire

$$
s_a\in\{-1,+1\}
$$

et le booléen

$$
q_a=\frac{1+s_aT}{2}.
$$

Pour chaque spin orienté $r_\ell$, on introduit aussi

$$
b_\ell=\frac{1+r_\ell}{2}.
$$

Le booléen $b_\ell$ vaut $1$ lorsque le littéral orienté est vrai.

Pour un paramètre

$$
M_a\geq u_a,
$$

on définit le gadget de Rosenberg

$$
G_a(b_i,b_j,b_k,q_a)
=u_a+q_a\left(3M_a-u_a-M_a(b_i+b_j+b_k)\right).
$$

Alors

$$
\min_{q_a\in\{0,1\}}G_a
=u_a\left(1-b_ib_jb_k\right).
$$

En revenant aux spins, cela donne exactement

$$
\min_{s_a\in\{-1,+1\}}G_a
=u_a\left(1-\mathbf{1}_{r_i=r_j=r_k=+1}\right).
$$

Il s'agit donc d'un encodage exact de la plaquette orientée pour l'optimisation zéro-température.

### 3.1. Vérification par table

Soit

$$
n=b_i+b_j+b_k.
$$

Alors

$$
G_a(q_a=0)=u_a,
$$

et

$$
G_a(q_a=1)=M_a(3-n).
$$

On obtient donc :

| Nombre de littéraux vrais $n$ | $G(q=0)$ | $G(q=1)$ | Minimum si $M_a\geq u_a$ | Plaquette |
| :---: | :---: | :---: | :---: | :---: |
| $3$ | $u_a$ | $0$ | $0$ | satisfaite |
| $2$ | $u_a$ | $M_a$ | $u_a$ | insatisfaite |
| $1$ | $u_a$ | $2M_a$ | $u_a$ | insatisfaite |
| $0$ | $u_a$ | $3M_a$ | $u_a$ | insatisfaite |

Donc le gadget possède exactement deux niveaux d'énergie après minimisation sur l'auxiliaire :

$$
0
$$

pour l'état orienté satisfait, et

$$
u_a
$$

pour les sept autres états.

Le choix minimal est

$$
M_a=u_a.
$$

Il minimise la rigidité artificielle introduite par l'auxiliaire. Le choix $M_a>u_a$ brise certaines dégénérescences de l'auxiliaire, mais augmente aussi les poids des arêtes et peut favoriser un gel parasite.

---

## 4. Forme en arêtes signées

Développons le gadget précédent en spins. À constante près,

$$
G_a
=-\frac{M_a}{4}(r_i+r_j+r_k)
-\frac{M_a}{4}s_aT(r_i+r_j+r_k)
+\left(\frac{3M_a}{4}-\frac{u_a}{2}\right)s_aT.
$$

Comme

$$
r_\ell=\tau_\ell\sigma_\ell T
$$

et

$$
s_aT\,r_\ell=\tau_\ell s_a\sigma_\ell,
$$

le gadget se représente par les arêtes suivantes :

1. Pour chaque variable $\ell\in\{i,j,k\}$, une arête variable-référence

$$
(\ell,T)
$$

de signe

$$
\tau_\ell
$$

et de poids

$$
\frac{M_a}{2}.
$$

2. Pour chaque variable $\ell\in\{i,j,k\}$, une arête auxiliaire-variable

$$
(s_a,\ell)
$$

de signe

$$
\tau_\ell
$$

et de poids

$$
\frac{M_a}{2}.
$$

3. Une arête auxiliaire-référence

$$
(s_a,T)
$$

de signe

$$
-1
$$

et de poids

$$
\frac{3M_a}{2}-u_a.
$$

Le poids de cette dernière arête est bien positif dès que

$$
M_a\geq \frac{2u_a}{3}.
$$

La condition de validité du gadget étant $M_a\geq u_a$, cette positivité est automatiquement vérifiée.

Pour le choix minimal $M_a=u_a$, les sept arêtes ont toutes le poids

$$
\frac{u_a}{2}.
$$

Dans la jauge $+++$, le gadget minimal devient :

$$
E_a=\frac{u_a}{2}
\left[
\mathbf{1}_{x\neq T}
+\mathbf{1}_{y\neq T}
+\mathbf{1}_{z\neq T}
+\mathbf{1}_{s_a\neq x}
+\mathbf{1}_{s_a\neq y}
+\mathbf{1}_{s_a\neq z}
+\mathbf{1}_{s_a=T}
\right].
$$

Plus précisément, cette somme d'arêtes vérifie

$$
\min_{s_a}E_a
=\frac{u_a}{2}
+u_a\left(1-\mathbf{1}_{x=y=z=+}\right).
$$

Le terme $u_a/2$ est une constante additive. Il ne change donc pas le problème de minimisation.

---

## 5. Lecture géométrique du gadget minimal

Dans le cas $M_a=u_a$, une plaquette orientée ajoute :

* trois arêtes qui attirent les variables vers leur signe satisfaisant par rapport à $T$ ;
* trois arêtes qui attirent l'auxiliaire $s_a$ vers les variables orientées ;
* une arête antiferromagnétique entre $s_a$ et $T$.

Pour le motif $+++$, avec $T=+$ :

$$
x--T,\quad y--T,\quad z--T
$$

sont ferromagnétiques,

$$
s_a--x,\quad s_a--y,\quad s_a--z
$$

sont ferromagnétiques, et

$$
s_a--T
$$

est antiferromagnétique.

Chaque triplet

$$
(s_a,\ell,T)
$$

forme donc un triangle frustré : les deux arêtes impliquant $\ell$ ont le même signe orienté $\tau_\ell$, tandis que l'arête $(s_a,T)$ est antiferromagnétique.

Cette observation est utile pour la dynamique existante : après sommation des arêtes, le transfert arêtes-vers-triangles peut découvrir des triangles frustrés impliquant des auxiliaires et le noeud $T$. Cependant, il ne faut pas interpréter localement chaque gadget comme la somme de trois triangles indépendants, car l'arête $(s_a,T)$ est commune aux trois triplets.

Avec $M_a=u_a$, chaque triplet voudrait utiliser une arête $(s_a,T)$ de poids $u_a/2$, mais le gadget ne contient qu'une seule arête $(s_a,T)$ de poids total $u_a/2$. Le regroupement en triangles doit donc être fait globalement par le LP de transfert, pas clause par clause de manière naïve.

---

## 6. Somme et compensation des arêtes

L'intérêt principal du gadget est qu'après quadratisation, toutes les contributions deviennent des arêtes signées.

Pour chaque plaquette $a=(i,j,k)$, on ajoute les contributions :

$$
(i,T):\quad \tau_i\frac{M_a}{2},
$$

$$
(j,T):\quad \tau_j\frac{M_a}{2},
$$

$$
(k,T):\quad \tau_k\frac{M_a}{2},
$$

$$
(s_a,i):\quad \tau_i\frac{M_a}{2},
$$

$$
(s_a,j):\quad \tau_j\frac{M_a}{2},
$$

$$
(s_a,k):\quad \tau_k\frac{M_a}{2},
$$

et

$$
(s_a,T):\quad -\left(\frac{3M_a}{2}-u_a\right).
$$

Ici l'écriture

$$
(p,q):\quad \varepsilon w
$$

signifie : arête de signe $\varepsilon$ et de poids $w$.

Après addition sur toutes les plaquettes, chaque paire $(p,q)$ possède un poids signé total

$$
K_{pq}=\sum_{a\rightarrow(p,q)}\varepsilon_{pq}^{(a)}w_{pq}^{(a)}.
$$

Elle se remplace par une seule arête effective :

$$
|K_{pq}|
$$

de signe

$$
\operatorname{sign}(K_{pq}).
$$

Les annulations sont donc automatiquement prises en compte.

### 6.1. Agrégation optimale des plaquettes sur un même triplet

La règle "un auxiliaire par plaquette" est locale. Elle est toujours valide, mais elle peut être inutilement coûteuse.

Supposons que plusieurs plaquettes orientées portent exactement sur le même triplet de variables

$$
\{i,j,k\}.
$$

On les indexe par $a\in A_{ijk}$, avec poids $u_a$ et motif satisfaisant

$$
\tau^a=(\tau_i^a,\tau_j^a,\tau_k^a)\in\{-1,+1\}^3.
$$

Le Hamiltonien agrégé du triplet est

$$
H_{ijk}(\sigma_i,\sigma_j,\sigma_k)
=\sum_{a\in A_{ijk}}
u_a\left(1-\mathbf{1}_{\sigma_i=\tau_i^aT,\ \sigma_j=\tau_j^aT,\ \sigma_k=\tau_k^aT}\right).
$$

En fixant $T=+1$ pour alléger les notations, on utilise l'identité

$$
\mathbf{1}_{\sigma_i=\tau_i,\ \sigma_j=\tau_j,\ \sigma_k=\tau_k}
=\frac{1}{8}
(1+\tau_i\sigma_i)(1+\tau_j\sigma_j)(1+\tau_k\sigma_k).
$$

Le Hamiltonien agrégé s'écrit donc sous la forme de Walsh-Fourier

$$
H_{ijk}
=C
+h_i\sigma_i+h_j\sigma_j+h_k\sigma_k
+J_{ij}\sigma_i\sigma_j
+J_{ik}\sigma_i\sigma_k
+J_{jk}\sigma_j\sigma_k
+K_{ijk}\sigma_i\sigma_j\sigma_k.
$$

Le seul terme qui ne peut pas être représenté par des arêtes est

$$
K_{ijk}\sigma_i\sigma_j\sigma_k,
$$

avec

$$
K_{ijk}
=-\frac{1}{8}
\sum_{a\in A_{ijk}}
u_a\,\tau_i^a\tau_j^a\tau_k^a.
$$

On définit donc la masse cubique résiduelle

$$
\lambda_{ijk}
=8|K_{ijk}|
=\left|
\sum_{a\in A_{ijk}}
u_a\,\tau_i^a\tau_j^a\tau_k^a
\right|.
$$

Si

$$
\lambda_{ijk}=0,
$$

aucun auxiliaire n'est nécessaire : toutes les plaquettes sur ce triplet se réduisent exactement à une constante, des champs vers $T$, et des arêtes internes.

Si

$$
\lambda_{ijk}>0,
$$

un seul auxiliaire suffit pour tout le triplet. On choisit un motif $\pi=(\pi_i,\pi_j,\pi_k)$ tel que

$$
\pi_i\pi_j\pi_k
=\operatorname{sign}\left(
\sum_{a\in A_{ijk}}
u_a\,\tau_i^a\tau_j^a\tau_k^a
\right).
$$

Alors la plaquette orientée effective

$$
\lambda_{ijk}
\left(
1-\mathbf{1}_{\sigma_i=\pi_iT,\ \sigma_j=\pi_jT,\ \sigma_k=\pi_kT}
\right)
$$

possède exactement le même coefficient cubique que $H_{ijk}$. La différence

$$
H_{ijk}
-
\lambda_{ijk}
\left(
1-\mathbf{1}_{\sigma_i=\pi_iT,\ \sigma_j=\pi_jT,\ \sigma_k=\pi_kT}
\right)
$$

est donc de degré au plus $2$. Elle s'encode entièrement par champs et arêtes signées.

Ainsi, le nombre optimal d'auxiliaires n'est pas le nombre de plaquettes, mais le nombre de triplets dont le coefficient cubique agrégé est non nul.

En pratique :

* même orientation : on fusionne les poids et on garde un seul auxiliaire ;
* parités cubiques opposées avec poids égaux : les cubiques s'annulent et aucun auxiliaire n'est nécessaire ;
* parités cubiques opposées avec poids inégaux : seul le poids résiduel nécessite un auxiliaire ;
* parités cubiques identiques : les masses cubiques s'additionnent, mais un seul auxiliaire suffit encore pour le triplet.

Le choix du motif $\pi$ n'est pas unique dès que seul son produit $\pi_i\pi_j\pi_k$ est imposé. Les différents choix donnent le même coefficient cubique et déplacent seulement les termes de degré $1$ et $2$ entre la plaquette effective et le résidu quadratique. On peut donc choisir $\pi$ pour minimiser les poids résiduels d'arêtes, ou simplement l'aligner avec l'orientation dominante du triplet.

### 6.2. Exemple : deux plaquettes partageant le même triplet

Considérons deux plaquettes sur les mêmes variables :

$$
u\left(1-\mathbf{1}_{\sigma=\tau}\right)
+v\left(1-\mathbf{1}_{\sigma=\rho}\right).
$$

Le coefficient cubique est proportionnel à

$$
u\,\tau_i\tau_j\tau_k
+v\,\rho_i\rho_j\rho_k.
$$

Si les deux parités sont opposées et $u=v$, alors ce coefficient est nul. Il ne faut créer aucun auxiliaire.

Par exemple,

$$
(+,+,+) \quad \text{et} \quad (-,+,+)
$$

avec le même poids $u$ donnent

$$
u(1-\mathbf{1}_{x=+,y=+,z=+})
+u(1-\mathbf{1}_{x=-,y=+,z=+})
=2u-u\,\mathbf{1}_{y=+,z=+}.
$$

À constante près, c'est une contrainte orientée binaire sur $(y,z)$, donc une énergie de degré $2$.

De même,

$$
(+,+,+) \quad \text{et} \quad (-,-,-)
$$

avec le même poids donnent

$$
2u-u\,\mathbf{1}_{x=y=z}
$$

et donc, à constante près, un triangle isotrope ferromagnétique.

Si les deux parités sont identiques, il reste un terme cubique. Mais il n'en reste qu'un seul. Par exemple,

$$
(+,+,+) \quad \text{et} \quad (-,-,+)
$$

ont la même parité cubique. Avec poids égaux $u$, la masse cubique vaut $2u$, et un seul auxiliaire suffit pour représenter une plaquette effective de poids $2u$, plus un résidu quadratique.

### 6.3. Clauses partageant une même paire orientée

L'idée la plus simple est de garder un auxiliaire par clause, puis d'imposer une égalité dure entre les auxiliaires de clauses qui partagent la même paire orientée.

Soient des clauses

$$
H_R=\sum_{r\in R}u_r(1-a b c_r),
$$

où $a$ et $b$ sont deux littéraux orientés communs, et $c_r$ est le troisième littéral orienté de la clause $r$.

Pour chaque clause, on prend le gadget minimal

$$
G_r(a,b,c_r,q_r)
=u_r\left[1+q_r(2-a-b-c_r)\right],
$$

qui correspond au choix $M_r=u_r$.

On ajoute ensuite des contraintes dures attractives

$$
q_r=q_{r'}\qquad (r,r'\in R).
$$

Ces contraintes sont équivalentes à un unique auxiliaire commun $q$. Alors

$$
\min_{q\in\{0,1\}}\sum_{r\in R}G_r(a,b,c_r,q)
=\sum_{r\in R}u_r(1-abc_r).
$$

Preuve :

* si $a=b=1$, alors $\sum_rG_r=\sum_ru_r(1-qc_r)$, donc le minimum est obtenu avec $q=1$ et vaut $\sum_ru_r(1-c_r)$ ;
* si $ab=0$, alors $q=0$ donne $\sum_ru_r$, et $q=1$ ne peut pas faire mieux.

Donc la contraction dure des auxiliaires est exacte pour la minimisation.

### 6.4. Condition de validité

La contraction précédente est exacte seulement pour une même paire orientée.

Ainsi,

$$
(x=+,y=+,z=+)
\quad\text{et}\quad
(x=+,y=+,w=+)
$$

peuvent partager le même auxiliaire, car elles utilisent toutes deux le certificat

$$
q_{xy}^{++}=\mathbf{1}_{x=+,y=+}.
$$

En revanche,

$$
(x=+,y=+,z=+)
\quad\text{et}\quad
(x=-,y=-,w=+)
$$

ne doivent pas être contractées ensemble. Elles demandent deux certificats différents :

$$
q_{xy}^{++}=\mathbf{1}_{x=+,y=+},
\qquad
q_{xy}^{--}=\mathbf{1}_{x=-,y=-}.
$$

Un seul spin auxiliaire ne peut pas représenter simultanément les trois cas

$$
xy=++,\qquad xy=--,\qquad xy\in\{+-,-+\}.
$$

Si deux clauses ne partagent qu'une seule variable, il n'y a pas de paire orientée commune à certifier. On peut seulement compenser les champs directs sur cette variable, ou choisir une autre paire qui se répète ailleurs.

La bonne règle est donc :

$$
\boxed{
\text{contracter les auxiliaires uniquement par classe de même paire orientée.}
}
$$

---

## 7. Relation avec le regroupement en triangles

Une fois les arêtes agrégées, on peut appliquer le même principe que dans la dynamique optimisée :

1. sommer toutes les arêtes signées ;
2. compenser les poids opposés ;
3. résoudre un LP de transfert d'énergie des arêtes vers des triangles isotropes ;
4. conserver les arêtes résiduelles.

La différence est que le graphe contient maintenant des noeuds auxiliaires. Ils peuvent être des auxiliaires de plaquette $s_a$, ou des auxiliaires de paire orientée $q_{ij}^{\tau_i,\tau_j}$.

Les triangles possibles peuvent être de plusieurs types :

$$
(s_a,\ell,T),
$$

$$
(s_a,\ell,m),
$$

$$
(\ell,m,n),
$$

ou encore des triangles entre auxiliaires si d'autres mécanismes créent des arêtes auxiliaire-auxiliaire.

Dans le gadget élémentaire pur, les triangles naturels sont surtout

$$
(s_a,\ell,T).
$$

Ils sont frustrés, car le produit des signes autour du cycle vaut

$$
\tau_\ell\cdot \tau_\ell\cdot (-1)=-1.
$$

Ils sont donc compatibles avec la règle de gel des triangles frustrés utilisée dans la dynamique de type Swendsen-Wang triangulaire.

Cependant, le transfert vers triangles doit rester global. En particulier, on ne doit pas décider localement que chaque plaquette orientée devient trois triangles frustrés indépendants : cela surcompterait l'arête commune $(s_a,T)$.

Pour les auxiliaires de paire orientée, le même principe s'applique : on ne force pas une décomposition locale en triangles. On convertit d'abord toutes les contributions quadratiques en arêtes signées, on les additionne, puis le LP décide quels poids peuvent être transférés vers des triangles.

---

## 8. Dynamique recommandée pour la minimisation

Le Hamiltonien étendu est, de manière générique,

$$
E_{\mathrm{ext}}(\sigma,\xi)
=\sum_g G_g(\sigma_{\partial g},\xi_g),
$$

où $g$ peut être une plaquette isolée, un triplet agrégé, ou une paire orientée mutualisée. La variable $\xi_g$ désigne l'auxiliaire associé au gadget choisi.

Par construction,

$$
\overline{E}(\sigma)
=\min_\xi E_{\mathrm{ext}}(\sigma,\xi)
=U_{\mathrm{SAT}}(\sigma)+\mathrm{const}.
$$

Pour minimiser l'énergie SAT originale, il est donc naturel de travailler avec l'énergie projetée

$$
\overline{E}(\sigma).
$$

La règle algorithmique recommandée est :

1. Partir d'une configuration des variables originales $\sigma$.
2. Mettre chaque auxiliaire $\xi_g$ à un minimiseur local :

$$
\xi_g\in\operatorname*{argmin}_{\xi}G_g(\sigma_{\partial g},\xi).
$$

3. Construire les arêtes agrégées sur le graphe étendu.
4. Former des clusters avec les arêtes résiduelles et les triangles transférés.
5. Proposer des mouvements de clusters.
6. Après chaque mouvement proposé sur les variables originales, réoptimiser les auxiliaires affectés.
7. Accepter le mouvement selon l'énergie projetée $\overline{E}$, ou selon une règle de descente/recuit si l'objectif est l'optimisation pure.

Le point crucial est que les auxiliaires ne doivent pas être considérés comme des variables physiques équivalentes aux variables SAT originales.

Si les auxiliaires sont gelés trop fortement, ils peuvent devenir des hubs artificiels. Dans ce cas, une clause ou une paire déjà satisfaite crée de nombreuses arêtes satisfaites autour de son auxiliaire, ce qui peut figer des régions entières du graphe étendu sans correspondre à une structure réelle du Hamiltonien original.

---

## 9. Choix du paramètre $M$

Pour un gadget de plaquette isolée, le paramètre $M_a$ doit satisfaire

$$
M_a\geq u_a.
$$

Le choix minimal

$$
M_a=u_a
$$

donne les poids d'arêtes les plus faibles :

$$
\frac{u_a}{2}
$$

sur les sept arêtes du gadget.

C'est le choix le plus naturel pour limiter la rigidité artificielle.

Il introduit cependant une dégénérescence lorsque deux littéraux orientés sont vrais et un est faux. Dans ce cas, les deux valeurs de l'auxiliaire peuvent donner le même minimum.

Un choix

$$
M_a>u_a
$$

brise cette dégénérescence : dès que la plaquette n'est pas totalement satisfaite, l'auxiliaire préfère rester dans l'état $q_a=0$, c'est-à-dire

$$
s_aT=-1.
$$

Mais ce choix augmente aussi les poids

$$
\frac{M_a}{2}
$$

et

$$
\frac{3M_a}{2}-u_a,
$$

ce qui peut renforcer le gel parasite. Pour une dynamique de clusters, le choix minimal $M_a=u_a$ est donc généralement le plus prudent.

Pour un gadget de paire orientée partagé par un groupe $R$, le paramètre doit satisfaire

$$
M_R\geq U_R:=\sum_{r\in R}u_r.
$$

Le choix minimal

$$
M_R=U_R
$$

est encore le moins rigide. Mais si $R$ est grand, ce choix peut produire des arêtes fortes autour de l'auxiliaire de paire. Il peut alors être préférable, algorithmiquement, de scinder un très gros groupe en plusieurs groupes plus petits, même si cela augmente le nombre d'auxiliaires.

---

## 10. Différence entre optimisation et sampling exact

Le gadget ci-dessus est exact au sens

$$
\min_\xi E_{\mathrm{ext}}(\sigma,\xi)
=U_{\mathrm{SAT}}(\sigma)+\mathrm{const}.
$$

Il n'est pas exact au sens Gibbsien :

$$
-\log\sum_\xi e^{-E_{\mathrm{ext}}(\sigma,\xi)}
\neq
U_{\mathrm{SAT}}(\sigma)+\mathrm{const}
$$

en général.

Ainsi, ce gadget est adapté à un algorithme de minimisation, de descente, de recuit, ou de recherche de bonne solution SAT. Il ne doit pas être présenté comme une dynamique de Gibbs exacte pour le Hamiltonien original à température finie.

Pour un sampling exact, il faudrait utiliser un autre gadget dont la marginalisation sur les auxiliaires reproduit exactement le poids de Gibbs. Ce gadget existe, mais ses couplages dépendent d'une équation de type log-cosh et ne donne pas le même objet simple de minimisation.

---

## 11. Résumé opérationnel

La stratégie recommandée est hiérarchique.

1. Pour chaque triplet exact $\{i,j,k\}$, agréger toutes les plaquettes qui portent sur ce triplet et calculer le coefficient cubique résiduel

$$
\lambda_{ijk}
=\left|
\sum_{a\in A_{ijk}}
u_a\,\tau_i^a\tau_j^a\tau_k^a
\right|.
$$

Si $\lambda_{ijk}=0$, aucun auxiliaire n'est nécessaire pour ce triplet.

2. Pour les plaquettes restantes, chercher les groupes qui partagent une même paire orientée. On peut alors soit introduire directement un auxiliaire de paire

$$
q_{ij}^{\tau_i,\tau_j}=ab
$$

avec

$$
M_R\geq \sum_{r\in R}u_r.
$$

soit garder un auxiliaire minimal $q_r$ par clause et imposer des liens attractifs infinis

$$
q_r=q_{r'}.
$$

Les deux formulations encodent exactement, après minimisation sur les auxiliaires, toutes les plaquettes du groupe.

3. Pour les plaquettes isolées ou les groupes où la mutualisation par paire n'est pas avantageuse, utiliser le gadget local à un auxiliaire $s_a$ avec le choix minimal $M_a=u_a$. Il ajoute :

* trois arêtes $(\ell,T)$ de signe $\tau_\ell$ et de poids $u_a/2$ ;
* trois arêtes $(s_a,\ell)$ de signe $\tau_\ell$ et de poids $u_a/2$ ;
* une arête $(s_a,T)$ de signe $-1$ et de poids $u_a/2$.

Après minimisation sur les auxiliaires, on obtient exactement

$$
\min_\xi E_{\mathrm{ext}}(\sigma,\xi)
=\mathrm{const}
+U_{\mathrm{SAT}}(\sigma).
$$

Toutes les arêtes ainsi produites peuvent ensuite être additionnées, compensées et transférées vers des triangles par le mécanisme habituel.

L'algorithme doit toutefois traiter les auxiliaires comme des variables de certification à réoptimiser, et non comme des variables SAT ordinaires que l'on laisserait se figer librement.
