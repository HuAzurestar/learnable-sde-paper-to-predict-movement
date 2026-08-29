# Git collaboration policy

`main` is the protected, always-green integration branch. Each ordinary change
uses an open Issue, a short-lived matching branch, an Issue-first commit/PR
title, and a reviewed PR. For manuscript work use
`paper/<issue>-<summary>` and `#<issue> paper: <summary>`.

```bash
git switch main
git pull --ff-only origin main
git switch -c paper/142-method-boundary
# run the canonical document checks in CONTRIBUTING.md
git add <paths>
git diff --cached
git commit
git push -u origin paper/142-method-boundary
```

Refresh a private topic branch with `git fetch origin` then
`git rebase origin/main`; never rebase or force-push `main`. Resolve conflicts
deliberately, run document checks again, and abort an uncertain rebase. Revert
published changes instead of rewriting history. A version tag is annotated
from a verified `main` commit; release/PDF publishing remains intentionally
unconfigured until an approved scholarly release process exists.

Raw data, row-level material, local mounts, checkpoints, private outputs,
credentials, and their archives are prohibited. Main branch protection must
require one review and the stable `ci / required` check.
