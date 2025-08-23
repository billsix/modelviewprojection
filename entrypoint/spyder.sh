/format.sh
cd /mvp/
python3 -m pip install --no-deps -e . --break-system-packages --root-user-action=ignore
python3 -m pip install moviepy
exec spyder -p .
