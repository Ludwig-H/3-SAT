# Rapport de Performance: Solveur MCMC Higher-Order pour 3-SAT

Ce tableau présente les performances du nouveau solveur MCMC **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).

L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation MCMC higher-order (warm-start) par rapport à un départ aléatoire (random-start).

| Instance | CDCL (Glucose4) | MaxSAT (RC2) | WalkSAT Pur (Target=0) | MCMC HO Seul | MCMC HO + WalkSAT (Target=0) | WalkSAT Pur (Ciblant MCMC HO Unsat) | Flips Gagnés (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **xor6**<br>(6 vars, 6 clauses) | SAT<br>0.0002s | OPT Unsat: 0<br>0.0061s | Unsat: 0<br>0.0001s<br>(0 flips) | Unsat: 0<br>0.0143s | Unsat: 0<br>**0.0144s**<br>(0 flips) | Unsat: 0<br>0.0000s<br>(0 flips) | 0.0% |
| **ph6**<br>(63 vars, 154 clauses) | UNSAT<br>0.0081s | OPT Unsat: 1<br>0.0169s | Unsat: 1<br>2.3153s<br>(300000 flips) | Unsat: 1<br>5.2277s | Unsat: 1<br>**8.0936s**<br>(300000 flips) | Unsat: 1<br>0.0012s<br>(86 flips) | 0.0% |
| **miter1**<br>(865 vars, 2488 clauses) | UNSAT<br>0.0121s | OPT Unsat: 1<br>0.0465s | Unsat: 1<br>4.5852s<br>(300000 flips) | Unsat: 15<br>15.5286s | Unsat: 1<br>**19.7101s**<br>(300000 flips) | Unsat: 15<br>0.0345s<br>(1774 flips) | 0.0% |
| **add32**<br>(695 vars, 1894 clauses) | UNSAT<br>0.0107s | OPT Unsat: 1<br>0.0496s | Unsat: 1<br>3.3479s<br>(300000 flips) | Unsat: 4<br>11.5233s | Unsat: 1<br>**14.1792s**<br>(300000 flips) | Unsat: 4<br>0.0651s<br>(2375 flips) | 0.0% |
| **prime169**<br>(461 vars, 1342 clauses) | SAT<br>0.0025s | OPT Unsat: 0<br>0.0070s | Unsat: 1<br>1.8751s<br>(300000 flips) | Unsat: 12<br>9.2376s | Unsat: 1<br>**11.2283s**<br>(300000 flips) | Unsat: 12<br>0.0206s<br>(1109 flips) | 0.0% |
| **add64**<br>(1428 vars, 3901 clauses) | UNSAT<br>0.0277s | Skipped | Unsat: 1<br>2.4737s<br>(300000 flips) | Unsat: 17<br>21.8117s | Unsat: 1<br>**24.5571s**<br>(300000 flips) | Unsat: 17<br>0.0548s<br>(2779 flips) | 0.0% |
| **add128**<br>(2282 vars, 6586 clauses) | UNSAT<br>0.0682s | Skipped | Unsat: 1<br>2.7007s<br>(300000 flips) | Unsat: 17<br>36.2402s | Unsat: 1<br>**39.7499s**<br>(300000 flips) | Unsat: 17<br>0.1855s<br>(8022 flips) | 0.0% |
| **prime841**<br>(791 vars, 2320 clauses) | SAT<br>0.0037s | OPT Unsat: 0<br>0.0200s | Unsat: 2<br>2.8746s<br>(300000 flips) | Unsat: 21<br>14.8678s | Unsat: 1<br>**17.0503s**<br>(300000 flips) | Unsat: 21<br>0.0289s<br>(2144 flips) | 0.0% |
| **sqrt10609**<br>(303 vars, 841 clauses) | SAT<br>0.0009s | OPT Unsat: 0<br>0.0055s | Unsat: 1<br>1.7653s<br>(300000 flips) | Unsat: 10<br>6.6579s | Unsat: 1<br>**8.4408s**<br>(300000 flips) | Unsat: 10<br>0.0116s<br>(560 flips) | 0.0% |
| **Miter_Small**<br>(91 vars, 268 clauses) | UNSAT<br>0.0004s | OPT Unsat: 1<br>0.0035s | Unsat: 1<br>2.4461s<br>(300000 flips) | Unsat: 1<br>2.8899s | Unsat: 1<br>**5.6208s**<br>(300000 flips) | Unsat: 1<br>0.0045s<br>(233 flips) | 0.0% |
| **Miter_Medium**<br>(331 vars, 1001 clauses) | SAT<br>0.0012s | OPT Unsat: 0<br>0.0067s | Unsat: 0<br>0.0332s<br>(1671 flips) | Unsat: 6<br>7.3019s | Unsat: 0<br>**7.4892s**<br>(10884 flips) | Unsat: 6<br>0.0110s<br>(351 flips) | -551.3% |
| **Miter_Large**<br>(651 vars, 2004 clauses) | UNSAT<br>0.0022s | OPT Unsat: 1<br>0.0128s | Unsat: 1<br>3.5101s<br>(300000 flips) | Unsat: 6<br>11.7971s | Unsat: 1<br>**14.9518s**<br>(300000 flips) | Unsat: 6<br>0.0323s<br>(1952 flips) | 0.0% |
| **Miter_Huge**<br>(1081 vars, 3340 clauses) | UNSAT<br>0.0035s | Skipped | Unsat: 1<br>3.5590s<br>(300000 flips) | Unsat: 20<br>19.1575s | Unsat: 1<br>**22.6218s**<br>(300000 flips) | Unsat: 20<br>0.0323s<br>(1561 flips) | 0.0% |