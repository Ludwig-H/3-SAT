# Rapport de Performance: Solveur MCMC Higher-Order pour 3-SAT

Ce tableau présente les performances du nouveau solveur MCMC **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).

L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation MCMC higher-order (warm-start) par rapport à un départ aléatoire (random-start).

| Instance | CDCL (Glucose4) | MaxSAT (RC2) | WalkSAT Pur (Ciblant Opt) | MCMC HO Seul | MCMC HO + WalkSAT (Ciblant Opt) | WalkSAT Pur (Ciblant MCMC HO Unsat) | Flips Gagnés (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **xor6**<br>(6 vars, 6 clauses) | SAT<br>0.0002s | OPT Unsat: 0<br>0.0069s | Unsat: 0 (Cible: 0)<br>0.0001s<br>(0 flips) | Unsat: 0<br>0.1367s | Unsat: 0 (Cible: 0)<br>**0.1368s**<br>(0 flips) | Unsat: 0<br>0.0000s<br>(0 flips) | 0.0% |
| **ph6**<br>(63 vars, 154 clauses) | UNSAT<br>0.0081s | OPT Unsat: 1<br>0.0322s | Unsat: 1 (Cible: 1)<br>0.0034s<br>(86 flips) | Unsat: 1<br>27.4914s | Unsat: 1 (Cible: 1)<br>**27.4917s**<br>(0 flips) | Unsat: 1<br>0.0012s<br>(86 flips) | 100.0% |
| **miter1**<br>(865 vars, 2488 clauses) | UNSAT<br>0.0116s | OPT Unsat: 1<br>0.0461s | Unsat: 1 (Cible: 1)<br>0.1535s<br>(8001 flips) | Unsat: 11<br>8.1064s | Unsat: 1 (Cible: 1)<br>**8.2440s**<br>(4193 flips) | Unsat: 11<br>0.0619s<br>(1940 flips) | 47.6% |
| **add32**<br>(695 vars, 1894 clauses) | UNSAT<br>0.0115s | OPT Unsat: 1<br>0.0419s | Unsat: 1 (Cible: 1)<br>0.1688s<br>(13601 flips) | Unsat: 8<br>11.4835s | Unsat: 1 (Cible: 1)<br>**11.5316s**<br>(4670 flips) | Unsat: 8<br>0.0176s<br>(861 flips) | 65.7% |
| **prime169**<br>(461 vars, 1342 clauses) | SAT<br>0.0025s | OPT Unsat: 0<br>0.0076s | Unsat: 1 (Cible: 0)<br>1.9407s<br>(300000 flips) | Unsat: 15<br>8.1018s | Unsat: 1 (Cible: 0)<br>**9.9652s**<br>(300000 flips) | Unsat: 15<br>0.0129s<br>(558 flips) | 0.0% |
| **add64**<br>(1428 vars, 3901 clauses) | UNSAT<br>0.0333s | Skipped | Unsat: 1 (Cible: 1)<br>0.1273s<br>(12926 flips) | Unsat: 18<br>14.3549s | Unsat: 1 (Cible: 1)<br>**14.5192s**<br>(11916 flips) | Unsat: 18<br>0.0525s<br>(2667 flips) | 7.8% |
| **add128**<br>(2282 vars, 6586 clauses) | UNSAT<br>0.0634s | Skipped | Unsat: 1 (Cible: 1)<br>0.3531s<br>(32374 flips) | Unsat: 16<br>23.5404s | Unsat: 1 (Cible: 1)<br>**23.7719s**<br>(24918 flips) | Unsat: 16<br>0.1929s<br>(8026 flips) | 23.0% |
| **prime841**<br>(791 vars, 2320 clauses) | SAT<br>0.0053s | OPT Unsat: 0<br>0.0225s | Unsat: 2 (Cible: 0)<br>2.3756s<br>(300000 flips) | Unsat: 17<br>9.8140s | Unsat: 1 (Cible: 0)<br>**11.8435s**<br>(300000 flips) | Unsat: 17<br>0.0391s<br>(3082 flips) | 0.0% |
| **sqrt10609**<br>(303 vars, 841 clauses) | SAT<br>0.0012s | OPT Unsat: 0<br>0.0060s | Unsat: 1 (Cible: 0)<br>1.8458s<br>(300000 flips) | Unsat: 10<br>7.5441s | Unsat: 1 (Cible: 0)<br>**9.2513s**<br>(300000 flips) | Unsat: 10<br>0.0114s<br>(560 flips) | 0.0% |
| **Miter_Small**<br>(91 vars, 268 clauses) | UNSAT<br>0.0006s | OPT Unsat: 1<br>0.0029s | Unsat: 1 (Cible: 1)<br>0.0040s<br>(233 flips) | Unsat: 2<br>22.4983s | Unsat: 1 (Cible: 1)<br>**22.5005s**<br>(95 flips) | Unsat: 2<br>0.0048s<br>(232 flips) | 59.2% |
| **Miter_Medium**<br>(331 vars, 1001 clauses) | SAT<br>0.0016s | OPT Unsat: 0<br>0.0060s | Unsat: 0 (Cible: 0)<br>0.0573s<br>(1671 flips) | Unsat: 4<br>6.4254s | Unsat: 0 (Cible: 0)<br>**6.4481s**<br>(1053 flips) | Unsat: 4<br>0.0206s<br>(842 flips) | 37.0% |
| **Miter_Large**<br>(651 vars, 2004 clauses) | UNSAT<br>0.0022s | OPT Unsat: 1<br>0.0112s | Unsat: 1 (Cible: 1)<br>0.1946s<br>(10727 flips) | Unsat: 11<br>9.0313s | Unsat: 1 (Cible: 1)<br>**9.2416s**<br>(13013 flips) | Unsat: 11<br>0.0273s<br>(1019 flips) | -21.3% |
| **Miter_Huge**<br>(1081 vars, 3340 clauses) | UNSAT<br>0.0037s | Skipped | Unsat: 1 (Cible: 1)<br>2.4170s<br>(189627 flips) | Unsat: 16<br>12.4639s | Unsat: 1 (Cible: 1)<br>**12.8140s**<br>(22054 flips) | Unsat: 16<br>0.0349s<br>(1647 flips) | 88.4% |