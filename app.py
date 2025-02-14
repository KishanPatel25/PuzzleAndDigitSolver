# app.py
from flask import Flask, render_template, request, redirect, url_for
import itertools, json

app = Flask(__name__)
app.secret_key = "some_random_secret"

# --- Switch Puzzle Solver Functions ---

def GetOutcome(input_sequence, output_sequence):
    mapping = {char: index for index, char in enumerate(input_sequence)}
    outcome = [mapping[o] + 1 for o in output_sequence]
    return "".join(str(x) for x in outcome)

def compute_single(formula):
    fml, outcome = formula.split("=")
    parts = fml.split("+")
    parts.append(outcome)
    def switch(a, b):
        mapping = {index: char for index, char in enumerate(a)}
        new = [mapping[int(n) - 1] for n in b]
        return "".join(new)
    def reverse_switch(b, out_str):
        a = [""] * len(out_str)
        for i, char in enumerate(out_str):
            a[int(b[i]) - 1] = char
        return "".join(a)
    x_index = parts.index("x")
    lhs = parts[:x_index]
    rhs = parts[x_index+1:]
    if len(rhs) == 1:
        rhs_str = rhs[0]
    else:
        temp = rhs[-1]
        for i in range(1, len(rhs)):
            temp = reverse_switch(rhs[-i-1], temp)
        rhs_str = temp
    if len(lhs) == 0:
        return rhs_str
    elif len(lhs) == 1:
        return GetOutcome(lhs[0], rhs_str)
    else:
        seq = lhs[0]
        for row in lhs[1:]:
            seq = switch(seq, row)
        return GetOutcome(seq, rhs_str)

def switch_fn(a, b):
    mapping = {index: char for index, char in enumerate(a)}
    new = [mapping[int(d) - 1] for d in b]
    return "".join(new)

def all_permutations(s):
    return [''.join(p) for p in itertools.permutations(s)]

def candidate_score(perm):
    target = "1234"
    return sum(1 for a, b in zip(perm, target) if a != b)

def solve_two_unknowns(initial, final):
    perms = all_permutations("1234")
    valid_pairs = []
    for x1 in perms:
        mid = switch_fn(initial, x1)
        for x2 in perms:
            out = switch_fn(mid, x2)
            if out == final:
                valid_pairs.append((x1, x2))
    if not valid_pairs:
        return None, None, []
    best_pair = min(valid_pairs, key=lambda p: candidate_score(p[0]) + candidate_score(p[1]))
    return best_pair[0], best_pair[1], valid_pairs

# --- Routes for the Switch Puzzle Solver ---

@app.route("/", methods=["GET", "POST"])
def switch_solver():
    error = ""
    result = ""
    best_x1 = ""
    best_x2 = ""
    candidates = []
    filtered_pairs = []
    filter_x1 = ""
    puzzle_data_json = ""
    formula = ""
    
    if request.method == "POST":
        # If filtering for double unknown puzzle
        if "filter_submit" in request.form:
            formula = request.form.get("formula", "").strip()
            puzzle_data_json = request.form.get("puzzle_data_json", "")
            filter_x1 = request.form.get("filter_x1", "").strip()
            if not puzzle_data_json:
                error = "No pairs data available to filter."
            else:
                try:
                    puzzle_data = json.loads(puzzle_data_json)
                    best_x1 = puzzle_data.get("best_x1", "")
                    best_x2 = puzzle_data.get("best_x2", "")
                    candidates = puzzle_data.get("pairs", [])
                    result = puzzle_data.get("result_msg", "")
                    if filter_x1:
                        filtered_pairs = [p for p in candidates if p[0] == filter_x1]
                    else:
                        error = "Please enter an x1 to filter."
                except Exception as e:
                    error = f"Error filtering pairs: {e}"
        else:
            formula = request.form.get("formula", "").strip()
            if not formula:
                error = "Please enter a formula."
            else:
                if "x1" in formula and "x2" in formula:
                    try:
                        left, final_part = formula.split("=")
                        parts = [p.strip() for p in left.split("+")]
                        if len(parts) < 3:
                            error = "Double puzzle must have at least an initial part + x1 + x2."
                        else:
                            initial_part = parts[0]
                            bx1, bx2, cand = solve_two_unknowns(initial_part.upper(), final_part.upper())
                            if bx1 is None:
                                error = "No valid combination found for double unknown puzzle."
                            else:
                                best_x1, best_x2 = bx1, bx2
                                candidates = cand
                                msg = f"Double puzzle solved. Found {len(cand)} valid pairs."
                                result = msg
                                puzzle_data = {
                                    "pairs": candidates,
                                    "best_x1": best_x1,
                                    "best_x2": best_x2,
                                    "result_msg": msg
                                }
                                puzzle_data_json = json.dumps(puzzle_data)
                    except Exception as e:
                        error = f"Error processing double puzzle: {e}"
                elif "x" in formula:
                    try:
                        xval = compute_single(formula)
                        result = f"Single Unknown Result: x = {xval}"
                    except Exception as e:
                        error = f"Error processing single puzzle: {e}"
                else:
                    error = "Formula must contain 'x' or 'x1' and 'x2'."
    
    return render_template("switch_solver.html",
                           title="Switch Puzzle Solver",
                           formula=formula,
                           error=error,
                           result=result,
                           best_x1=best_x1,
                           best_x2=best_x2,
                           candidates=candidates,
                           puzzle_data_json=puzzle_data_json,
                           filter_x1=filter_x1,
                           filtered_pairs=filtered_pairs)

# --- Route for the Digit Calculation Solver ---

@app.route("/digit")
def digit_solver():
    return render_template("digit_solver.html", title="Digit Calculation Solver")

if __name__ == "__main__":
    app.run(debug=True)
