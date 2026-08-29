# Fail-fast setup: a failed step (venv activate, loadpackages editable install)
# aborts rather than dropping you into / running a shell-exec script against a
# half-set-up tree. The final `exec bash` is a FRESH bash not under -e, so
# interactive/script behaviour is unchanged. `set -e` only (no -u).
set -e
export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate
cd /mvp/
loadpackages.sh
# No args -> interactive shell (as before). Args (a `-c '...'` payload from
# `make shell-exec`) -> run them after setup, in a fresh bash not under -e.
exec bash "$@"
