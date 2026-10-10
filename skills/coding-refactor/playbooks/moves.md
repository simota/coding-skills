<!-- coding:guidance -->
# Moves — the catalogue, and when each one earns its place

Every move here is behaviour-preserving. Pick the smallest one that removes the
named difficulty, apply it, run the tests, commit. One move per commit.

## Reading the difficulty

| The difficulty | The move |
|---|---|
| A function is edited on every unrelated feature | Split by reason-to-change, not by line count |
| You must read the body to know what it does | Extract and name the parts, or fix the name |
| A comment explains what the next block does | Extract that block, and the comment becomes the name |
| The same fix has to be applied in several places | Deduplicate — but only once you have confirmed they are the same thing |
| A magic value appears in more than one place | Name it once, at the level where it is meaningful |
| Nested conditionals past three levels | Guard clauses, early return, or invert the condition |
| A boolean parameter switches the whole body | Two functions with honest names |
| A long parameter list, always passed together | Group them into a type that has a name |
| The call site reads wrong | The name is wrong. Fix the name, not the call site |
| Code lives where it does not belong | Move it to the module that owns the concept |
| You cannot tell whether a branch is reachable | Prove it, then delete it or make it obvious |

## Duplication needs a judgement first

Three similar blocks may be one thing repeated or three things that currently
coincide. Ask what makes them change:

- **They change together, for the same reason** → the same thing. Deduplicate
- **They would change separately** → coincidence. Leave them apart

**A wrong abstraction costs more than duplication**, because every future case
now bends around it and each bend adds a parameter. Duplication is visible and
cheap to fix; the wrong abstraction is invisible and expensive to undo. When
unsure, wait for the third real case.

## Deleting

The highest-value move and the one most often skipped.

1. Grep the symbol across the whole repo, including tests, config, docs, and
   generated files
2. Check what grep cannot see: reflection, string-keyed registries, config
   naming a class, DI, re-exports, framework conventions, other repos
3. Check the history — was it added for something not yet launched?
4. Delete it. **Do not comment it out**: version control already remembers, and
   commented code is read as intentional by the next person

Dead code is not just unused functions. Also: flags whose branch is never taken,
config nobody reads, dependencies nobody imports, tests asserting nothing, and
compatibility shims for versions no longer running.

## Renaming

- The name states **what**, not how, and matches the codebase's word for the concept
- Units and nullability belong in the name where the type does not carry them
- A rename crossing a public boundary is not a refactor — it breaks callers you
  cannot see, and needs the add-migrate-remove sequence
- **A name that is also data is not renamed by a refactor** — a class or field
  name written into pickles, JSON, an ORM column, a stored enum name, a message
  schema, or a reflection or config string. Check whether it is persisted or
  serialised first; if it is, the rename is a migration — sequenced per
  `coding-plan` (data and deployed clients), built by `coding-implement`. The same holds for reordering enum members whose ordinal is stored
- Rename with the tool, not by hand. A regex rename catches a substring in an
  unrelated identifier, and the resulting bug looks nothing like a rename

## Sequencing a larger restructuring

1. Add the new structure alongside the old one; nothing uses it
2. Move one caller. Run the tests. Commit
3. Repeat until no caller uses the old structure
4. Delete the old structure

Each step is green, each is revertible, and the work can be abandoned at any
point without leaving the codebase worse. A big-bang restructuring has neither
property, and it is only ever one merge conflict from being thrown away.

## Before committing a move

- Tests were green before and are green now, with the same cases and assertions
- The diff contains exactly one kind of move
- Something is smaller: fewer lines, fewer branches, fewer call sites, fewer concepts
- No behaviour changed — including error messages, ordering, and exception types
