from abc import abstractproperty
from collections import defaultdict

class CFG:
    def __init__(self, terminals = None, nonterminals = None, start = None):
        self.terminals = set(terminals)
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
    def __splitIntoNonterminals__(cls, string):
        result = []
        for c in string:
            if c == '_' or c.isnumeric():
                result[-1] = result[-1] + c
            else:
                result.append(c)
        return result


    def convertToCNF(self):
        # 1. daca simbolul de start se afla intr-o productie adaug un nou simbol de start
        found = any([self.start in string for strings in self.productions.values() for string in strings])
        if found:
            self.addProduction('S_0', [f'{self.start}'])
            self.start = 'S_0'
        ##########################################################################################################
        
        # 2. inlocuiesc neterminalele din fiecare productie, doar daca nu e de forma A -> a,
        #    cu un terminal care se duce in acel neterminal 

        terminal_dict = defaultdict(str)
        for terminal in self.terminals:
            terminal_dict[terminal] = self.__getUnusedNonterminal__(terminal)
        
        # adaug productiile noi
        for k,v in terminal_dict.items():
            self.addProduction(v, [k])
        

        # iau toate productiile si inlocuiesc terminalele care apar cu neterminale
        new_productions = defaultdict(set)
        for key, val in self.productions.items():
            for string in val:
                if len(string) == 1 and string in self.terminals:       # daca am ceva de genul A -> a le las asa
                    new_productions[key].add(string)
                else:
                    for k, v in terminal_dict.items():                  # altfel inlocuiesc fiecare terminal cu neterminalul nou
                        string = string.replace(k, v)
                    new_productions[key].add(string)

        self.productions = new_productions                              # la final updatez productiile
        ###############################################################################################################

        # 3. elimin productiile in care apar mai mult de 2 neterminale
        ok = False
        
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():
                for string in v:
                    nonterminals = CFG.__splitIntoNonterminals__(string)                # splituiesc string-ul in neterminale
                    if len(nonterminals) <= 2:                                          # daca sunt mai putin de 2 neterminale atunci le las asa
                        newProductions[k].add(string)
                        continue
                    ok = False
                    newNonterminal = self.__getUnusedNonterminal__(nonterminals[1][0])  # nonterminals[1] poate fi cv de genul A_23 si iau doar A-ul
                    newProductions[k].add(f'{nonterminals[0]}{newNonterminal}')         # productia va deveni {primul neterminal}+{neterminalul nou 
                    newProductions[newNonterminal].add(''.join(nonterminals[1:]))       # care se va duce in restul de neterminale}
            self.productions = newProductions
        ####################################################################################################################################
        
        # 4. elimin lambda-productiile

        # mai intai caut lambda-neterminalele
        nullables = set()
        ok = False

        while not ok:
            ok = True
            for k, v in self.productions.items():
                for string in v:
                    if string == '$' or all([(nonterminal in nullables) for nonterminal in CFG.__splitIntoNonterminals__(string)]):
                        if k in nullables or k == self.start:
                            continue
                        nullables.add(k)
                        ok = False
            
        print(nullables)




    def print(self, file=None):
        if file == None:
            print(f'Start symbol: {self.start}')
            for key, val in self.productions.items():
                print(key, '->', ' | '.join(val))

d = CFG(['a', 'b'], ['T', 'S'], 'S')
d.addProduction('S', ['Taaa', 'SS', 'SaSa', 'TT'])
d.addProduction('T', ['$', 'Tba'])
d.print()
d.convertToCNF()
d.print()
