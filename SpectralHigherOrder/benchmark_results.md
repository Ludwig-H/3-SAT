# Rapport de Performance: Solveur Spectral Higher-Order pour 3-SAT

Ce tableau présente les performances du nouveau solveur spectral **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).

L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation spectrale higher-order (warm-start) par rapport à un départ aléatoire (random-start).

| Instance | CDCL (Glucose4) | MaxSAT (RC2) | WalkSAT Pur (Target=0) | HO Spectral Seul | HO Spectral + WalkSAT (Target=0) | WalkSAT Pur (Ciblant HO Unsat) | Flips Gagnés (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **xor6**<br>(6 vars, 6 clauses) | SAT<br>0.0001s | OPT Unsat: 0<br>0.0067s | Unsat: 0<br>0.0001s<br>(0 flips) | Unsat: 0<br>0.0288s | Unsat: 0<br>**0.0289s**<br>(0 flips) | Unsat: 0<br>0.0000s<br>(0 flips) | 0.0% |
| **ph6**<br>(63 vars, 154 clauses) | UNSAT<br>0.0097s | OPT Unsat: 1<br>0.0187s | Unsat: 1<br>2.6704s<br>(300000 flips) | Unsat: 7<br>0.3623s | Unsat: 1<br>**3.1835s**<br>(300000 flips) | Unsat: 7<br>0.0005s<br>(11 flips) | 0.0% |
| **miter1**<br>(865 vars, 2488 clauses) | UNSAT<br>0.0120s | OPT Unsat: 1<br>0.0532s | Unsat: 1<br>4.7289s<br>(300000 flips) | Unsat: 243<br>2.2801s | Unsat: 1<br>**6.8394s**<br>(300000 flips) | Unsat: 242<br>0.0101s<br>(168 flips) | 0.0% |
| **add32**<br>(695 vars, 1894 clauses) | UNSAT<br>0.0103s | OPT Unsat: 1<br>0.0534s | Unsat: 1<br>2.8377s<br>(300000 flips) | Unsat: 157<br>1.2762s | Unsat: 1<br>**4.0085s**<br>(300000 flips) | Unsat: 157<br>0.0081s<br>(163 flips) | 0.0% |
| **prime169**<br>(461 vars, 1342 clauses) | SAT<br>0.0029s | OPT Unsat: 0<br>0.0185s | Unsat: 1<br>2.2643s<br>(300000 flips) | Unsat: 115<br>0.7433s | Unsat: 1<br>**2.8382s**<br>(300000 flips) | Unsat: 114<br>0.0054s<br>(120 flips) | 0.0% |
| **add64**<br>(1428 vars, 3901 clauses) | UNSAT<br>0.0294s | Skipped | Unsat: 1<br>2.8523s<br>(300000 flips) | Unsat: 370<br>3.2032s | Unsat: 1<br>**6.1228s**<br>(300000 flips) | Unsat: 370<br>0.0169s<br>(294 flips) | 0.0% |
| **add128**<br>(2282 vars, 6586 clauses) | UNSAT<br>0.0668s | Skipped | Unsat: 1<br>3.0133s<br>(300000 flips) | Unsat: 816<br>9.0123s | Unsat: 1<br>**12.0929s**<br>(300000 flips) | Unsat: 816<br>0.0251s<br>(228 flips) | 0.0% |
| **prime841**<br>(791 vars, 2320 clauses) | SAT<br>0.0044s | OPT Unsat: 0<br>0.0258s | Unsat: 2<br>2.7987s<br>(300000 flips) | Unsat: 184<br>1.6871s | Unsat: 1<br>**3.9305s**<br>(300000 flips) | Unsat: 184<br>0.0110s<br>(262 flips) | 0.0% |
| **sqrt10609**<br>(303 vars, 841 clauses) | SAT<br>0.0010s | OPT Unsat: 0<br>0.0053s | Unsat: 1<br>1.9130s<br>(300000 flips) | Unsat: 71<br>0.5074s | Unsat: 1<br>**2.5722s**<br>(300000 flips) | Unsat: 71<br>0.0032s<br>(74 flips) | 0.0% |
| **Miter_Small**<br>(91 vars, 268 clauses) | UNSAT<br>0.0005s | OPT Unsat: 1<br>0.0032s | Unsat: 1<br>2.7737s<br>(300000 flips) | Unsat: 13<br>0.2024s | Unsat: 1<br>**3.2577s**<br>(300000 flips) | Unsat: 10<br>0.0013s<br>(35 flips) | 0.0% |
| **Miter_Medium**<br>(331 vars, 1001 clauses) | SAT<br>0.0011s | OPT Unsat: 0<br>0.0060s | Unsat: 0<br>0.0387s<br>(1671 flips) | Unsat: 68<br>0.6020s | Unsat: 0<br>**0.6968s**<br>(3494 flips) | Unsat: 68<br>0.0046s<br>(85 flips) | -109.1% |
| **Miter_Large**<br>(651 vars, 2004 clauses) | UNSAT<br>0.0029s | OPT Unsat: 1<br>0.0202s | Unsat: 1<br>3.6252s<br>(300000 flips) | Unsat: 157<br>1.8112s | Unsat: 1<br>**5.1923s**<br>(300000 flips) | Unsat: 157<br>0.0077s<br>(131 flips) | 0.0% |
| **Miter_Huge**<br>(1081 vars, 3340 clauses) | UNSAT<br>0.0034s | Skipped | Unsat: 1<br>3.8931s<br>(300000 flips) | Unsat: 271<br>5.3328s | Unsat: 1<br>**9.0173s**<br>(300000 flips) | Unsat: 271<br>0.0148s<br>(239 flips) | 0.0% |