<!-- coding:guidance -->
# Views — drawing all of a plan

A plan read as prose is checked one sentence at a time, and each sentence is
fine. The flaws live between sentences: a step nobody owns, a value that
changes unit between two paragraphs, a failure with no way back. A drawing puts
the sentences side by side, and no single drawing is enough — each view hides
what another shows.

## The views

Every row that matches is owed, not the first. A view that is not owed is named
in one line with the reason — "Sequence: not owed, one actor" — so the reader
can see it was considered, not forgotten.

| View | Owed when | It shows |
|---|---|---|
| Usage | The plan adds or changes something others call | The call as the caller writes it, before any type |
| Structure | Two or more modules are touched | What depends on what, which way, and what is new |
| Data flow | A value crosses a boundary | Where each value is born, changed, stored and read; its unit and its one writer |
| Sequence | Two or more actors, or the order matters | Who calls whom in time, and where it can be interrupted |
| States | Something has a lifecycle | Each state the reader would name, and what moves between them |
| Failure | Any step can fail — nearly always | Per step: how it fails, who notices, what is left behind, the way back |
| Data lifetime | Persisted data or a public format is touched | Old rows, new rows, the window where both exist, rollback |
| Trust boundary | A rule says who may act, or input arrives from outside | Each crossing, what is checked there, and against what |
| Operations | It ships somewhere it can fail | Rollout, the signal a person sees for each failure, the switch, the rollback |
| Load | A loop, a queue, or a limit somebody else owns | Each quantity with its number and the number's source |
| Build order | The plan has more than one step | What each step needs, and what can be run once it is done |
| Proof | There are rules — always | Per rule, the check the plan names and the step it can run after |
| Network | Traffic crosses a zone, or a host, port or route is added | Where each part runs, each link's direction and protocol, what may reach what |
| Screen design | A person sees or presses something new | Each screen as a wireframe, in every state it can be in, its parts numbered |
| Screen spec | A screen has an input or an action | Per numbered part: where its value comes from, what it rejects, what a press does |
| Screen flow | Two or more screens, or a dialog | Every screen, what moves between them, and the path after something goes wrong |
| Tables | A table or a column is added or changed | Per column: type, null, key, and the constraint that holds a rule |
| ER | Two or more tables relate | Each relation, with how many on each end |

## Drawing rules

- **From the plan's words, not from yours.** Each mark carries its source in the
  legend: the plan's line, or the `file:line` opened for a thing that exists
- **Existing and new look different.** `[new]` on what the plan builds. A box
  with neither a source nor `[new]` is a guess that looks like a fact
- **A gap is `?`, never a guess.** Where the plan does not say, the drawing says
  `?`. Count them when the views are done — each is already a finding
- **One name per thing, one number per step, in every view.** Step ③ in the
  sequence is step ③ in the failure grid and the build order. Without that the
  seams between views cannot be checked
- **The reader's words on the drawing**, identifiers in the legend under it
- **The sheet draws them; ASCII quotes them.** The page a person reads follows
  [sheet](sheet.md). A view quoted in a terminal, a handoff or a commit message
  takes the ASCII form below, under about 70 columns, aligned by spaces
- **About 20 arrows a view.** First merge what acts the same; a plan still too
  large to draw is two plans, and the report says where the seam is

## Forms

The ASCII form of the views a report most often quotes. Marks are circled
numbers, and the flaw hangs off its mark. The sheet's template shows all of them.

**Usage** — the call site first, as the laziest caller would write it.

```
refund = payments.refund(order_id)        [new]
if refund.pending: show("Refund on its way")
        ▲ ? — the plan never says what a second call returns
```

**Structure** — arrows point at what is depended on.

```
checkout ──▶ payments ──▶ gateway client
    │            │
    │            └──▶ refunds [new] ──▶ ledger
    └──▶ ledger          ▲ ① two writers of one balance
```

**Data flow** — the value on the arrow, with its unit.

```
form ──amount: text──▶ parse ──cents: int──▶ refunds [new] ──?──▶ ledger
                                                           ▲ ① unit not stated
```

**Sequence** — one lane per actor, time to the right.

```
you      press refund ─────────────────────── press again ──┐
server        ① reserve ── ② call gateway ─────────────┐    │
gateway                          └── pays ─────────────┘    ▼
                                    ▲ ② still in flight: a second reserve
```

**States** — states and arrows in the reader's words, the breaking state marked.

```
Paid ──you ask for a refund──▶ Refund pending ──gateway pays──▶ Refunded
                                    │
                                    └──gateway times out──▶ ? — no way out drawn
```

**Failure grid** — one row per numbered step; an empty cell is a finding.

```
step                 fails how    noticed by    left behind      way back
① reserve refund     db down      caller        nothing          retry
② call gateway       timeout      ?             reserved row     ?
③ write ledger       conflict     job log       money sent       ——
```

**Data lifetime** — code above, data below, time to the right.

```
code   old ────────────┬── new ───────────┬── rollback to old
data   rows v1 ────────┴── v1 and v2 ─────┴── ? — v2 rows read by old code
```

**Build order** — what each step leans on, and the check that runs after it.

```
① ledger column ──▶ ② refunds module ──▶ ④ checkout button
                          │
                          └──▶ ③ gateway call
check:  ① migration both ways   ② unit   ③ ? — needs ④ to run   ④ end to end
```

## Before attacking

- Every owed view is on the sheet, and every view not owed has its line
- Every mark has a source or `[new]`, and every gap is a `?`
- The same step carries the same number everywhere it appears
