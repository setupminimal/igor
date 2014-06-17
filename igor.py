import re, os

dbg = False

term_regex = r'''(?mx)
    \s*(?:
        (?P<brackl>\()|
        (?P<brackr>\))|
        (?P<num>\-?\d+\.\d+|\-?\d+)|
        (?P<sq>"[^"]*")|
        (?P<s>[^(^)\s]+)
       )'''

def preFunctionSugar(sexp): # MY FUNCTION
    l = sexp.split()
    for i in range(0, len(l)):
        if l[i].endswith("("):
            l[i] = "(" + l[i][0:(len(l[i]) - 1)]
    return " ".join(l)

def parse_sexp(sexp):
    stack = []
    out = []
    #MY CHANGE
    sexp = preFunctionSugar(sexp)
    #END CHANGE
    if dbg: print("%-6s %-14s %-44s %-s" % tuple("term value out stack".split()))
    for termtypes in re.finditer(term_regex, sexp):
        term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]
        if dbg: print("%-7s %-14s %-44r %-r" % (term, value, out, stack))
        if   term == 'brackl':
            stack.append(out)
            out = []
        elif term == 'brackr':
            assert stack, "Trouble with nesting of brackets"
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)
        elif term == 'num':
            v = float(value)
            if v.is_integer(): v = int(v)
            out.append(v)
        elif term == 'sq':
            out.append(value[1:-1])
        elif term == 's':
            out.append(value)
        else:
            raise NotImplementedError("Error: %r" % (term, value))
    assert not stack, "Trouble with nesting of brackets"
    return out[0]

def print_sexp(exp):
    out = ''
    if type(exp) == type([]):
        out += '(' + ' '.join(print_sexp(x) for x in exp) + ')'
    elif type(exp) == type('') and re.search(r'[\s()]', exp):
        out += '"%s"' % repr(exp)[1:-1].replace('"', '\"')
    else:
        out += '%s' % exp
    return out

# BEGIN MY CODE

SYMBOL_MAPPING = {"nil": []}

SYMBOL_MAPPING["apply"] = lambda l: evil([l[0]] + [l[1]])
SYMBOL_MAPPING["eval"] = lambda l: [evil(item) for item in l][-1]
SYMBOL_MAPPING["evil"] = lambda l: [evil(item) for item in l][-1]
SYMBOL_MAPPING["eq"] = lambda l: "t" if l[0] == l[1] else "f"
SYMBOL_MAPPING["cons"] = lambda l: [l[0]] + l[1]
SYMBOL_MAPPING["car"] = lambda l: l[0][0]
SYMBOL_MAPPING["cdr"] = lambda l: l[0][1:len(l[0])]
SYMBOL_MAPPING["atom"] = lambda l: "f" if isinstance(l[0], list) and not l[0] == [] else "t"
SYMBOL_MAPPING["internal-representation"] = lambda l: print(l)
SYMBOL_MAPPING["command"] = lambda l: os.system(l[0])
SYMBOL_MAPPING["str->code"] = lambda l: parse_sexp(l[0])

BUILTINS = ["apply", "eval", "evil", "eq", "cons", "car", "cdr", "atom", "internal-representation", "command", "str->code"]

NO_EVILS = ["quote", "fn", "if", "'"]

def putInsInBody(inputsName, body, inputs):
    if isinstance(body, list):
        for i in range(0, len(body)):
            if isinstance(body[i], list):
                body[i] = putInsInBody(inputsName, body[i], inputs)
            if body[i] in inputsName:
                p = inputsName.index(body[i])
                if not isinstance(inputs[p], list):
                    body[i] = inputs[p]
                else:
                    body[i] = ["'", inputs[p]]
        return body
    else:
        print("Warning in putInsInBody")
        return body

def makeFn(inputs, body):
    def func(l, T=0, inp=inputs, bo=body):
        if T==0:
            return evil(putInsInBody(inp, bo, l))
        else:
            return (inp, bo, T, l)
    return func

def newFn(f):
    p = f([], T=1)
    return makeFn(p[0], p[1])

def evil(exp):
    global SYMBOL_MAPPING
    if not isinstance(exp, list):
        if exp in SYMBOL_MAPPING.keys():
            return SYMBOL_MAPPING[exp]
        else:
            return exp
    elif not exp == []:
        if exp[0] in NO_EVILS:
            # Special Stuff
            if exp[0] == "'" or exp[0] == "quote":
                return exp[1]
            elif exp[0] == "fn":
                return makeFn(exp[1], exp[2])
            elif exp[0] == "if":
                exp[1] = evil(exp[1])
                if not (exp[1] == "f" or exp[1] == [] or exp[1] == "nil"):
                    return evil(exp[2])
                else:
                    return evil(exp[3])
            else:
                print("Something in NO_EVILS unaccounted for.")
                return exp
        else:
            # Normal recursive evaluation
            flat = []
            for item in exp:
                flat.append(evil(item))
            if isinstance(flat[0], type(lambda x: x*x)):
                for k, v in SYMBOL_MAPPING.items():
                    if v == flat[0] and not k in BUILTINS:
                        SYMBOL_MAPPING[k] = newFn(v)
                return flat[0](flat[1:len(flat)])
            elif flat[0] == "define":
                SYMBOL_MAPPING[flat[1]] = flat[2]
                return flat[1]
            elif flat[0] == "slurp":
                if flat[1] == "-":
                    if len(flat) == 3:
                        return input(flat[2])
                    else:
                        return input("")
                else:
                    with open(flat[1]) as f:
                        t = f.read()
                    return t
            elif flat[0] == "spit":
                if flat[1] == "-":
                    print(flat[2])
                    return "t"
                else:
                    with open(flat[1], 'w') as f:
                        f.write(flat[2])
                    return "t"
            else:
                print("Wierdness evaluating "+print_sexp(exp))
    else:
        print("Warning, tried to evaluate the empty list.")
        return []



if __name__ == '__main__':
    print("Bootstrap Igor")
    evil(parse_sexp('(eval (str->code (slurp "/home/carl/systemLibrary.ig")))'))
    print("Loaded System Library")
    while True:
        x = input(":] ")
        x = parse_sexp(x)
        x = evil(x)
        print(print_sexp(x))
