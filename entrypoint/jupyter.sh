cd /mvp/
# in general this is super dangerous, but for our purposes,
# it's fine
exec  jupyter notebook \
         --allow-root \
         --ip=0.0.0.0 \
         --port=8888 \
         --no-browser \
         --NotebookApp.token='' \
         --NotebookApp.password=''

