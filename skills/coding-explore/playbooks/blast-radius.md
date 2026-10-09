<!-- coding:guidance -->
# Blast radius — what a change would touch

Asked before a change, this decides whether the work is a `T0` edit or a
migration. Asked after, it is an incident review. The estimate is only useful
if it names what it could not see.

## Two directions, both required

**Vertical — who depends on this?** Callers, subclasses, importers, and
everything downstream of them. Depth matters: a change to a leaf helper with
forty callers is wider than a change to an entry point with one.

**Horizontal — what else looks like this?** The same pattern copied elsewhere.
A fix applied to one of three copies leaves two live bugs and creates a
divergence nobody documents. Search for the shape, not the name.

## Radius by what is changing

| Changing | Reaches |
|---|---|
| A function body, same signature | Its callers' behaviour, and any test asserting the old output |
| A signature | Every caller, every mock or stub of it, every subclass overriding it |
| A public/exported interface | Everything above, plus consumers outside this repo you cannot grep |
| A database column | Readers, writers, migrations, backups, analytics queries, and anything reading the DB directly |
| A serialised format or API response | Every deployed client, including versions still running that you do not control |
| A config default | Every environment that did not override it — and the ones that overrode it to the old default on purpose |
| A shared constant or enum | Everywhere it is compared, persisted, or serialised. Persisted enums outlive their code |
| A dependency version | Its transitive tree, its peer constraints, and any code relying on a bug it fixed |
| A file's location | Imports, build config, CI paths, docs, and anything constructing the path as a string |

## The layers grep cannot reach

Name each one that applies in the report's coverage boundary, not a footnote.
The run is `PARTIAL` when the question cannot be answered without one of them.

- **Persisted data** already written in the old shape. Code changes forwards;
  rows do not
- **In-flight work** — queued jobs, retries, and cached values holding the old
  format
- **Other repos and deployed clients** — mobile apps in particular, where the
  old version runs for months
- **Runtime wiring** — reflection, config strings, DI, generated code
- **Humans** — a runbook, dashboard, or alert built on the old behaviour

## Producing the estimate

1. Confirm the change's exact surface: which symbols, files, and formats
2. Vertical sweep — enumerate callers, read each to confirm it is real
3. Horizontal sweep — find the copies of the pattern
4. Walk the invisible-layers list above and mark each present or absent
5. Classify: `contained` (this module only) / `wide` (several modules, one repo)
   / `crosses a boundary` (data, protocol, or another deployable)

**Anything crossing a boundary is not a code change alone.** It needs an order:
write the new path, migrate, then remove the old one. Say so, and let the human
decide, rather than estimating it as a number of files.

## Before reporting

- Both sweeps ran — vertical and horizontal — and the horizontal one is stated
  even when it found nothing
- The count distinguishes confirmed call sites from name matches
- Every invisible layer was considered, and the present ones are listed
- The classification comes with the one thing that would most likely be missed
