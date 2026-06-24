# Rapport de Performance: Solveur Spectral Higher-Order pour 3-SAT

Ce tableau présente les performances du nouveau solveur spectral **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).

L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation spectrale higher-order (warm-start) par rapport à un départ aléatoire (random-start).

| Instance | CDCL (Glucose4) | MaxSAT (RC2) | WalkSAT Pur (Target=0) | HO Spectral Seul | HO Spectral + WalkSAT (Target=0) | WalkSAT Pur (Ciblant HO Unsat) | Flips Gagnés (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **xor6**<br>(6 vars, 6 clauses) | SAT<br>0.0002s | OPT Unsat: 0<br>0.0558s | Unsat: 0<br>0.0001s<br>(0 flips) | Unsat: 0<br>0.1146s | Unsat: 0<br>**0.1146s**<br>(0 flips) | Unsat: 0<br>0.0000s<br>(0 flips) | 0.0% |
| **ph6**<br>(42 vars, 133 clauses) | UNSAT<br>0.0058s | OPT Unsat: 1<br>0.0204s | Unsat: 1<br>3.9786s<br>(300000 flips) | Unsat: 7<br>0.0318s | Unsat: 1<br>**3.5352s**<br>(300000 flips) | Unsat: 7<br>0.0004s<br>(6 flips) | 0.0% |
| **miter1**<br>(865 vars, 2488 clauses) | UNSAT<br>0.0122s | OPT Unsat: 1<br>0.0623s | Unsat: 1<br>5.0914s<br>(300000 flips) | Unsat: 243<br>3.3153s | Unsat: 1<br>**7.6472s**<br>(300000 flips) | Unsat: 242<br>0.0103s<br>(168 flips) | 0.0% |
| **add32**<br>(695 vars, 1894 clauses) | UNSAT<br>0.0111s | OPT Unsat: 1<br>0.0682s | Unsat: 1<br>2.6156s<br>(300000 flips) | Unsat: 157<br>2.2441s | Unsat: 1<br>**4.8364s**<br>(300000 flips) | Unsat: 157<br>0.0076s<br>(163 flips) | 0.0% |
| **prime169**<br>(461 vars, 1342 clauses) | SAT<br>0.0030s | OPT Unsat: 0<br>0.0079s | Unsat: 1<br>2.2821s<br>(300000 flips) | Unsat: 115<br>1.2615s | Unsat: 1<br>**3.3311s**<br>(300000 flips) | Unsat: 114<br>0.0057s<br>(120 flips) | 0.0% |
| **add64**<br>(1428 vars, 3901 clauses) | UNSAT<br>0.0321s | Skipped | Unsat: 1<br>3.0114s<br>(300000 flips) | Unsat: 370<br>5.8052s | Unsat: 1<br>**8.6201s**<br>(300000 flips) | Unsat: 370<br>0.0158s<br>(294 flips) | 0.0% |
| **add128**<br>(2282 vars, 6586 clauses) | UNSAT<br>0.0714s | Skipped | Unsat: 1<br>3.1699s<br>(300000 flips) | Unsat: 808<br>10.4637s | Unsat: 1<br>**13.5742s**<br>(300000 flips) | Unsat: 807<br>0.0215s<br>(235 flips) | 0.0% |
| **prime841**<br>(791 vars, 2320 clauses) | SAT<br>0.0040s | OPT Unsat: 0<br>0.0156s | Unsat: 2<br>2.8768s<br>(300000 flips) | Unsat: 184<br>2.7307s | Unsat: 1<br>**4.9714s**<br>(300000 flips) | Unsat: 184<br>0.0106s<br>(262 flips) | 0.0% |
| **sqrt10609**<br>(303 vars, 841 clauses) | SAT<br>0.0009s | OPT Unsat: 0<br>0.0047s | Unsat: 1<br>1.9165s<br>(300000 flips) | Unsat: 71<br>0.8249s | Unsat: 1<br>**2.9822s**<br>(300000 flips) | Unsat: 71<br>0.0029s<br>(74 flips) | 0.0% |
| **Miter_Small**<br>(91 vars, 268 clauses) | UNSAT<br>0.0005s | OPT Unsat: 1<br>0.0025s | Unsat: 1<br>3.1069s<br>(300000 flips) | Unsat: 12<br>0.1475s | Unsat: 1<br>**3.0026s**<br>(300000 flips) | Unsat: 10<br>0.0012s<br>(35 flips) | 0.0% |
| **Miter_Medium**<br>(331 vars, 1001 clauses) | SAT<br>0.0014s | OPT Unsat: 0<br>0.0060s | Unsat: 0<br>0.0365s<br>(1671 flips) | Unsat: 67<br>0.8846s | Unsat: 0<br>**0.9709s**<br>(2167 flips) | Unsat: 67<br>0.0080s<br>(89 flips) | -29.7% |
| **Miter_Large**<br>(651 vars, 2004 clauses) | UNSAT<br>0.0054s | OPT Unsat: 1<br>0.0203s | Unsat: 1<br>3.8688s<br>(300000 flips) | Unsat: 160<br>1.8411s | Unsat: 1<br>**5.5137s**<br>(300000 flips) | Unsat: 159<br>0.0086s<br>(129 flips) | 0.0% |
| **Miter_Huge**<br>(1081 vars, 3340 clauses) | UNSAT<br>0.0040s | Skipped | Unsat: 1<br>3.7431s<br>(300000 flips) | Unsat: 264<br>6.6804s | Unsat: 1<br>**9.9727s**<br>(300000 flips) | Unsat: 263<br>0.0160s<br>(250 flips) | 0.0% |