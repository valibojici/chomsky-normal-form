# chomsky-normal-form / forma-normala-chomsky
Aducerea unei gramatici independente de context in forma normala chomsky.
Fiecare terminal si neterminal trebuie sa fie o singura litera fara numere sau '_'
Fisierul de input trebuie sa aibe forma:

``` 
< terminale separate prin spatiu > 
< neterminale separate prin spatiu > 
< simbol start > 
< simbol = productie1 | productie2 | .... > 
```
<hr>

Exemplu input.txt:
```
a b c
S A B 
S 
S = bSa | aSb | SA | AS | c
A = aBa | bBb | $
B = c | cBc
```

output.txt
```
Start symbol: S_0
S_0 -> c | AS | SA | CG | EF
S -> c | AS | SA | CG | EF
A -> CH | EI
B -> c | DJ
F -> SC
G -> SE
H -> BC
I -> BE
J -> BD
C -> a
E -> b
D -> c
```

Daca simbolul de start este 'nonterminating symbol' atunci cand se apeleaza convertToCFG() gramatica se sterge

output.txt
```
Start symbol: None
```
