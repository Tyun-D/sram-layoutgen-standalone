# Project Remote Sync Audit

- local_head: `9eef97fbb3956ae155175ecff27ebfe485d3a636`
- remote_url: `https://github.com/Tyun-D/sram-layoutgen-standalone.git`
- ls_remote: `FAILED_TLS_HANDSHAKE`
- fetch: `FAILED_TLS_HANDSHAKE`
- push: `FAILED_TLS_HANDSHAKE`

## Diagnostics

- `git ls-remote`, `git fetch origin --prune`, and `git push -u origin project/mainline-inventory-20260726` all failed with the same error:
  `gnutls_handshake() failed: The TLS connection was non-properly terminated.`
- Git is using `http.proxy=http://127.0.0.1:7890` from `~/.gitconfig`.
- The shell environment exposes `HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:20092`.
- `http.version` is already `HTTP/1.1`, including a repo-local retry.
- `~/.ssh` contains only `known_hosts`; no private/public key pair was present, so no trusted SSH remote switch was attempted.

## Fallback

- A complete-history bundle was created and verified:
  `/data1/qujh/project_checkpoints/project-mainline-inventory-9eef97f.bundle`
- bundle_sha256: `99d1551241d1d9803ad8844d3712ded6bcb5102dccd557c521ed2f791be751ee`
