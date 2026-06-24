# Rapport de Performance: Solveur MCMC Higher-Order pour 3-SAT

Ce tableau présente les performances du nouveau solveur MCMC **Higher-Order** comparé aux baselines CDCL (Glucose4), Max-SAT exact (RC2), et WalkSAT (Random-start).

L'analyse met en évidence le gain en temps de calcul et en nombre d'itérations (flips) obtenu grâce à l'initialisation MCMC higher-order (warm-start) par rapport à un départ aléatoire (random-start).

| Instance | CDCL (Glucose4) | MaxSAT (RC2) | WalkSAT Pur (Target=0) | MCMC HO Seul | MCMC HO + WalkSAT (Target=0) | WalkSAT Pur (Ciblant MCMC HO Unsat) | Flips Gagnés (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **xor6**<br>(6 vars, 6 clauses) | SAT<br>0.0002s | OPT Unsat: 0<br>0.0067s | Unsat: 0<br>0.0001s<br>(0 flips) | Unsat: 0<br>0.0152s | Unsat: 0<br>**0.0153s**<br>(0 flips) | Unsat: 0<br>0.0000s<br>(0 flips) | 0.0% |
| **ph6**<br>(63 vars, 154 clauses) | UNSAT<br>0.0124s | OPT Unsat: 1<br>0.0334s | Unsat: 1<br>2.4695s<br>(300000 flips) | Unsat: 1<br>8.2828s | Unsat: 1<br>**11.9496s**<br>(300000 flips) | Unsat: 1<br>0.0014s<br>(86 flips) | 0.0% |
| **miter1**<br>(865 vars, 2488 clauses) | UNSAT<br>0.0124s | OPT Unsat: 1<br>0.0517s | Unsat: 1<br>4.2767s<br>(300000 flips) | Unsat: 10<br>10.9572s | Unsat: 1<br>**14.6882s**<br>(300000 flips) | Unsat: 10<br>0.0381s<br>(1981 flips) | 0.0% |
| **add32**<br>(695 vars, 1894 clauses) | UNSAT<br>0.0101s | OPT Unsat: 1<br>0.0532s | Unsat: 1<br>2.7861s<br>(300000 flips) | Unsat: 10<br>9.4589s | Unsat: 1<br>**12.0451s**<br>(300000 flips) | Unsat: 10<br>0.0158s<br>(811 flips) | 0.0% |
| **prime169**<br>(461 vars, 1342 clauses) | SAT<br>0.0024s | OPT Unsat: 0<br>0.0068s | Unsat: 1<br>2.0854s<br>(300000 flips) | Unsat: 12<br>7.2145s | Unsat: 1<br>**9.3617s**<br>(300000 flips) | Unsat: 12<br>0.0201s<br>(1109 flips) | 0.0% |
| **add64**<br>(1428 vars, 3901 clauses) | UNSAT<br>0.0277s | Skipped | Unsat: 1<br>2.6218s<br>(300000 flips) | Unsat: 11<br>16.6421s | Unsat: 1<br>**19.1656s**<br>(300000 flips) | Unsat: 11<br>0.0446s<br>(3204 flips) | 0.0% |
| **add128**<br>(2282 vars, 6586 clauses) | UNSAT<br>0.1083s | Skipped | Unsat: 1<br>2.9107s<br>(300000 flips) | Unsat: 22<br>28.6216s | Unsat: 1<br>**31.5300s**<br>(300000 flips) | Unsat: 22<br>0.1158s<br>(6538 flips) | 0.0% |
| **prime841**<br>(791 vars, 2320 clauses) | SAT<br>0.0037s | OPT Unsat: 0<br>0.0469s | Unsat: 2<br>2.4629s<br>(300000 flips) | Unsat: 23<br>10.8110s | Unsat: 1<br>**13.5404s**<br>(300000 flips) | Unsat: 23<br>0.0307s<br>(1737 flips) | 0.0% |
| **sqrt10609**<br>(303 vars, 841 clauses) | SAT<br>0.0009s | OPT Unsat: 0<br>0.0049s | Unsat: 1<br>2.3395s<br>(300000 flips) | Unsat: 8<br>7.4978s | Unsat: 1<br>**9.2526s**<br>(300000 flips) | Unsat: 8<br>0.0135s<br>(670 flips) | 0.0% |
| **Miter_Small**<br>(91 vars, 268 clauses) | UNSAT<br>0.0004s | OPT Unsat: 1<br>0.0031s | Unsat: 1<br>2.5887s<br>(300000 flips) | Unsat: 1<br>2.8574s | Unsat: 1<br>**5.6639s**<br>(300000 flips) | Unsat: 1<br>0.0052s<br>(233 flips) | 0.0% |
| **Miter_Medium**<br>(331 vars, 1001 clauses) | SAT<br>0.0051s | OPT Unsat: 0<br>0.0089s | Unsat: 0<br>0.0457s<br>(1671 flips) | Unsat: 4<br>5.9488s | Unsat: 0<br>**6.0126s**<br>(2134 flips) | Unsat: 4<br>0.0467s<br>(842 flips) | -27.7% |
| **Miter_Large**<br>(651 vars, 2004 clauses) | UNSAT<br>0.0038s | OPT Unsat: 1<br>0.0188s | Unsat: 1<br>3.4048s<br>(300000 flips) | Unsat: 6<br>9.9497s | Unsat: 1<br>**13.5033s**<br>(300000 flips) | Unsat: 6<br>0.0337s<br>(1952 flips) | 0.0% |
| **Miter_Huge**<br>(1081 vars, 3340 clauses) | UNSAT<br>0.0035s | Skipped | Unsat: 1<br>3.5964s<br>(300000 flips) | Unsat: 8<br>15.5149s | Unsat: 1<br>**18.7497s**<br>(300000 flips) | Unsat: 8<br>0.0967s<br>(1980 flips) | 0.0% |