#!/bin/sh
# Push the current branch and open a PR that merges into main (merge commit, so the grouped commits stay visible).
# Usage: tools/ship.sh "PR title" [BODYFILE]   (run from a topic branch, never from main)
# The body is read from a FILE (write it with the Write tool); never pass multi-line text on the command line.
# For a one-liner body a plain second argument still works, but a file is always safer.
set -e
br=$(git rev-parse --abbrev-ref HEAD)
[ "$br" = main ] && { echo "on main: make a topic branch first (git switch -c topic/name)"; exit 1; }
git push -u origin "$br"
if [ -n "$2" ] && [ -f "$2" ]; then
  gh pr create --base main --head "$br" --title "$1" --body-file "$2"
else
  gh pr create --base main --head "$br" --title "$1" --body "${2:-Grouped commits from branch $br.}"
fi
# --auto waits for required checks; with none configured GitHub refuses it as "clean", so merge right away.
gh pr merge "$br" --merge --delete-branch --auto 2>/dev/null || gh pr merge "$br" --merge --delete-branch
git switch main && git pull -q --ff-only
