# Rapport de Performance: Solveur MCMC Higher-Order pour 3-SAT

Ce tableau présente les performances du nouveau solveur MCMC **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).

L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation MCMC higher-order (warm-start) par rapport à un départ aléatoire (random-start).

| Instance | CDCL (Glucose4) | MaxSAT (RC2) | WalkSAT Pur (Target=0) | MCMC HO Seul | MCMC HO + WalkSAT (Target=0) | WalkSAT Pur (Ciblant MCMC HO Unsat) | Flips Gagnés (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **xor6**<br>(6 vars, 6 clauses) | SAT<br>0.0002s | OPT Unsat: 0<br>0.0084s | Unsat: 0<br>0.0001s<br>(0 flips) | Unsat: 0<br>0.0053s | Unsat: 0<br>**0.0054s**<br>(0 flips) | Unsat: 0<br>0.0000s<br>(0 flips) | 0.0% |
| **ph6**<br>(63 vars, 154 clauses) | UNSAT<br>0.0038s | OPT Unsat: 1<br>0.0112s | Unsat: 1<br>2.2165s<br>(300000 flips) | Unsat: 1<br>3.6786s | Unsat: 1<br>**5.7141s**<br>(300000 flips) | Unsat: 1<br>0.0013s<br>(86 flips) | 0.0% |
| **miter1**<br>(865 vars, 2488 clauses) | UNSAT<br>0.0071s | OPT Unsat: 1<br>0.0286s | Unsat: 1<br>3.7660s<br>(300000 flips) | Unsat: 5<br>9.8950s | Unsat: 1<br>**13.2238s**<br>(300000 flips) | Unsat: 5<br>0.0331s<br>(2748 flips) | 0.0% |
| **add32**<br>(695 vars, 1894 clauses) | UNSAT<br>0.0073s | OPT Unsat: 1<br>0.0324s | Unsat: 1<br>2.1639s<br>(300000 flips) | Unsat: 8<br>8.4213s | Unsat: 1<br>**11.0533s**<br>(300000 flips) | Unsat: 8<br>0.0174s<br>(861 flips) | 0.0% |
| **prime169**<br>(461 vars, 1342 clauses) | SAT<br>0.0029s | OPT Unsat: 0<br>0.0072s | Unsat: 1<br>1.9085s<br>(300000 flips) | Unsat: 15<br>8.8774s | Unsat: 1<br>**10.9548s**<br>(300000 flips) | Unsat: 15<br>0.0150s<br>(558 flips) | 0.0% |
| **add64**<br>(1428 vars, 3901 clauses) | UNSAT<br>0.0395s | Skipped | Unsat: 1<br>2.7813s<br>(300000 flips) | Unsat: 11<br>17.3598s | Unsat: 1<br>**19.9689s**<br>(300000 flips) | Unsat: 11<br>0.0774s<br>(3204 flips) | 0.0% |
| **add128**<br>(2282 vars, 6586 clauses) | UNSAT<br>0.1070s | Skipped | Unsat: 1<br>2.9572s<br>(300000 flips) | Unsat: 15<br>29.1907s | Unsat: 1<br>**32.2132s**<br>(300000 flips) | Unsat: 15<br>0.0861s<br>(8088 flips) | 0.0% |
| **prime841**<br>(791 vars, 2320 clauses) | SAT<br>0.0046s | OPT Unsat: 0<br>0.0186s | Unsat: 2<br>2.4410s<br>(300000 flips) | Unsat: 24<br>10.6037s | Unsat: 2<br>**13.2288s**<br>(300000 flips) | Unsat: 24<br>0.0374s<br>(1546 flips) | 0.0% |
| **sqrt10609**<br>(303 vars, 841 clauses) | SAT<br>0.0057s | OPT Unsat: 0<br>0.0126s | Unsat: 1<br>2.0294s<br>(300000 flips) | Unsat: 8<br>7.1457s | Unsat: 1<br>**9.8346s**<br>(300000 flips) | Unsat: 8<br>0.0124s<br>(670 flips) | 0.0% |
| **Miter_Small**<br>(91 vars, 268 clauses) | UNSAT<br>0.0005s | OPT Unsat: 1<br>0.0043s | Unsat: 1<br>3.6718s<br>(300000 flips) | Unsat: 1<br>3.3691s | Unsat: 1<br>**6.3546s**<br>(300000 flips) | Unsat: 1<br>0.0045s<br>(233 flips) | 0.0% |
| **Miter_Medium**<br>(331 vars, 1001 clauses) | SAT<br>0.0011s | OPT Unsat: 0<br>0.0064s | Unsat: 0<br>0.0293s<br>(1671 flips) | Unsat: 5<br>6.2837s | Unsat: 0<br>**6.3601s**<br>(4813 flips) | Unsat: 5<br>0.0231s<br>(841 flips) | -188.0% |
| **Miter_Large**<br>(651 vars, 2004 clauses) | UNSAT<br>0.0020s | OPT Unsat: 1<br>0.0109s | Unsat: 1<br>4.8256s<br>(300000 flips) | Unsat: 10<br>10.7573s | Unsat: 1<br>**13.7423s**<br>(300000 flips) | Unsat: 10<br>0.0267s<br>(1147 flips) | 0.0% |
| **Miter_Huge**<br>(1081 vars, 3340 clauses) | UNSAT<br>0.0036s | Skipped | Unsat: 1<br>3.6986s<br>(300000 flips) | Unsat: 14<br>16.3640s | Unsat: 1<br>**19.4545s**<br>(300000 flips) | Unsat: 14<br>0.0395s<br>(1722 flips) | 0.0% |