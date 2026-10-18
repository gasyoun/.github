# Contributing

## Where things live

- Dictionary source text is canonical upstream and is **not** edited directly in
  the view repositories. Corrections go through the correction queue for the
  owning dictionary (see the repository README).
- Each repository keeps its own changelog; add one bullet under `## [Unreleased]`,
  never rewrite released sections.

## Issues

Use the issue form that matches the request: **bug**, **feature**, or **data
correction**. A data-correction issue needs the dictionary, the headword, the
current reading, and the proposed reading.

## Pull requests

- One concern per pull request; say what changes and what proves it.
- Run the repository's checks locally where they exist (`data-validate`,
  `changelog-lint`).
- Never commit personal data, credentials, or scanned text you do not have the
  right to redistribute.
- Release numbering is owned by the maintainers; do not bump versions in a
  feature pull request.

## Conduct

By participating you agree to the Code of Conduct.
