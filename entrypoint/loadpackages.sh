export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate
cd /mvp/
uv pip install --no-deps --no-index --no-build-isolation -e . --python $(which python)
