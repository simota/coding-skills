<!-- coding:guidance -->
# When a finding needs a picture

A finding a reader has to reassemble in their head is a finding that gets
skimmed, and a skimmed report did not happen. A diagram is not decoration here
— it is the finding, in the form that costs the reader least.

It is also not free. A picture that restates a sentence costs the reader twice:
once to read the sentence, once to check the picture says the same thing.

## The four triggers

A diagram is owed when **any one** of these holds. None of them is "it would
look nice".

| Trigger | Holds when | Because |
|---|---|---|
| `hops` | The finding spans three or more places the reader must hold at once | Prose makes them remember; a picture makes them look |
| `ordering` | It depends on sequence — the same parts in another order would be fine | "Then... then... then" in the prose is the tell |
| `disagreement` | Two things state different values and both must be shown to see it | Two paragraphs make the reader diff them by eye |
| `location` | It is somewhere in a two-dimensional artifact — a region, a crop, a layout | Words for a position are longer and less exact than a mark |

In this family `hops` fires most: a defect is rarely at one line, it is at the
third step of a path, and the reader has to hold the first two to see it.
`location` fires least — code is not two-dimensional — except where the finding
is a position in a structure that is not linear, such as a case matrix or a
lock held across methods.

## When not to

- One place, one line, one sentence. Say it
- The picture would contain exactly what the sentence contains
- Nothing was traced. A diagram of an untraced path is speculation with better
  graphics, and the finding is not at its floor either
- The diagram would need the whole artifact to make sense. Bound it or drop it

## Which form

**ASCII by default.** It survives a terminal, a plain-text report, a commit
message and a diff, and it cannot fail to render. Every trigger above has an
ASCII form in [diagram-forms](../reference/diagram-forms.md).

**Mermaid when the shape is genuinely a graph** — more than about six nodes, or
branching and merging that ASCII would misalign. It needs a renderer, so it is a
trade, not an upgrade.

**Never both for one finding.** Two pictures of one thing is the reader
checking them against each other.

## The floor

A diagram carries the same rung as the finding it belongs to — its certainty
label from the severity playbook (Confirmed / Likely / Question) and its
evidence grade. It never raises either, and three things keep it a finding rather than an illustration:

- **`labelled`** — every mark names something that was opened. A region, a file,
  a step that exists. An unlabelled box is a guess that looks like a fact
- **`derived`** — it says nothing the evidence did not establish. It adds no hop
  nobody traced and no cause nobody checked
- **`bounded`** — it shows the parts the finding is about and stops. A diagram
  of the whole thing is a second thing to read

**The test:** could a reader who disagrees point at the part of the diagram that
is wrong, and check it? If not, it is not carrying a finding.

## Where it goes

Inside the finding, under the row it belongs to — not in a gallery at the end.
A picture separated from its claim is a puzzle.

One finding, one diagram. Where several findings share a location, one map with
numbered marks and the findings referring to the numbers beats one map each.

## In this family

- **A call chain** for anything with `hops` — each node a `file:line` that was
  opened, the defect hung off the step it is at. The default here
- **Two lanes** when the finding is a race or an ordering hazard: two callers,
  time to the right, and the mark where the interleaving goes wrong
- **Two columns** for a wrong value — what the code computes against what the
  caller, the schema, or the test expects
- **A blast-radius fan** when the finding is that a changed signature reaches
  further than the diff: the changed thing on the left, its callers to the
  right, and the ones the diff did not touch marked
- **A case grid** when a conditional is missing a branch: the inputs down one
  axis, the states across the other, and the empty cell as the finding
