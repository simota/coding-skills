- **Register the prediction before the run.** Before the edit: what will be
  run, and what observable result changes — a named test, an exit code, a value
  at a path. After it, report `hit`, `miss`, or `void` (it turned out
  unobservable). **A `miss` costs nothing; an unrecorded `miss` costs the run.**
  Two consecutive misses in one area mean the model of it is wrong: stop editing
  and read. `executed` with nothing registered supports "it ran", never "it
  works because X" (`_coding/PREDICTION.md`)
