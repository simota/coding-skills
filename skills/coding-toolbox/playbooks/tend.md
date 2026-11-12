<!-- coding:guidance -->
# Tend — keeping a toolbox worth reading

A tool rots the moment the app it drives changes, and a toolbox with one tool
that lies teaches every reader to distrust the rest. The unit of a tend is the
tool: each one is run, and each one leaves fixed, merged, deleted or confirmed.

## How it ends

Say which of the three, in the first line of the report.

| Ending | Means | Leaves |
|---|---|---|
| Nothing to change | Every tool was run and did what its header says | No edit. The coverage is the result |
| Corrections | One or more tools or headers were wrong and are now proved right | The edits, each with the run that proves it |
| Stopped | Coverage could not finish, or a fix could not be proved | What stopped it, and which tools were not reached |

## Edit scope

Only `.agents/toolbox/`. A tool that fails because the app changed its flags, its
port or its output is drift: fix the tool. A tool that fails because the app is
broken has found a defect: report it with the tool's output and leave both alone.
Rewriting a tool until it passes against a broken app deletes the evidence.

## The pass

1. **Check the index** — run `toolbox.py check` and fix what it names. This is
   the cheap half; it says nothing about whether any tool works
2. **Sort by side effect.** `read-only` and `scratch` tools are run without
   asking. `mutates` tools are listed to the human with what each changes, and
   run only on a go-ahead for this pass
3. **Run each tool as its `Run` line says**, with `Proves` as the prediction.
   One tool, one run, one grade. A tool whose prerequisite is absent — a
   service, a credential, another platform — is not failed: it is unreached,
   with the prerequisite named. A header that omits that prerequisite is drift
4. **Triage each miss**

   | What was seen | It is | Do |
   |---|---|---|
   | The tool errors on something the app renamed or moved | Drift in the tool | Fix it, run it again, refresh `Verified` |
   | The tool runs and `Proves` describes something else | Drift in the header | Correct the line to what a good run shows, then confirm against a known-good state |
   | The app misbehaves and the tool reports it faithfully | A defect in the product | Report it. The tool is working |
   | Nothing in the repo's recent history would have reached for it | Dead weight | Delete it. Git keeps it for whoever wants it back |
   | Two tools do one job | A fork | Keep the one with the better header, fold in what the other knew, delete the other |

5. **Look for what is missing** — only from evidence: a script in the recent
   history of the repo that was written twice, or an instruction in the host's
   agent files that a tool would replace. A guess at what might be useful is not
   a reason to add one
6. **Regenerate and check** — `toolbox.py index`, then `toolbox.py check`
7. **Confirm the pointer** — the host's agent instructions still tell a reader to
   open the index. Missing and not writable in this run: it goes in `open`

## Three things that hold for the whole pass

- **Nothing a tool started outlives the run.** Stop what was started, by the
  handle it returned and never by process name
- **A tool that surprised you is not run again blind.** Read it before the
  second attempt; two misses on one tool mean the model of it is wrong
- **Output captured as evidence survives cleanup**, at a path the report names

## What it leaves behind

The coverage — tools run, tools unreached and why, tools deleted and why — and
`Verified` refreshed on exactly the tools that were run in this pass. A date
moved forward on a tool nobody ran is the one edit a tend must never make.

Adapted from pstack (cursor/plugins): `maintain-verification-skill`'s outcomes,
edit scope and triage.
