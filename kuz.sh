#!/usr/bin/env bash

set -Eeo pipefail
trap cleanup SIGINT SIGTERM ERR EXIT

VERBOSE=0
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
if [[ -n "$VIRTUAL_ENV" ]]; then virt_env="$VIRTUAL_ENV"; fi

usage() {
  cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") param1 [-h] [-v]

Script description here.

Available options:
  -h, --help      Print this help and exit
  -v, --verbose   Print verbose output
  venv      Use virtualenv to run the script
  freeze    Update the requirements.txt file with the latest versions of the dependencies
  update    Install the latest versions of the dependencies from the requirements.txt file
EOF
  exit
}

cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
}

setup_colors() {
  if [[ -t 2 ]] && [[ -z "${NO_COLOR-}" ]] && [[ "${TERM-}" != "dumb" ]]; then
    NOFORMAT='\033[0m' RED='\033[0;31m' GREEN='\033[0;32m' ORANGE='\033[0;33m' BLUE='\033[0;34m' PURPLE='\033[0;35m' CYAN='\033[0;36m' YELLOW='\033[1;33m'
  else
    NOFORMAT='' RED='' GREEN='' ORANGE='' BLUE='' PURPLE='' CYAN='' YELLOW=''
  fi
}

venv() {
  if [[ -n "$virt_env" ]]; then
    msg "Virtualenv is already activated"
  else
    msg "To activate the virtualenv, run: source venv/bin/activate"
  fi
}

exit_venv() {
  if [[ -n "$virt_env" ]]; then
    msg "Deactivating virtualenv"
    deactivate
  else
    msg "Virtualenv is not activated"
  fi
}

freeze() {

  if [[ -z "$virt_env" ]]; then
    msg "Activating virtualenv" verbose
    source "$script_dir/env/bin/activate"
  fi
  msg "Updating requirements.txt"
  pip freeze >"$script_dir/requirements.txt"
  if [[ -z "$virt_env" ]]; then
    msg "Deactivating virtualenv" verbose
    deactivate
  fi
}

install() {
  if [[ -z "$virt_env" ]]; then
    msg "Activating virtualenv" verbose
    source "$script_dir/env/bin/activate"
  fi
  msg "Installing dependencies"
  pip install -r "$script_dir/requirements.txt"
  if [[ -z "$virt_env" ]]; then
    msg "Deactivating virtualenv" verbose
    deactivate
  fi
}

msg() {
  if [[ ("${2-}" == "verbose" && $VERBOSE -eq 1) || -z "${2-}" ]]; then
    if [[ "${2-}" == "verbose" ]]; then
      echo >&2 -e "${ORANGE}${1-}${NOFORMAT}"
    else
      echo >&2 -e "${1-}"
    fi
  fi
}

die() {
  local msg=$1
  local code=${2-1} # default exit status 1
  msg "${RED}$msg${NOFORMAT}"
  msg "usage: $(basename "${BASH_SOURCE[0]}") [-h] param1 [-v]"
  exit "$code"
}

parse_args() {
  for arg in "$@"; do
    case "$arg" in
    -h | --help) usage ;;
    -v | --verbose) VERBOSE=1 ;;
    -?*) die "Unknown args: $1" ;;
    *) continue ;;
    esac
  done
  args=("$@")
  [[ ${#args[@]} -eq 0 ]] && die "Missing script arguments"
  return 0
}

parse_params() {
  for arg in "$args"; do
    case "$arg" in
    -?*) continue ;;
    venv) venv ;;
    exit) exit_venv ;;
    freeze) freeze ;;
    update) install ;;
    ?*) die "Unknown option: ${args[0]}" ;;
    esac
  done

}

setup_colors
parse_args "$@"
parse_params "$@"
