#!/bin/sh
# Push the current branch and open a PR that merges into main (merge commit, so the grouped commits stay visible).
# Usage: tools/ship.sh "PR title" ["PR body"]   (run from a topic branch, never from main)
set -e
br=$(git rev-parse --abbrev-ref HEAD)
[ "$br" = main ] && { echo "on main: make a topic branch first (git switch -c topic/name)"; exit 1; }
git push -u origin "$br"
body=${2:-"Grouped commits from branch $br.

Claude-Session: https://claude.ai/code/session_011NDxF8J8uuECMfwpFjRKE3"}
gh pr create --base main --head "$br" --title "$1" --body "$body"
# --auto waits for required checks; with none configured GitHub refuses it as "clean", so merge right away.
gh pr merge "$br" --merge --delete-branch --auto 2>/dev/null || gh pr merge "$br" --merge --delete-branch
git switch main && git pull -q --ff-only
