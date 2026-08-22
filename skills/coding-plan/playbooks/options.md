<!-- coding:guidance -->
# Options — choosing between viable approaches

The job is a decision, not a menu. A list of three approaches with no
recommendation returns the work to the person who asked.

## Generating candidates worth comparing

Two options are usually one option and a strawman. Force real difference by
generating along axes that actually conflict:

- **The smallest thing that could work** — often uglier and often correct
- **The shape the codebase already uses** — cheapest to review, cheapest to own
- **The one that removes something** — can this be solved by deleting a feature,
  a branch, or a dependency instead of adding one?
- **The one that buys the option** — a thin seam now so the expensive decision
  can be made later with more information
- **Do nothing yet** — always on the list. Sometimes it wins, and naming it stops
  the plan from being motivated by momentum

Drop any candidate you would never recommend. Carrying a strawman to make the
recommendation look inevitable is dishonest reasoning dressed as rigour.

## Pricing them

Compare on the axes that decide this case, not on generic ones. Useful axes:

| Axis | Why it decides |
|---|---|
| Files and modules touched | Review cost and merge-conflict risk, right now |
| Reversibility | What it costs to undo after it ships. This dominates when uncertainty is high |
| What it forecloses | The approach you cannot take afterwards. Rarely visible, usually the real cost |
| Who must know about it | An approach only its author understands has a single point of failure |
| Failure mode | Loud and early beats quiet and late, even at a higher probability |
| Ongoing cost | Every new dependency, config option, or environment is a permanent tax |
| Time to first working path | High when someone is blocked on this today |

**Do not score with numbers you invented.** A weighted matrix built from made-up
weights launders a preference into arithmetic. State the trade-off in words and
own the recommendation.

## Making the call

1. Name the one axis that dominates *this* decision, and say why it dominates
2. Recommend the option that wins on it
3. State what the recommendation costs — every choice costs something, and a
   recommendation with no stated cost has not been examined
4. State the condition under which you would switch. This is what makes the
   decision revisable instead of permanent

## Recording it

Short, and where the next reader will be standing:

```
Decision: <what was chosen>
Because: <the dominating axis, in one sentence>
Rejected: <option> — <the one reason>
Costs: <what this choice makes harder>
Revisit if: <the observable condition>
```

`Revisit if` is the load-bearing line. Without it the decision is permanent by
default, and nobody remembers it was ever a choice.

## Traps

- **Deciding on the axis that is easiest to measure** rather than the one that
  matters. Lines of code is measurable; reversibility is what will hurt
- **Comparing an approach you understand against one you do not.** The unfamiliar
  option always looks riskier. Read enough to price it honestly, or say you did not
- **Letting the sunk plan decide.** Work already done on an approach is not a
  reason to continue it
- **Reopening a decision the human already made.** Their call is an input, not a
  candidate — unless a fact has changed, and then say which fact
