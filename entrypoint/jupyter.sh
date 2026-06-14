export VIRTUAL_ENV_DISABLE_PROMPT=1
source /venv/bin/activate
cd /mvp/
# install the package editable so the notebooks can `import modelviewprojection`
# (mirrors shell.sh; the install effect lands on /venv on disk).
loadpackages.sh
exec \
  jupyter lab \
         --allow-root \
         --ip=0.0.0.0 \
         --port=8888 \
         --ServerApp.token='' \
         --ServerApp.password='' \
         --ServerApp.disable_check_xsrf=True \
         --no-browser
