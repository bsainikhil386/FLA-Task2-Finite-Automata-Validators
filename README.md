# FLA Task 2: Finite Automata for Real-Time Validation

Course 21CSC301T - Formal Language and Automata, SRM IST Tiruchirappalli.
Author: B. Sai Nikhil (RA2411026050036)

Three DFAs for input validation, matching the design note:

| App | Rule | States |
|---|---|---|
| `mobile` | 10 digits, first digit 6-9 | q0 to q10 |
| `username` | letter first, no `__`, no trailing `_` | u0 to u2 |
| `time` | 24-hour `HH:MM` | t0 to t6 |

Any move not listed goes to an implicit dead state.

## Run (Python 3.8+, no packages needed)

```
python fa_validators.py demo                    # 5 accepted + 5 rejected strings per app
python fa_validators.py check mobile 9876543210
python fa_validators.py trace time 12:60        # step-by-step transitions
python fa_validators.py live username ra__vi    # status after each keystroke
python fa_validators.py test                    # compares each DFA with an independent regex
python fa_validators.py dot time > time.dot     # Graphviz source of the DFA
```

`test` checks every username string up to length 6, every time string up to
length 5 and 30,000 sampled mobile numbers against Python's `re.fullmatch`.

## Syntax versus semantics
The DFAs check syntax only. Whether a mobile number is allocated, a username is
free or a time falls inside office hours needs a database, a clock or an
external service.
