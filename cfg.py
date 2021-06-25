from collections import defaultdict
import copy

class CFG:
    def __init__(self, terminals = None, nonterminals = None, start = None):
        self.terminals = set(terminals)
        self.terminals.add('$')
        self.nonterminals = set(nonterminals)
        self.productions = defaultdict(set)
        self.start = start

    def addProduction(self, symbol, string):
        self.productions[symbol].update(string)

    def __getUnusedNonterminal__(self, letter):
        # gasesc un neterminal nou, care nu exista
        # incerc mai intai letter.upper(), ca sa aibe mai mult sens gen A -> a in loc de D -> a
        # daca nu se poate iau alta litera din alfabet
        # daca nici asa nu se poate iau pe rand fiecare litera si ii pun indici A_4 de exemplu

        if letter.upper() not in self.nonterminals:
            self.nonterminals.add(letter.upper())
            return letter.upper()
        for i in range(0, 26):
            L = chr(ord('A') + i)
            if L not in self.nonterminals:
                self.nonterminals.add(L)
                return L

        for i in range(0, 26):
            letter = chr(ord('A') + i)
            for j in range(1,10):
                L = letter + '_' + str(j)
                if L not in self.nonterminals:
                    self.nonterminals.add(L)
                    return L    


    @classmethod
    def __splitIntoSymbols__(cls, string):
        # splituiesc string-ul in neterminale si terminale

        result = []
        for c in string:
            if c == '_' or c.isnumeric():
                result[-1] = result[-1] + c
            else:
                result.append(c)
        return result

    
    def removeDeletedNonterminals(self):
        # sterg neterminalele din productii daca acele neterminale nu mai exista (au fost sterse)
        # adica in productii apar neterminale care nu sunt in self.nonterminals
        ok = False
        while not ok:                                                   # cat timp se sterg neterminale 
            ok = True
            newProductions = defaultdict(set)                           # in newProductions pun simbolurile si productiile valide
            for k, v in self.productions.items():
                if k not in self.nonterminals:                          # daca neterminalul curent nu mai exista, il elimin cu tot cu productiile lui
                    continue
                for string in v:                                        # iau fiecare productie si elimin de acolo daca exista neterminale sterse
                    string = CFG.__splitIntoSymbols__(string)                                               # splituiesc string in neterminale si terminale
                    newString = [x for x in string if x in self.nonterminals or x in self.terminals]        # din string iau doar terminalele si neterminalele care exista
                    if string != newString:                                                                 # daca string != newString inseamna ca in string apar neterminale sterse deci continui cu while-ul
                        ok = False                                                                                  # s-ar putea sa am A -> B, sterg B si acum A -> '' deci trb sters si A
                    if len(newString):                                                                      # daca mai am ceva in string dupa ce am eliminat neterminalele sterse
                        newProductions[k].add(''.join(newString))
            self.productions = newProductions
            self.nonterminals = set(newProductions.keys())            # updatez si neterminalele pt ca s-ar putea sa fie sterse si alte neterminale daca in productii erau doar neterminale sterse


    def removeRedundantSymbols(self):

        # 1. sterg non-terminating symbols

        # simbolul e terminating daca toate simbolurile dintr-o productie de a lui sunt terminating
        # terminalele si $ sunt terminating
        terminating = set()
        ok = False
        while not ok:
            ok = True
            for k, v in self.productions.items():
                if k in terminating:                                            # daca simbolul curent e terminating trec mai departe
                    continue
                for string in v:                                                # ma uit la fiecare prodcutie a simbolului
                    symbols = CFG.__splitIntoSymbols__(string)                  # despart string-ul in simboluri (terminale si neterminale)
                    isTerminating = True                                        # presupun ca simbolul (din stanga productiei) e terminating
                    for s in symbols:                                           # verific daca toate simbolurile din string sunt terminating
                        if s not in terminating and s not in self.terminals:    # daca simbolul nu e in terminating si nici nu e terminal atunci trebuie sa verific alta productie
                            isTerminating = False
                    
                    if isTerminating:                                           # daca am o productie in care toate simbolurile sunt 'terminating' atunci si simbolul din dreapta productiei e 'terminating'
                        terminating.add(k)
                        ok = False

        self.nonterminals = terminating

        # daca simbolul de start nu e 'terminating' nu este ok
        if self.start not in terminating:                                   
            raise ValueError('Simbolul de start nu e terminating!')

        # sterg simbolurile 'nonterminating'
        self.removeDeletedNonterminals()    
        #############################################################################################################################################################################################################
        
        # 2. sterg unreachable symbols 

        # simbolul e 'reachable' daca pot sa ajung in el din simbolul de start
        reachable = set(self.start)
        stack = [self.start]
        
        while len(stack) > 0:       # fac un fel de DFS ca sa gasesc simbolurile accesibile plecand de la simbolul de start
            top = stack[-1]
            stack.pop()
            for string in self.productions[top]:
                symbols = [x for x in CFG.__splitIntoSymbols__(string) if x in self.nonterminals]
                for s in symbols:
                    if s not in reachable:
                        reachable.add(s)
                        stack.append(s)

        self.nonterminals = reachable

        # sterg simbolurile unreachable
        self.removeDeletedNonterminals()
 
    def __replaceSymbol__(self, old, new):
        newProductions = defaultdict(set)
        for k,v in self.productions.items():
            for string in v:
                string = string.replace(old, new)
                newProductions[k].add(string)

        self.nonterminals.remove(old)
        self.productions = newProductions
        self.removeDeletedNonterminals()

    def __convertToCNF__(self):

        self.removeRedundantSymbols()
 
        # 1. daca simbolul de start se afla intr-o productie adaug un nou simbol de start
        found = any([self.start in string for strings in self.productions.values() for string in strings])
        if found:
            self.addProduction('S_0', [f'{self.start}'])
            self.start = 'S_0'

        #########################################################################################################################################################################
        
        # 2. inlocuiesc terminalele din fiecare productie, doar daca nu e de forma A -> a,
        #    cu un neterminal care se duce in acel terminal 

        # pt fiecare terminal creez un neterminal care nu e folosit
        terminal_dict = defaultdict(str)
 
        for terminal in self.terminals:
            for k, v in self.productions.items():       # verific daca exista deja o productie in care apare doar neterminalul asta
                if len(v) == 1 and terminal in v:
                    terminal_dict[terminal] = k
                    break
            else:
                terminal_dict[terminal] = self.__getUnusedNonterminal__(terminal)     

         
        # iau toate productiile si inlocuiesc terminalele care apar cu neterminale
        new_productions = defaultdict(set)
        for key, val in self.productions.items():
            for string in val:
                if len(string) == 1 and string in self.terminals:       # daca am ceva de genul A -> a le las asa
                    new_productions[key].add(string)
                else:
                    for k, v in terminal_dict.items():                  # altfel inlocuiesc fiecare terminal cu neterminalul nou
                        if k in string:                                 
                            string = string.replace(k, v)               # inlocuiesc terminalul cu neterminal
                            new_productions[v].add(k)                   # adaug productia neterminal -> terminal

                    new_productions[key].add(string)

        self.productions = new_productions                              # la final updatez productiile

        #########################################################################################################################################################################
         
        # 3. inlocuiesc productiile in care apar mai mult de 2 neterminale cu doar 2 neterminale
        
        newNonterminals = dict()
        ok = False
        
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():
                
                for string in v:
                    nonterminals = CFG.__splitIntoSymbols__(string)                     # splituiesc string-ul in neterminale
                    if len(nonterminals) <= 2:                                          # daca sunt mai putin de 2 neterminale atunci le las asa
                        newProductions[k].add(string)
                        continue
                    ok = False

                    newNonterminal = None
                                                
                    for nonterminal in newNonterminals:                                 # verific sa nu existe un neterminal nou adaugat care sa faca acelasi lucru
                        if ''.join(nonterminals[1:]) == newNonterminals.get(nonterminal):
                            newNonterminal = nonterminal
 
                    if newNonterminal is None:                                                  # daca nu mai exista alt neterminal atunci creez unul
                        newNonterminal = self.__getUnusedNonterminal__(nonterminals[1][0])      # nonterminals[1] poate fi cv de genul A_23 si iau doar A-ul
                        newNonterminals[newNonterminal] = ''.join(nonterminals[1:])             # newNonterminal se duce in restul de neterminale (nonterminals[1:])
                        self.nonterminals.add(newNonterminal)  
                        newProductions[newNonterminal].add(''.join(nonterminals[1:]))           # noul neterminal care se va duce in restul de neterminale

                    newProductions[k].add(nonterminals[0] + newNonterminal)                 # productia va deveni {primul neterminal}+{neterminalul nou}
                    
            self.productions = newProductions
            

        #########################################################################################################################################################################
        
        # 4. elimin lambda-productiile

        # mai intai caut lambda-neterminalele
        nullables = set()
        ok = False

        while not ok:
            ok = True
            for k, v in self.productions.items():
                if k in nullables:
                    continue
                for string in v:
                    if string == '$' or all([nonterminal in nullables for nonterminal in CFG.__splitIntoSymbols__(string)]):
                        nullables.add(k)
                        ok = False
        
        # am prodcutii doar de forma A -> a($), A -> B sau A -> BC  
        newProductions = defaultdict(set)
        for k, v in self.productions.items():
            newProductions[k] = set(v)                                              # la productiile deja existente adaug productii noi in care sterg un neterminal
            for string in v:
                nonterminals = CFG.__splitIntoSymbols__(string)                     # splituiesc string-ul in simboluri
                if len(nonterminals) == 1 and nonterminals[0] in nullables:         # daca e doar 1 simbol si e lambda-neterminal adaug $ la productie
                    newProductions[k].add('$')
                elif len(nonterminals) == 2:                                        # daca sunt 2 simboluri gen A -> BC
                    if nonterminals[0] in nullables:                                # daca B e nullable
                        newProductions[k].add(nonterminals[1])                      # atunci adaug A -> C
                    if nonterminals[1] in nullables:                                # daca C e nullable
                        newProductions[k].add(nonterminals[0])                      # adaug A -> B
                    if nonterminals[0] in nullables and nonterminals[1] in nullables:
                        newProductions[k].add('$')                                  # daca ambele sunt nullable adaug A -> $

        # elimin productiile de forma A -> $ 
        newProductions = {k : v.difference(['$']) for k,v in newProductions.items() if len(v.difference(['$'])) > 0}

        # actualizez neterminalele si productiile
        self.nonterminals = set(newProductions.keys())
        self.productions = newProductions

        # daca simbolul de start era lambda neterminal atunci adaug productia S -> $
        if self.start in nullables:
            self.productions[self.start].add('$')

        # sterg neterminalele eliminate (de genul A -> $) din productii 
        self.removeDeletedNonterminals()

        #########################################################################################################################################################################

        # 5. elimin unit-productions

        deletedNonterminals = set()
        ok = False
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():                                           # iau fiecare productie pe rand
                for string in v:
                    nonterminals = CFG.__splitIntoSymbols__(string)                         # splituiesc in neterminale (sau doar 1 terminal eventual)
                    if len(nonterminals) == 1 and nonterminals[0] in self.nonterminals:     # daca am doar un neterminal atunci trebuie eliminat
                        ok = False
                        if nonterminals[0] == k:                                            # daca e ceva de genul A -> A ignor
                            continue
                        newProductions[k].update(self.productions[nonterminals[0]])         # altfel la productiile simbolului curent adaug productiile celulalt simbol
                    else:
                        newProductions[k].add(string)                                       # daca NU am doar un neterminal (am 2) le las asa
        
            self.productions = newProductions
            self.nonterminals = set(newProductions.keys())                                  # updatez productiile, neterminalele si sterg neterminalele eliminate (gen A -> A, elimin A)
            self.removeDeletedNonterminals()

        #########################################################################################################################################################################

        

    def isCNF(self):
        # verific daca e in CNF
        for k, v in self.productions.items():
            for string in v:
                string = CFG.__splitIntoSymbols__(string)
                if len(string) != 2 and len(string) != 1:                       # daca productia nu are fix 2 sau 1 simboluri atunci nu e in CNF
                    return False
                else:
                    if len(string) == 1 and string[0] not in self.terminals:    # daca productia are 1 simbol si nu e terminal atunci nu e in CNF
                        return False
                    elif len(string) == 2 and (string[0] not in self.nonterminals or string[1] not in self.nonterminals):   # daca productia are 2 simboluri si nu sunt neterminale atunci nu e in CNF
                        return False
        return True


    def convertToCNF(self):
        if not self.isCNF():
            try:
                while not self.isCNF():
                    self.__convertToCNF__()
            except ValueError:
                self.start = None
                self.productions.clear()
                self.nonterminals.clear()
                self.terminals.clear()
                print('Simbolul de start nu e terminating!')
                return False


        # iau toate neterminalele si verific dau au productii identice ca se le elimin
        ok = False
        while not ok:
            ok = True
            for k1 in self.productions.keys():
                if k1 == self.start: 
                    continue
                for k2 in self.productions.keys():
                    if k2 == self.start:
                        continue
                    if k1 != k2 and self.productions[k1] == self.productions[k2]:
                        self.__replaceSymbol__(k1, k2)
                        ok = False
                        break
                if not ok: 
                    break



        return True



    def print(self, file=None):
        if file == None:
            print(f'Start symbol: {self.start}')
            if len(self.productions) == 0:
                return
            
            print(self.start, '->', ' | '.join(self.productions[self.start]))
            
            for key, val in sorted(self.productions.items(),key=lambda x : (-len(x[1]), list(x[1])[0] in self.terminals)):
                if key != self.start:
                    print(key, '->', ' | '.join(val))
        else:
            with open(file, 'w') as f:
                f.write(f'Start symbol: {self.start}\n')
                if len(self.productions) == 0:
                    return
                
                f.write(self.start + ' -> ' + ' | '.join(self.productions[self.start]) + '\n')
                
                for key, val in sorted(self.productions.items(),key=lambda x : (-len(x[1]), list(x[1])[0] in self.terminals) ):
                    if key != self.start:
                        f.write(str(key) + ' -> ' + ' | '.join(val) + '\n')
 



if __name__ == '__main__':
    with open('input.txt', 'r') as f:
        lines = [x.strip() for x in f.readlines()]
        terminale = [x.strip() for x in lines[0].split()]
        neterminale = [x.strip() for x in lines[1].split()]
        start = lines[2].strip()

        g = CFG(terminale, neterminale, start)

        for line in lines[3:]:
            line = [x.strip() for x in line.split('=')]
            symbol = line[0]
            strings = [x.strip() for x in line[1].split('|')]

            g.addProduction(symbol, strings)

    print('Input:')
    g.print()

    print('\nChomsky normal form: ')
    g.convertToCNF()


    g.print()
    g.print('output.txt')