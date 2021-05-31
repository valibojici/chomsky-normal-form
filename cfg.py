from abc import abstractproperty
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

    
    def removeDeletedNonterminals(self):
        # sterg neterminalele din productii daca acele neterminale nu mai exista (au fost sterse)
        ok = False
        while not ok:
            ok = True
            newProductions = defaultdict(set)
            for k, v in self.productions.items():
                if k not in self.nonterminals:                          # daca neterminalul curent nu mai exista, nu mai conteaza de productii a avut
                    continue
                for string in v:                                        # iau fiecare productie si elimin de acolo daca exista neterminale sterse
                    string = CFG.__splitIntoSymbols__(string)
                    newString = [x for x in string if x in self.nonterminals or x in self.terminals]
                    if string != newString:
                        ok = False
                    if len(newString):
                        newProductions[k].add(''.join(newString))
            self.productions = newProductions
            self.nonterminals = set(newProductions.keys())            # updatez si neterminalele pt ca s-ar putea sa fie sterse si alte neterminale daca in productii erau doar neterminale sterse


    def removeRedundantSymbols(self):
        self.removeDeletedNonterminals()        
     
        # sterg non-terminating symbols
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

        self.nonterminals = terminating

        if self.start not in terminating:
            raise ValueError('Simbolul de start nu e terminating!')

        self.removeDeletedNonterminals()    

        # sterg unreachable symbols 
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
                    print(v)
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

        # actualizez neterminalele si productiile
        self.nonterminals = set(newProductions.keys())
        self.productions = newProductions

        # sterg neterminalele eliminate (de genul A -> $) din productii 
        self.removeDeletedNonterminals()

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
                        if nonterminals[0] == k:    # daca e ceva de genul A -> A ignor
                            continue
                        newProductions[k].update(self.productions[nonterminals[0]])
                    else:
                        newProductions[k].add(string)
        
            self.productions = newProductions
            self.nonterminals = set(newProductions.keys())
            self.removeDeletedNonterminals()
        

    def isCNF(self):
        for k, v in self.productions.items():
            for string in v:
                string = CFG.__splitIntoSymbols__(string)
                if len(string) != 2 and len(string) != 1: 
                    return False
                else:
                    if len(string) == 1 and string[0] not in self.terminals:
                        return False
                    elif len(string) == 2 and (string[0] not in self.nonterminals or string[1] not in self.nonterminals):
                        return False
        return True


    def convertToCNF(self):
        if not self.isCNF():
            try:
                self.removeRedundantSymbols()
                self.__convertToCNF__()
            except ValueError:
                print('Simbolul de start nu e terminating!')



    def print(self, file=None):
        if len(self.productions) == 0:
            return
        if file == None:
            print(f'Start symbol: {self.start}')
            print(self.start, '->', ' | '.join(self.productions[self.start]))
            # for key, val in sorted(self.productions.items(),key=lambda x : (-len(x[1]), list(x[1])[0] in self.terminals) ):
            for key, val in self.productions.items():
                if key != self.start:
                    print(key, '->', ' | '.join(val))
        else:
            with open(file, 'w') as f:
                f.write(f'Start symbol: {self.start}\n')
                f.write(self.start + ' -> ' + ' | '.join(self.productions[self.start]) + '\n')
                for key, val in sorted(self.productions.items(),key=lambda x : (-len(x[1]), list(x[1])[0] in self.terminals) ):
                    if key != self.start:
                        f.write(str(key) + ' -> ' + ' | '.join(val) + '\n')



# d = CFG(['a', 'b'], ['T', 'S', 'B', 'A', 'C'], 'S')
# d.addProduction('S', ['Taaa', 'SS', 'SaSa', 'T', 'a'])
# d.addProduction('T', ['a', 'BB'])
# d.addProduction('B', ['Ba'])
# d.addProduction('A', ['C'])
# d.addProduction('C', ['AA', 'B'])
# d.print()
# c = copy.deepcopy(d)
# d.convertToCNF()
# d.print()
# c.print()