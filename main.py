from itertools import groupby


def parse_input(file_path):
    fsa = {'type': None, 'states': [], 'alphabet': [], 'initial': None, 'accepting': [], 'transitions': []}

    try:
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file.readlines()]
        if len(lines) != 6:
            print("E1: Input file is malformed")
            exit(0)
        for line in lines:
            if line.startswith('type=['):
                fsa['type'] = line.split('=')[1].strip('[]')
            elif line.startswith('states=['):
                fsa['states'] = line.split('=')[1].strip('[]').split(',')
            elif line.startswith('alphabet=['):
                fsa['alphabet'] = line.split('=')[1].strip('[]').split(',')
            elif line.startswith('initial=['):
                fsa['initial'] = line.split('=')[1].strip('[]')
            elif line.startswith('accepting=['):
                fsa['accepting'] = line.split('=')[1].strip('[]').split(',')
            elif line.startswith('transitions=['):
                transitions = line.split('=')[1].strip('[]').split(',')
                fsa['transitions'] = [tuple(trans.split('>')) for trans in transitions]
    except Exception as e:
        print("E1: Input file is malformed")
        exit(0)

    return fsa


def dfs_test(fsa):
    initial = fsa['initial']
    visited = []
    visited.append(initial)
    queue = []
    queue.append(initial)
    while len(queue) > 0:
        current = queue.pop(0)
        for transition in fsa['transitions']:
            if transition[0] == current:
                if transition[2] not in visited:
                    queue.append(transition[2])
                    visited.append(transition[2])
    if len(visited) != len(fsa['states']):
        return True
    return False


def is_deterministic(fsa):
    n_symbols = len(fsa['alphabet'])
    started = {}
    started[fsa['initial']] = []
    for transition in fsa['transitions']:
        if transition[0] in started:
            if transition[1] not in started[transition[0]]:
                started[transition[0]].append(transition[1])
            else:
                return True
        else:
            started[transition[0]] = []
            started[transition[0]].append(transition[1])
    return False


def validate_fsa(fsa):
    try:
        fsa['states'] = [el for el, _ in groupby(fsa['states'])]
        fsa['alphabet'] = [el for el, _ in groupby(fsa['alphabet'])]
        fsa['accepting'] = [el for el, _ in groupby(fsa['accepting'])]
        if fsa['states'][0] == "":
            return 'E1'
        if fsa['alphabet'][0] == "":
            return 'E1'
        for transition in fsa['transitions']:
            tr_copy = fsa['transitions'].copy()
            tr_copy.remove(transition)
            if transition in tr_copy:
                return 'E1'
        if not fsa['initial']:
            return 'E2'
        if fsa['accepting'][0] == "":
            return 'E3'
        if fsa['initial'] not in fsa['states']:
            return 'E4', fsa['initial']
        for s in fsa['accepting']:
            if s not in fsa['states']:
                return 'E4', s
        for s1, a, s2 in fsa['transitions']:
            if s1 not in fsa['states'] or s2 not in fsa['states']:
                return 'E4', s1 if s1 not in fsa['states'] else s2
            if a not in fsa['alphabet']:
                if a != "":
                    return 'E5', a
                else:
                    return 'E1'
        if dfs_test(fsa):
            return 'E6'
        if fsa['type'] == 'deterministic':
            if is_deterministic(fsa):
                return 'E7'
        return None
    except Exception:
        print("E1: Input file is malformed")
        exit(0)


def fsa_to_regexp(fsa):
    states = fsa['states']
    transitions = fsa['transitions']
    num_states = len(states)
    state_index = {state: i for i, state in enumerate(states)}

    # Initialize regular expression matrix with empty strings
    R = [[[[] for _ in range(num_states)] for _ in range(num_states)] for _ in range(num_states + 1)]

    # Populate the matrix with direct transitions
    for s1, a, s2 in transitions:
        if len(R[0][state_index[s1]][state_index[s2]]) == 0:
            R[0][state_index[s1]][state_index[s2]].append(a)
        else:
            R[0][state_index[s1]][state_index[s2]].append("|" + a)

    # Feeling the R^-1
    for i in range(num_states):
        for j in range(num_states):
            if i == j:
                if len(R[0][i][j]) == 0:
                    R[0][i][j].append("eps")
                else:
                    R[0][i][j].append("|eps")
            else:
                if len(R[0][i][j]) == 0:
                    R[0][i][j].append("{}")

    # Apply the modified Kleene's algorithm
    for k in range(1, num_states + 1):
        for i in range(num_states):
            for j in range(num_states):
                # New paths through k using R[i][k], R[k][k], and R[k][j]
                R[k][i][j] = [
                    '(' + "".join(R[k - 1][i][k - 1]) + ')' + '(' + "".join(R[k - 1][k - 1][k - 1]) + ')*' + '(' + ''.join(R[k - 1][k - 1][j]) + ')' + "|(" + ''.join(R[k - 1][i][j]) + ")"]


    # Build the regular expression from initial to accepting states
    initial_idx = state_index[fsa['initial']]
    accepting_exprs = []
    for acc_state in fsa['states']:
        if acc_state in fsa['accepting']:
            acc_idx = state_index[acc_state]
            accepting_exprs.extend(R[num_states][initial_idx][acc_idx])

    # Final regular expression
    final_regex = ""
    for i in range(len(accepting_exprs)):
        if i == 0:
            final_regex += "(" + accepting_exprs[i] + ")"
        else:
            final_regex += "|(" + accepting_exprs[i] + ")"
    return final_regex if final_regex else '{}'


file_path = 'input.txt'
fsa = parse_input(file_path)
validation_error = validate_fsa(fsa)
errors = {
        'E1': "E1: Input file is malformed",
        'E2': "E2: Initial state is not defined",
        'E3': "E3: Set of accepting states is empty",
        'E4': lambda s: f"E4: A state '{s}' is not in the set of states",
        'E5': lambda a: f"E5: A transition '{a}' is not represented in the alphabet",
        'E6': "E6: Some states are disjoint",
        'E7': "E7: FSA is non-deterministic"
    }
if validation_error:
    print(errors[validation_error[0]](validation_error[1]) if isinstance(validation_error, tuple) else errors[
        validation_error])
    exit(0)

regexp = fsa_to_regexp(fsa)
print(regexp)

