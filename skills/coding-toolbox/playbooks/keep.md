<!-- coding:guidance -->
# Keep — turning a script from one run into a tool for the next

A script written mid-task works for one agent, in one session, against one
state of the machine. Keeping it means removing each of those three, and then
proving the result from the place the next agent will run it.

## The gate

A script is kept only when every row holds. One that fails a row is named in the
report and let go; a toolbox is not an archive.

| Question | Kept when | Otherwise |
|---|---|---|
| Was it costly to derive? | It encodes something that was discovered: a flag, a port, an order of steps, where the logs land | A one-liner any agent would write in a minute is cheaper to rewrite than to find |
| Will it be derived again? | The job recurs: every reproduction, every local start, every release | Useful to this change only: it dies with the change |
| Does the index already hold it? | No tool does this job | Fix the existing tool. A second one is how neither gets maintained |
| Does it run from a clean checkout? | It needs only what the repo's own setup provides, or the header says what else | It leans on this session's scratch files, shell state or an open process |
| Is anything pinned? | Every path, port, commit, account and date is an argument or read from the environment | Make it an argument first. A pinned value passes today and fails silently later |
| Is anything secret? | Credentials come from the environment and the header names the variable | Never kept as written |
| Is there room? | The toolbox is under its cap | Merge or delete one first |

## The header

Six lines in a comment near the top of the file, in the comment syntax of its
language. `toolbox.py` reads them and builds the index from them.

```sh
# Purpose: <what it does, in the words a request would use>
# Use when: <the situation that should send an agent here>
# Run: <the exact invocation, from the repo root, with its arguments>
# Proves: <what a good run shows — a line printed, an exit code, a file written>
# Side effects: <read-only, scratch or mutates> — <what it writes or changes>
# Verified: <date> by running <what was run, against what>
```

| Line | What makes it wrong |
|---|---|
| `Purpose` | It describes the implementation. The reader is choosing, not reviewing |
| `Use when` | It restates the purpose. This is the line an agent matches its situation against |
| `Run` | It needs editing before it works. An agent mid-task will paste it |
| `Proves` | It says "works". It is the prediction for every later run, so it names an observable |
| `Side effects` | It says read-only for a script that writes anywhere. `scratch` is a directory the tool creates and removes itself; anything else is `mutates` |
| `Verified` | It was written before the run. The date is when someone looked, and the rest says at what |

## The steps

1. Pass the gate, row by row. Stop at the first row that fails
2. Generalise: every pinned value becomes an argument with no default that
   only works here. A missing argument fails loudly with the usage line
3. Move it to `.agents/toolbox/tools/<name>`, named for the job in the words
   of `Use when`, and make it executable
4. Write the header, `Verified` last and still empty
5. Predict, then run it from there as its `Run` line says, in a state as
   close to a clean checkout as this run can reach. The prediction is the
   `Proves` line. A miss is a fix to the tool or to the line, never to both at
   once, or nothing was tested
6. Fill `Verified`, then run `toolbox.py index` and `toolbox.py check`
7. First keep in this project: with the human's go-ahead, add the pointer to
   the host's agent instructions, one line saying to read
   `.agents/toolbox/INDEX.md` before writing a script, and to keep what would be
   derived again. Refused or not writable: it goes in `open`, because a toolbox
   nothing points at is read by nobody

## What it leaves behind

The tool, the regenerated index, and in the report the scripts this run wrote
and did not keep, each with the gate row it failed. The handoff's `evidence`
keys the tool file with the command that was run and what it showed.

Adapted from pstack (cursor/plugins): `create-verification-skill`'s helpers rule
and its proof before handing over, and the tooling lens of `reflect`.
