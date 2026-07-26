# Artifact Storage Policy

## Store In Normal Git

- source code
- tests
- JSON
- CSV
- Markdown

## Store In Git LFS Only If Already Enabled

- long-lived versioned GDS artifacts

This repository currently does not have working `git lfs` available in the local environment, so COLLAB-P0 does not migrate history or enable LFS.

## Large Artifact Handling

- `tar.gz`
- `bundle`
- large `lyrdb`
- deterministic A/B GDS comparison sets
- review atlas bundles

Large artifacts should go to one of:

- GitHub Release attachments
- server shared directory
- external transfer

## What Git Tracks When The Large Artifact Lives Elsewhere

- file name
- size
- SHA-256
- evidence role
- storage location
