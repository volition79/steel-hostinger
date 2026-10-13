#!/bin/sh
set -eu
# The lock file must never be removed: all cooperating containers use its inode.
mkdir -p /data/browser
exec flock --nonblock --conflict-exit-code 73 --no-fork /data/browser/.steel-profile-owner.lock /bin/sh -ec '
  # Only the exclusive profile owner may remove stale Chromium singleton links.
  rm -f /data/browser/SingletonLock /data/browser/SingletonCookie /data/browser/SingletonSocket
  exec /app/api/entrypoint.sh
'
