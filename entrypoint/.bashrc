exit() {
    echo "Formatting on shell exit"
    format.sh
    builtin exit "$@"
}
