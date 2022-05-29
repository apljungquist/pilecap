#!/usr/bin/env bash
set -e

export GIT_AUTHOR_NAME="Alice"
export GIT_AUTHOR_EMAIL="alice@example.com"
export GIT_AUTHOR_DATE="Thu, 01 Jan 1970 00:00:00 +0000"
export GIT_COMMITTER_NAME="Bob"
export GIT_COMMITTER_EMAIL="bob@example.com"
export GIT_COMMITTER_DATE="Thu, 01 Jan 1970 00:00:00 +0000"

if [ ! -d .git ]; then
  git init .
  git reset "`git commit-tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904 -m "Initial commit"`"
  git tag v0.0.0
  git add .
  git commit -m "Add boilerplate from template"
fi
