# Contributing and Reproducibility Rules

## Workflow

1. Make a focused change in one workstream.
2. Add or update tests before relying on the change.
3. Run `python -m pytest -q` and any specific notebook/static checks available.
4. Update the relevant `.md` file in the same change. Update `CHANGELOG.md` for meaningful changes.
5. Review `git diff --check`, `git diff --stat`, and `git status`.
6. Commit with a clear imperative message that describes one coherent change.

## Commit messages

Prefer conventional prefixes such as `feat:`, `fix:`, `test:`, `docs:`, `chore:`, and `refactor:`. Do not squash all development into one final commit. Follow the commit sequence in `plan.md`.

## Reproducibility requirements

- Record package versions, time, seeds, dataset file URLs, model parameters and feature columns.
- Train preprocessing only on historical training data.
- Do not tune any decision rule on the final temporal test set.
- Regenerate figures and tables from the saved artifacts; never hand-edit empirical values.
- Do not commit source participant records or participant-level prediction outputs by default.
- Keep the ontology versioned and ensure each clinical rule has a source and scope note.

## Clinical-safety requirements

Do not describe the app as a diagnostic tool. Do not turn screening eligibility into a diagnosis. Do not make causal claims about medication or disease from NHANES associations. Document incomplete guideline coverage and fairness implications of race/ethnicity mappings.
