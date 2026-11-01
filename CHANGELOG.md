# Project history

## 2026-11-01

- Advance the Compat source pin to its readability refactor, with focused C modules,
  explanatory Windows comments and separate user/developer documentation. Music
  loss/crashes appear fixed in observed use, without proof across every case.

- Pin Compat preview `v0.1.0-preview.1` (`02ed088`), with documented display internals,
  optional stock backdrop reuse and CI-published release packages. Game artwork is
  loaded from the owner's executable and is not distributed with the shim.
- Link [Imperialism Compat](https://github.com/warthurton/imperialism-compat) at
  `compat/` as a Git submodule pinned to a specific revision. The legacy display
  and music build entry points, and the default game-acceptance harness path,
  use that checkout. Initialize it with `git submodule update --init compat`,
  or clone RE with `--recurse-submodules`.
- Document the intentional project boundary: **Compat** maintains runtime display
  and music compatibility, build tooling, CI and distributable releases; **RE**
  maintains decompilation, analysis, snapshot-based verification and portable
  game-logic reimplementation. The split gives each project its own maintenance
  and release lifecycle while the submodule records what RE tests against.

## 2026-10-31

- Purposefully extract the maintained display shim and music-wrapper build tooling
  into Imperialism Compat. Preserve the earlier source history in this repository
  and retain legacy build entry points here. The extraction separates compatibility
  work from decompilation/reimplementation; it is not a game-logic milestone.
- Keep the real-game acceptance harness with RE, where its saved fixtures and
  memory readers live. Both display/music codec combinations completed the
  ten-check snapshot turn test, with original DLLs/INI files restored and the
  game stopped. This did not establish long-term music stability.
