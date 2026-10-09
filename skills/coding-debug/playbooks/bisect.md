<!-- coding:guidance -->
# Bisect — isolating the cause

Two moves isolate almost every bug: cut the history in half, or cut the system
in half. Both work by removing possibilities, not by accumulating suspicions.

## Bisecting history

Use when it worked before. Cheapest first move whenever a good commit exists.

1. Find a good commit and a bad one, and **verify both by running the
   reproduction** — a bisect anchored on an unverified "good" wastes every step
2. `git bisect start && git bisect bad <bad> && git bisect good <good>`
3. Script the check and use `git bisect run <script>`. The script must exit
   non-zero **only** for this failure — a build error at some midpoint scores as
   bad and points at the wrong commit. Exit 125 for "cannot test this commit"
4. **Keep the script outside the working tree.** Each step checks out an older
   commit, and a script committed into the repo disappears at every commit that
   predates it. Git reports `bogus exit code 127` and stops the run, leaving the
   bisect open and `HEAD` detached at the midpoint — it reads as a broken
   repository and is a path problem. Pass an absolute path
   from a temporary directory instead
5. When it lands on a commit, **read the diff and explain the mechanism**. The
   bisect names the change; it does not explain it. A merge commit or a
   thousand-line refactor means the answer is a lead, not a cause
6. **`git bisect reset` before doing anything else.** A bisect left running
   leaves you on a detached `HEAD` at an arbitrary commit, and every edit after
   that lands somewhere no branch points at

Traps: flaky failures make bisect return nonsense — stabilise first;
`node_modules`/build artifacts must be rebuilt at each step or you are testing
the wrong tree; a bug introduced dormant and exposed later lands on the exposing
commit, not the causing one.

## Bisecting the system

Use when history is no help — it never worked, or the reproduction is new.

Take the path from input to wrong output and pick a **midpoint** where the value
can be observed. Is it correct there?

- **Correct at the midpoint** → the fault is downstream. Bisect that half
- **Wrong at the midpoint** → the fault is upstream. Bisect that half

Each observation halves the search space. Three or four cuts localise most bugs
to a function. Good midpoints: a boundary crossing, a serialisation step, a
layer entry, a queue, the point where a value is transformed.

## Observing without lying to yourself

- **Print the value and the type**, not just the value. `"1"` and `1` and `1.0`
  print similarly and behave differently
- **Print at the boundary in both directions.** What was sent and what was
  received, separately — the difference is often the bug
- **A debugger beats prints** where stepping is available and state is complex;
  prints beat a debugger for anything concurrent, timing-sensitive, or remote
- **Diff a working case against the failing one.** Two inputs, same code path,
  one works: the difference between the inputs is the shortest route to the cause

## Hypothesis discipline

- **One change at a time.** Two changes make the next result uninterpretable,
  and you will not remember which you undid
- **Try to disprove, not to confirm.** Ask "what would I see if this hypothesis
  were false?" and go look for that
- **Write down what was ruled out**, with how. An investigation without this
  list revisits the same dead end an hour later
- **After two failed hypotheses in one area, question the premise** (the
  `_coding/PREDICTION.md` stop rule). Is the reproduction
  actually testing what you think? Is the code you are reading the code that runs?
  Is it the right process, the right build, the right environment?

## The cause is proved when

You can state, in one sentence, how this input produces that output through this
code — and you can make the failure appear and disappear at will by toggling
that one mechanism. Anything less is a correlation.
