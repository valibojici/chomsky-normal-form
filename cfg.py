from abc import abstractproperty
from collections import defaultdict

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
        if letter.upper() not in self.nonterminals:
            self.nonterminals.add(letter.upper())
            return letter.upper()
        for i in range(0, 26):
            L = chr(ord('A') + i)
            if L not in self.nonterminals:
                self.nonterminals.add(L)
                return L
        for i in range(1,100):
            L = letter + '_' + str(i)
            if L not in self.nonterminals:
                self.nonterminals.add(L)
                return L    

    @classmethod
    def __splitIntoSymbols__(cls, string):
        result = []
        for c in string:
            if c == '_' or c.isnumeric():
                result[-1] = result[-1] + c
            else:
                result.append(c)
        return result

    def removeRedundantSymbols(self):
        ok = False
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():
                for string in v:
                    string = CFG.__splitIntoSymbols__(string)
                    newString = [x for x in string if x in self.nonterminals or x in self.terminals]
                    if string != newString:
                        ok = False
                    if len(newString):
                        newProductions[k].add(''.join(newString))
            self.productions = newProductions
            self.nonterminals = list(newProductions.keys())

        terminating = set()
        ok = False
        while not ok:
            ok = True
            for k, v in self.productions.items():
                if k in terminating:
                    continue
                for string in v:
                    symbols = CFG.__splitIntoSymbols__(string)
                    isTerminating = True
                    for s in symbols:
                        if s not in terminating and s not in self.terminals:
                            isTerminating = False
                    
                    if isTerminating:
                        terminating.add(k)
                        ok = False

        print(terminating)






    def convertToCNF(self):
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

        # 3. elimin productiile in care apar mai mult de 2 neterminale
        ok = False
        
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():
                for string in v:
                    nonterminals = CFG.__splitIntoSymbols__(string)                # splituiesc string-ul in neterminale
                    if len(nonterminals) <= 2:                                          # daca sunt mai putin de 2 neterminale atunci le las asa
                        newProductions[k].add(string)
                        continue
                    ok = False
                    newNonterminal = self.__getUnusedNonterminal__(nonterminals[1][0])  # nonterminals[1] poate fi cv de genul A_23 si iau doar A-ul
                    newProductions[k].add(f'{nonterminals[0]}{newNonterminal}')         # productia va deveni {primul neterminal}+{neterminalul nou 
                    newProductions[newNonterminal].add(''.join(nonterminals[1:]))       # care se va duce in restul de neterminale}
            self.productions = newProductions

        #########################################################################################################################################################################
        
        # 4. elimin lambda-productiile

        # mai intai caut lambda-neterminalele
        nullables = set()
        ok = False

        while not ok:
            ok = True
            for k, v in self.productions.items():
                if k in nullables or k == self.start:
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

        # gasesc neterminalele care s-au sters
        deletedNonterminals = set(self.nonterminals) - set(newProductions.keys())

        # actualizez neterminalele
        self.nonterminals = [x for x in self.productions.keys()]

        # elimin neterminalele care s-au sters din toate productiile
        self.productions = defaultdict(set)
        for k, v in newProductions.items():
            for string in v:
                string = CFG.__splitIntoSymbols__(string)
                string = [c for c in string if c not in deletedNonterminals] # daca am avut ceva de genul A -> BC si ambele sunt sterse nu mai adaug
                if len(string) > 0:
                    self.productions[k].add(''.join(string))

        #########################################################################################################################################################################

        # 5. elimin unit-productions

        deletedNonterminals = set()
        ok = False
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():
                for string in v:
                    nonterminals = CFG.__splitIntoSymbols__(string)
                    if len(nonterminals) == 1 and nonterminals[0] in self.nonterminals:
                        ok = False
                        if nonterminals[0] == k:
                            continue
                        newProductions[k].update(self.productions[nonterminals[0]])
                    else:
                        newProductions[k].add(string)

            deletedNonterminals = set(self.nonterminals) - set(newProductions.keys())
            self.nonterminals = [x for x in self.productions.keys()]
            self.productions = defaultdict(set)
            
            for k, v in newProductions.items():
                for string in v:
                    string = CFG.__splitIntoSymbols__(string)
                    string = [c for c in string if c not in deletedNonterminals] 
                    if len(string) > 0:
                        self.productions[k].add(''.join(string))

        


    def print(self, file=None):
        if file == None:
            print(f'Start symbol: {self.start}')
            for key, val in self.productions.items():
                print(key, '->', ' | '.join(val))



d = CFG(['a', 'b'], ['T', 'S', 'B'], 'S')
d.addProduction('S', ['Taaa', 'SS', 'SaSa', 'T', 'a'])
d.addProduction('T', ['$'])
d.addProduction('B', ['Ba'])
d.print()
d.removeRedundantSymbols()
d.print()
