#!/usr/bin/env python3
"""
FLA Task 2 - Finite automata for real-time validation.
Author: B. Sai Nikhil (RA2411026050036)

Three DFAs (see the design note):
    mobile   10 digits, first digit 6-9                  q0..q10
    username letter first, no '__', no trailing '_'      u0..u2
    time     24-hour HH:MM                               t0..t6

Every unlisted move goes to the implicit dead state 'dead'.

Usage:
    python fa_validators.py demo                 # accept/reject tables
    python fa_validators.py check mobile 9876543210
    python fa_validators.py trace time 12:60     # step-by-step transitions
    python fa_validators.py live username ra__vi # status after each keystroke
    python fa_validators.py test                 # automatic cross-checks
    python fa_validators.py dot mobile           # Graphviz source of the DFA
"""
import argparse
import itertools
import random
import re
import string
import sys

DEAD = "dead"
GREEN, RED, YELLOW, DIM, BOLD, END = (
    "\033[92m", "\033[91m", "\033[93m", "\033[2m", "\033[1m", "\033[0m")


class DFA:
    def __init__(self, name, start, accepting, delta, classify, regex):
        self.name, self.start = name, start
        self.accepting, self.delta = set(accepting), delta
        self.classify, self.regex = classify, regex
        self.viable = self._viable_states()

    # ---- running the machine -------------------------------------------
    def run(self, word):
        """Return (final_state, rows). rows = (i, state, char, class, next)."""
        state, rows = self.start, []
        for i, ch in enumerate(word, 1):
            cls = self.classify(ch)
            nxt = self.delta.get((state, cls), DEAD)
            rows.append((i, state, ch, cls, nxt))
            state = nxt
            if state == DEAD:
                break
        return state, rows

    def accepts(self, word):
        return self.run(word)[0] in self.accepting

    def status(self, word):
        """ACCEPT / INCOMPLETE (valid prefix) / ERROR (dead or unviable)."""
        state, _ = self.run(word)
        if state in self.accepting:
            return "ACCEPT"
        return "INCOMPLETE" if state in self.viable else "ERROR"

    # ---- helpers -------------------------------------------------------
    def _viable_states(self):
        """States from which an accepting state is still reachable."""
        edges = {}
        for (s, _), t in self.delta.items():
            edges.setdefault(t, set()).add(s)
        seen, todo = set(self.accepting), list(self.accepting)
        while todo:
            for p in edges.get(todo.pop(), ()):
                if p not in seen:
                    seen.add(p)
                    todo.append(p)
        return seen

    def states(self):
        names = {self.start} | self.accepting
        for (s, _), t in self.delta.items():
            names |= {s, t}
        return sorted(names - {DEAD}, key=lambda x: (len(x), x))

    def to_dot(self):
        merged = {}
        for (s, c), t in self.delta.items():
            merged.setdefault((s, t), []).append(c)
        out = ["digraph DFA {", "  rankdir=LR;", '  node [shape=circle];',
               '  start [shape=point];', f"  start -> {self.start};"]
        for a in sorted(self.accepting):
            out.append(f"  {a} [shape=doublecircle];")
        for (s, t), cs in sorted(merged.items()):
            label = ", ".join(sorted(set(cs)))
            if len(label) > 18:
                label = label[:15] + "..."
            out.append(f'  {s} -> {t} [label="{label}"];')
        out.append("}")
        return "\n".join(out)


# ---------------------------------------------------------------------------
# Application 1: mobile number  [6-9][0-9]{9}
# ---------------------------------------------------------------------------
def mobile_dfa():
    delta = {("q0", d): "q1" for d in "6789"}
    for i in range(1, 10):
        for d in string.digits:
            delta[(f"q{i}", d)] = f"q{i + 1}"
    return DFA("Mobile number", "q0", {"q10"}, delta,
               lambda c: c if c in string.digits else None,
               r"[6-9][0-9]{9}")


# ---------------------------------------------------------------------------
# Application 2: username  L (U? (L|D))*
# ---------------------------------------------------------------------------
def username_class(ch):
    if ch in string.ascii_letters:
        return "L"
    if ch in string.digits:
        return "D"
    return "U" if ch == "_" else None


def username_dfa():
    delta = {("u0", "L"): "u1", ("u1", "L"): "u1", ("u1", "D"): "u1",
             ("u1", "U"): "u2", ("u2", "L"): "u1", ("u2", "D"): "u1"}
    return DFA("Username", "u0", {"u1"}, delta, username_class,
               r"[A-Za-z](_?[A-Za-z0-9])*")


# ---------------------------------------------------------------------------
# Application 3: 24-hour time  ([01][0-9] | 2[0-3]) : [0-5][0-9]
# ---------------------------------------------------------------------------
def time_dfa():
    delta = {}
    for d in "01":
        delta[("t0", d)] = "t1"
    delta[("t0", "2")] = "t2"
    for d in string.digits:
        delta[("t1", d)] = "t3"
    for d in "0123":
        delta[("t2", d)] = "t3"
    delta[("t3", ":")] = "t4"
    for d in "012345":
        delta[("t4", d)] = "t5"
    for d in string.digits:
        delta[("t5", d)] = "t6"
    return DFA("24-hour time", "t0", {"t6"}, delta,
               lambda c: c if c in string.digits + ":" else None,
               r"([01][0-9]|2[0-3]):[0-5][0-9]")


APPS = {"mobile": mobile_dfa(), "username": username_dfa(), "time": time_dfa()}

# Five accepted and five rejected strings per application (as in the report).
TESTS = {
    "mobile": (["9876543210", "6000000000", "7012345678", "8123456789", "9999999999"],
               ["5876543210", "987654321", "98765432101", "98765-43210", "0987654321"]),
    "username": (["a", "ravi_01", "sai_nikhil", "k9", "x_y_z"],
                 ["1ravi", "_ravi", "ravi_", "ra__vi", "ra-vi"]),
    "time": (["00:00", "09:45", "12:30", "19:05", "23:59"],
             ["24:00", "12:60", "1:30", "12-30", "2330"]),
}


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def verdict(ok):
    return f"{GREEN}ACCEPT{END}" if ok else f"{RED}REJECT{END}"


def show_trace(dfa, word):
    state, rows = dfa.run(word)
    print(f"{BOLD}{dfa.name}{END} on {word!r}")
    print(f"  {'#':>2}  {'state':<6} {'char':<5} {'class':<6} next")
    for i, s, ch, cls, nxt in rows:
        print(f"  {i:>2}  {s:<6} {ch!r:<5} {str(cls):<6} {nxt}")
    if not word:
        print("  (empty input)")
    print(f"  final state: {state} -> {verdict(state in dfa.accepting)}\n")


def cmd_demo(_):
    for key, dfa in APPS.items():
        good, bad = TESTS[key]
        print(f"\n{BOLD}== {dfa.name}  (regex: {dfa.regex}) =={END}")
        for w in good + bad:
            expected = w in good
            got = dfa.accepts(w)
            flag = "" if got == expected else f"  {RED}<-- MISMATCH{END}"
            print(f"  {w!r:<18} {verdict(got)}  (expected "
                  f"{'ACCEPT' if expected else 'REJECT'}){flag}")


def cmd_live(args):
    dfa = APPS[args.app]
    print(f"{BOLD}{dfa.name}{END}: status after each character typed")
    colour = {"ACCEPT": GREEN, "INCOMPLETE": YELLOW, "ERROR": RED}
    for i in range(0, len(args.text) + 1):
        prefix = args.text[:i]
        st = dfa.status(prefix)
        print(f"  {prefix!r:<20} {colour[st]}{st}{END}")
        if st == "ERROR":
            print(f"  {DIM}error at character {i}: {args.text[i - 1]!r}{END}")
            break


def cmd_test(_):
    random.seed(2026)
    failures = 0

    def check(name, word, dfa):
        nonlocal failures
        want = re.fullmatch(dfa.regex, word) is not None
        if dfa.accepts(word) != want:
            failures += 1
            print(f"{RED}MISMATCH{END} {name} {word!r}")

    # 1. the 5 + 5 report examples
    for key, (good, bad) in TESTS.items():
        for w in good:
            assert APPS[key].accepts(w), (key, w)
        for w in bad:
            assert not APPS[key].accepts(w), (key, w)
    print(f"report examples: 30 strings OK")

    # 2. exhaustive comparison with an independent regular expression
    n = 0
    for k in range(7):                       # username: every string, length <= 6
        for t in itertools.product("a1_-", repeat=k):
            check("username", "".join(t), APPS["username"]); n += 1
    for k in range(6):                       # time: every string, length <= 5
        for t in itertools.product(string.digits + ":", repeat=k):
            check("time", "".join(t), APPS["time"]); n += 1
    # mobile numbers are 10 long, so sample valid, mutated and random strings
    for _ in range(30000):
        base = random.choice("6789") + "".join(random.choice(string.digits) for _ in range(9))
        w = random.choice([base, base[:random.randint(0, 10)], base + random.choice("0-9"),
                           "".join(random.choice(string.digits + "-") for _ in range(random.randint(0, 12)))])
        check("mobile", w, APPS["mobile"]); n += 1
    print(f"DFA vs independent regex: {n:,} strings compared")
    print(f"{GREEN}ALL TESTS PASSED{END}" if not failures else f"{RED}{failures} FAILURES{END}")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo").set_defaults(fn=cmd_demo)
    sub.add_parser("test").set_defaults(fn=cmd_test)
    for name, fn in [("check", None), ("trace", None), ("live", None), ("dot", None)]:
        q = sub.add_parser(name)
        q.add_argument("app", choices=APPS)
        if name != "dot":
            q.add_argument("text")
    sub.choices["check"].set_defaults(fn=lambda a: print(
        f"{a.text!r}: {APPS[a.app].status(a.text)}"))
    sub.choices["trace"].set_defaults(fn=lambda a: show_trace(APPS[a.app], a.text))
    sub.choices["live"].set_defaults(fn=cmd_live)
    sub.choices["dot"].set_defaults(fn=lambda a: print(APPS[a.app].to_dot()))
    args = p.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
