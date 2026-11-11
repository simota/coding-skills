<!-- coding:guidance -->
# Sheet — the drawn plan as one page

The sheet is what the person deciding reads. A flaw list they have to hold
against a plan in another window gets skimmed; a page where the flaw is a red
flag on the drawing of the plan gets argued with, which is the point. They
should be able to put a finger on the mark that is wrong.

## Build it

- **Read [the template](../sheet.html) first.** It is a worked example on an
  invented plan: the style block, the marks, and every view drawn once
- **Write a new file beside the plan** with that style block and those marks,
  and this plan's content. The template is never edited, and none of its
  example content survives — search the result for the template's plan name
- **One file that opens from disk.** No script, no image file, nothing fetched —
  opening a sheet sends nothing anywhere. A sheet that needs a server is not read
- **Both themes.** Every colour is a token from the top of the style block. A
  literal colour in a drawing is unreadable in one theme or the other

## Order

Title block — the plan, the revision read, run status, the loop's cycle when
in one, who is next, the verdict. The index of views, each dotted by its worst
mark: red for a flaw of rank 1–3 or a breaking cell, amber for a lower flaw or
a `?`, green when clean, no dot when not owed. What stops the build, then
counts. The legend. The premise. The rules, with the rule-by-view matrix (a
dash under a view not owed). Then the views, numbered in the views table's
order; a view not owed keeps its number and its one line. Then every seam the
hunt lists, the flaw register, and what the sheet covers.

## The marks

| Mark | Means | Never |
|---|---|---|
| Plain box | Exists today; its `file:line` is in the sources under the drawing | A box nobody opened |
| Green box, tagged new | Built by this plan | Something that exists and is changed — say changed in the label |
| Dashed amber, `?` | The plan does not say | A guess in its place |
| Red box or arrow | On the path to a broken rule | Emphasis |
| Dotted box | Outside this team's control | — |
| Round balloon | A plan step; the same number in every view | A second numbering |
| Square tag | A part of a screen; the same number in the screen spec | A step |
| Red flag | A flaw; it links to its card in the register | A flaw with no card |

Colour means these things and nothing else. A reader learns the legend once.
Red wins: a box on a breaking path is red, and its label keeps the `?` or new.

## Drawing

- **Place boxes on a grid** — fixed columns and rows — and draw each arrow
  straight or with one elbow. No arrow through a box, no label on top of one
- **Graphs are inline drawings; grids and matrices are tables.** A table drawn
  as a picture cannot be searched or copied
- **Under each drawing**: the flaws whose marks are on it, one sentence each,
  then the sources. A picture separated from its claim is a puzzle
- **A wide drawing scrolls in its own frame.** The page never scrolls sideways

## Counts are computed

Flaws by rank, gaps, views drawn, rules checked, and any number in a sentence:
count them from the finished page, then write the number. A gap is one amber
`?` on a view; the matrix repeats them and is not counted. A headline that
disagrees with its own page is the first thing a reader stops trusting.

## Verdict is not status

The run's status says whether the preflight finished. The verdict says whether
the plan may be built: not cleared while a flaw of rank 1–3 stands, cleared
when none does — with the lower ranks listed for the human to accept or not.
A finished preflight of a broken plan is `DONE`, and not cleared.

## Before handing over

- Every flag links to a card, and every card names the views it is seen in
- Every count on the page was counted from the page
- It was opened and looked at in both themes — or the report says it was not,
  and the file's grade is `inspected`
