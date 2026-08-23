#!/bin/sh
# 
#  Show git status and recent commits
#
#  Note: Run from repo root
#
# -----------------------------------------------------------------------------

git status --short

echo '---' 

git log --oneline -5

