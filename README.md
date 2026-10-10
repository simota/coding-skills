# coding-skills

Eight agent skills covering the coding lifecycle, the contracts they share, and
the budgets that keep the set from growing into something nobody can route
through. Each skill owns one phase and returns evidence rather than assurances.

## The skills

| Skill | Owns | Writes code? |
|---|---|---|
| [`coding-explore`](skills/coding-explore/SKILL.md) | Where things are, how a path works, what a change would touch | No |
| [`coding-plan`](skills/coding-plan/SKILL.md) | The shape before code exists: interfaces, data model, build order | No |
| [`coding-implement`](skills/coding-implement/SKILL.md) | Producing working code | Yes |
| [`coding-debug`](skills/coding-debug/SKILL.md) | Reproducing, proving a cause, fixing minimally | Yes |
| [`coding-refactor`](skills/coding-refactor/SKILL.md) | Structure changed, behaviour identical | Yes |
| [`coding-test`](skills/coding-test/SKILL.md) | The checks that catch defects; flaky repair | Yes |
| [`coding-review`](skills/coding-review/SKILL.md) | Defects in a change, before it lands | No |
| [`coding-ship`](skills/coding-ship/SKILL.md) | Commits, history shape, PR, release notes | History and release docs only |

## The idea the set is built on

**The prediction is the only part of a run that cannot be revised in hindsight.**
Every observed output has a story that accommodates it, so an explanation
written after the output is evidence that language is flexible, not that the
code was understood. So a skill that causes an observable change registers one
line before it runs — what will be run, and what observable result changes —
and reports `hit`, `miss`, or `void` after. **A `miss` costs nothing; an
unrecorded `miss` costs the run.** Two consecutive misses in one area mean the
model of that area is wrong, and the next move is reading, not another edit.

The completion contract grades a claim after the fact; this one fixes what the
claim was before it. `executed` with nothing registered beforehand still
supports *it ran and produced that output* — never *it works because X*
([`_coding/PREDICTION.md`](skills/_coding/PREDICTION.md)).

## How it is put together

A skill is loaded in three stages, and each stage costs something different.
The **listing** carries `name` and `description` only, for every enabled skill,
on every turn. **`SKILL.md`** is read in full once a skill is chosen. Anything
it points at is read only if the situation calls for it. Four consequences
shape everything below.

**Selection happens on the description alone.** Nothing else is in front of the
engine at that moment — not the registry, not the boundaries, not the body. So
every word that selects a skill is required to appear literally in its
description, and `coding-registry/capabilities.yaml` lists those words per skill.
A rule checks the two agree: a signal that lives only in the registry never
reaches anything.

**Boundaries live in one file.** `coding-registry/capabilities.yaml` carries `not:` —
what a skill does not do and where that work goes instead. Descriptions never
name a neighbour. If they did, adding a ninth skill would mean editing the
other eight, and a description would spend its 200-character listing budget
advertising a competitor.

**Contracts are delivered, not referenced.** A rule kept in `skills/_coding/` is read
on a minority of launches, so the operative part of each contract is copied
verbatim into each `SKILL.md` that owes it, between `<!-- deliver:… -->` markers.
`coding-registry/delivered/` holds the source, `make render` writes it back, and a
rule fails if any copy has drifted. The longer prose stays in `skills/_coding/`.

**Budgets are enforced, not intended.** `coding-registry/harness.yaml` holds every
threshold — line counts, skill count, description length. `coding-tools/validate.py`
decides them and CI fails on a violation. Nothing is exempt for being
important, because a gate that a person can argue past is a gate the person
who wants to grow the set will argue past.

## Three rules that follow from it

**Evidence has grades.** `executed` (it was run) supports completion.
`inspected` (it was read back) does so only where nothing could be run and the
entry says why. `asserted` never does. The unit is the file written to: each one
carries a grade or appears in the residuals as `UNVERIFIED`.

**Ceremony is sized, not chosen.** A one-line reversible fix gets a one-line
report. Anything larger settles a brief first, with a non-empty `excludes`. Both
over- and under-ceremony come from picking the tier for comfort, so the tier is
read on first match.

**Residuals are visible or they do not exist.** Anything left behind is
`BLOCKED` / `OUT-OF-SCOPE` / `DEFERRED` / `UNVERIFIED` and appears in the
handoff's `open` list. A run that may write the file also drops a
`#TODO(agent):` marker in the tree; one that may not names where it belongs
and leaves the writing to its receiver. The report closes and is gone; the
marker stays.

## Files

**Shared pages.** Every file states its kind on its first line:
`<!-- coding:contract -->` binds on every run, `<!-- coding:guidance -->` is
consulted, and `<!-- coding:deferred -->` (the `reference/` pages) is read only
when a row points at it.

| File | What it fixes |
|---|---|
| [`skills/_coding/CONTRACT.md`](skills/_coding/CONTRACT.md) | Evidence grades, status, residual classes, the completion sweep |
| [`skills/_coding/PREDICTION.md`](skills/_coding/PREDICTION.md) | The one line registered before a run; `hit` / `miss` / `void`; the stop rule |
| [`skills/_coding/SIZING.md`](skills/_coding/SIZING.md) | How much ceremony a request is worth; when a dialogue is mandatory; the brief |
| [`skills/_coding/HANDOFF.md`](skills/_coding/HANDOFF.md) | What passes between skills, and the seven checks the receiver runs |
| [`skills/_coding/VALUES.md`](skills/_coding/VALUES.md) | The order that decides when two goods conflict, and the escape hatch |
| [`skills/_coding/ROUTING.md`](skills/_coding/ROUTING.md) | **Guidance, not binding.** Read when the owner is unclear or the work spans several |
| [`skills/_coding/REPORT.md`](skills/_coding/REPORT.md) | What a person reads: the moments a run speaks, the order at the end, proportion by tier, and why the handoff is the record |

**Registry — the machine-readable definitions.**

| File | Holds |
|---|---|
| [`coding-registry/harness.yaml`](coding-registry/harness.yaml) | Every budget and every piece of fixed vocabulary |
| [`coding-registry/capabilities.yaml`](coding-registry/capabilities.yaml) | Per skill: permission class, what it does, `not:`, and its signals |
| [`coding-registry/routes.yaml`](coding-registry/routes.yaml) | The chains that recur, with their control structure |
| [`coding-registry/fixtures.yaml`](coding-registry/fixtures.yaml) | A record of misroutes, grown from accidents |
| [`coding-registry/delivered/`](coding-registry/delivered) | The blocks copied verbatim into each `SKILL.md` that owes them |

## Layout

```
coding-skills/
├── README.md
├── Makefile
├── coding-registry/            # budgets, boundaries, routes, delivered blocks
├── coding-tools/               # validate · test_validate · test_tools · render ·
│                               # figures_check · fences · engine · refute · githooks/
├── docs/                       # the generated overview page (not edited here)
└── skills/                     # everything the CLI reads
    ├── _coding/                # shared contracts, and routing guidance
    └── coding-<phase>/         # a SKILL.md is what makes this a skill, and
        │                       # only skills are installed
        ├── SKILL.md            # Owns / Before starting / Decide first /
        │                       # Always·Never / Verify with / Done when
        ├── _coding   -> ../_coding        # short names: the parent scopes them
        ├── registry  -> ../../coding-registry
        ├── refute.py -> ../../coding-tools/refute.py   # harness `linked_tools`
        ├── playbooks/          # loaded only when a SKILL.md row points at one
        └── reference/          # no line budget, carries dated headers instead
```

**The git behaviour those pages state is re-run, not dated.** `make figures`
builds throwaway repositories and checks every documented behaviour against the
git actually installed — that `-S` misses an equal-count edit, that three-dot
diff isolates a branch's own work, that `restore .` leaves no trace where
`git add` leaves a recoverable blob, that `checkout -f` discards tracked edits
and leaves untracked files. 31 behaviours, about two seconds, in `make check`, CI
and the pre-commit hook. Where a page prints an output, that output is parsed from
the page, so editing the page to say something false fails too — proven by
injecting both kinds of break, including deleting a block so the checker matches
nothing.

**Two knowledge layers, and the split is about budget, not importance.**
`playbooks/` holds judgement that has to stay short enough to be read in full.
`reference/` holds what the model approximates rather than recalls — exact
command semantics, what a destructive operation can and cannot undo, where a
test's expected value may legitimately come from. It has no line budget and is
read only when a row points at it, so it states its purpose, when to read it,
and when it was last checked against the tool.

| Reference | Answers |
|---|---|
| [`coding-explore/reference/history.md`](skills/coding-explore/reference/history.md) | `-S` vs `-G`, the `..`/`...` inversion between `log` and `diff`, blame that stops lying, finding deleted code |
| [`coding-review/reference/diff-scoping.md`](skills/coding-review/reference/diff-scoping.md) | Getting the whole change set, and the commands that silently return a subset |
| [`coding-review/reference/diagram-forms.md`](skills/coding-review/reference/diagram-forms.md) | The copy-paste ASCII form for each finding a reader would otherwise reassemble |
| [`coding-review/reference/machine-authored.md`](skills/coding-review/reference/machine-authored.md) | The ten defect classes that concentrate in generated code, each with a runnable check |
| [`coding-ship/reference/recovery.md`](skills/coding-ship/reference/recovery.md) | What git can undo, what nothing can, and the one command that makes the difference |
| [`coding-test/reference/oracles.md`](skills/coding-test/reference/oracles.md) | Where an expected value may come from, and the shapes that assert nothing |

## Names, and why none of them are generic

A skills directory is flat and shared with every other set installed on the
machine. A generic name placed there is a silent collision, and it is not
hypothetical: `_common` in that directory already belongs to an unrelated set,
and a sibling set's install line is `cp -R quality-* _common <skills dir>` —
which today writes into the other set's repository.

**One declaration.** `set: coding` in `coding-registry/harness.yaml` is the one
declaration every other spelling of the name is checked against. The skill prefix
(`coding-`), the shared directory (`skills/_coding/`), and the label every
document carries (`<!-- coding:contract -->`) all derive from it, and a rule
fails if they stop agreeing.

**Every directory this set owns carries the set name** — `coding-*` or
`_coding`, with only the directories in `platform_dirs` (`.git`, `.github`,
`.claude`, `skills`, `docs`) exempt. A rule enforces it.

The weaker rule is tempting: prefix only what gets installed, and leave
`registry/` and `tools/` generic since they never leave the repo. It fails on
its premise. "Never leaves the repo" is a claim about every future install
script, every copy command, and every consolidation of these sets into one
tree — and the sibling set's `cp -R … _common` line is exactly what that claim
looks like once it is wrong. A name that cannot collide beats a name that is
not supposed to.

**Being prefixed is not what makes something installable.** `coding-registry/`
and `coding-tools/` share the prefix and are never installed; a skill is a
directory holding a `SKILL.md`, and that is what `make link` links.

**Everything a skill reads lives inside the skill.** The contracts and the
registry are reached through symlinks in each skill directory — named `_coding`
and `registry`, kept short because the parent already scopes them. This is not
a convenience: a skill is handed its own directory as the base for relative
paths, and those paths are normalised *lexically*, so `../_coding/X.md` does
not travel back through the install symlink. A shell follows the link and finds
the file, which is what makes this fail quietly rather than loudly. A rule
rejects any backticked path containing `..` and any link that climbs out of the
skill directory, and checks that every path named in a `SKILL.md`, a playbook,
**or a shared contract** resolves from a skill directory. Extending that check
past `SKILL.md` found two live breaks: a contract pointing at
`registry/capabilities.yaml` from the wrong base, and a playbook pointing into
another skill's playbook — which should name the skill, not reach into it.

## Working on it

```sh
make check      # what CI runs: the rules, proof they still fire, the tool tests,
                # the git figures, and that every delivered block is current
make render     # after editing anything in coding-registry/delivered/
make hooks      # run the rules on every commit
```

Adding a rule means adding a deliberate violation to `coding-tools/test_validate.py`
and watching it fail. A check only ever seen passing may be checking nothing —
building that test found one rule that could not fail at all.

Nearing a playbook cap is not a reason to split a skill. Merge the duplicates,
delete what nothing reads, compress it into a `Decide first` row, move it to the
skill it belongs to — and only then consider splitting, which is accepted only
when the two halves have disjoint signals and neither is left with only a
playbook or two. Splitting to relieve a budget is how a set of eight becomes a set nobody
can route through.

## Installing

```sh
make link                       # into every installed host: claude, codex, agy
make link CLAUDE_DIR=.claude/skills
```

Each `coding-*` directory is linked individually, so a skills directory keeps
whatever else it already carries, and a name already taken by a real directory
is skipped rather than overwritten.

## What this does not guarantee

- **`allowed-tools` is one CLI's mechanism.** Where a tool grant is not
  enforced, the `Never` lines are discipline and nothing more. `Bash` is granted
  to every skill, so a determined misuse is always reachable
- **Read-only is not "sends nothing".** The permission class governs local
  writes. Anything leaving the machine is a separate question and needs asking
- **The fixtures do not model how a model chooses.** They catch a missing or
  duplicated signal. Passing them is not evidence that nothing will be misrouted
- **No rule here measures whether the right skill was picked.** That needs usage
  data this repo does not collect yet
- **Eight skills need no pack machinery.** Selection degrades as a listing
  grows; at this size the whole set is the working set. `packs_needed_above` in
  `coding-registry/harness.yaml` names the point where that stops being true

## The published overview

[`docs/index.html`](docs/index.html) is a generated page — every figure on it is
read off this repository, the way `make figures` recomputes what the reference
layer states. **Do not edit it by hand**: `tools/pages.py` in the `agent-toolkit`
repository writes it, `tools/pages.py --check` fails when it is behind, and
`.github/workflows/pages.yml` here only publishes what is committed.

