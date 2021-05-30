import sys
import cfg



with open('input.txt', 'r') as f:
    lines = [x.strip() for x in f.readlines()]
    terminale = [x.strip() for x in lines[0].split()]
    neterminale = [x.strip() for x in lines[1].split()]
    start = lines[2].strip()

    g = cfg.CFG(terminale, neterminale, start)

    for line in lines[3:]:
        line = [x.strip() for x in line.split('=')]
        symbol = line[0]
        strings = [x.strip() for x in line[1].split('|')]

        g.addProduction(symbol, strings)

g.print()
print()

g.convertToCNF()

g.print()
g.print('output.txt')