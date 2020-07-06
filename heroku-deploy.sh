#!/bin/bash

set -x 

function heroku_set_config {
  echo "Setting $1=$2"
  heroku config:set "$1=$2"
  if [ $? -ne 0 ]
  then
    echo "Failed to set $1, bailing"
    exit 1
  fi
}

function iss_set_config {
  heroku_set_config "ISS_CONF__$1" $2
  heroku ps:restart web
}

function gen_secret_key {
  local schars='abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
  local key=''
  local idx=0

  for i in {1..50}
  do
    idx=$(($RANDOM % 50))
    key="$key${schars:$idx:1}"
  done
  echo "$key"
}

function get_config {
  echo "$(heroku config | grep $1 | tr -s ' ' | cut -d ' ' -f 2)"
}

function ensure_heroku {
  echo "Looking for Heroku CLI tools..."
  which heroku

  if [ $? -ne 0 ]
  then
    echo "Heroku CLI not found..."

    which brew
    has_brew=$(( $? == 0 ))  

    if [ $has_brew == 1 ]
    then
      read -p "Homebrew found, install Heroku CLI from brew? (y/N)" -n 1 -r
      if [[ ! $REPLY =~ ^[Yy]$ ]]
      then
          exit 1
      fi

      brew tap heroku/brew
      brew install heroku
    else
      read -p "Install Heroku CLI from Heroku install script (requires sudo)? (y/N)" -n 1 -r
      if [[ ! $REPLY =~ ^[Yy]$ ]]
      then
          exit 1
      fi
      curl https://cli-assets.heroku.com/install.sh | sh
    fi
  else
    echo "Heroku CLI was found...."
  fi
}

function ensure_logged_in {
  heroku_user="$(heroku whoami)"
  if [ $? -eq 0 ]
  then
    read -p "Currently logged in to heroku as $heroku_user, continue? (Y/n)" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]
    then
      echo "Declined to continue as $heroku_user. Run \"heroku logout\" to deauth then run this script again."
      exit 2
    fi
  else
    echo "Initiating heroku login..."
    heroku login
    if [ $? -ne 0 ]
    then
      echo "Login unsuccessful, bailing"
      exit 1
    fi
  fi
}

function run_management_command {
  heroku run python manage.py $@
}

function sub_help {
  echo "Usage: $ProgName <subcommand> [options]\n"
  echo "Subcommands:"
  echo "    setup           Create a new Heroku app and superuser"
  echo "    iss_set_config  Set a forum config value"
  echo ""
}

function sub_setup {
  ensure_heroku
  ensure_logged_in

  existing_app="$(heroku info | grep "===" | awk '{ print $2 }')"
  if [ ! -z "$existing_app" ]
  then
    echo "Found existing heroku app..."
    read -p "Destroy app before continuing (recommended)? (y/N)" -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
      echo ""
      echo "Destroying $existing_app"
      heroku apps:destroy --confirm "$existing_app"
      git remote remove heroku
    fi
  fi

  echo "Creating a new app for ISS"
  heroku create
  if [ $? -ne 0 ]
  then
    echo "App creation unsuccessful, bailing"
  fi

  app_domain="$(heroku info -s | grep web_url | cut -d/ -f3)"
  echo "Following operations will apply to the app: $app_domain"


  echo "Setting buildpacks for app..."

  heroku buildpacks:set heroku/python
  heroku buildpacks:add --index 1 heroku/nodejs

  echo "Adding postgres and mailgun addons..."
  heroku addons:create heroku-postgresql:hobby-dev
  heroku addons:create mailgun:starter

  db_url="$(get_config DATABASE_URL)"

  echo "Found DB URL to be $db_url"

  echo "Setting instance env vars..."
  heroku_set_config "ALLOWED_HOST" $app_domain
  heroku_set_config "DJANGO_SETTINGS_MODULE" "heroku-settings"
  heroku_set_config "SECRET_KEY" "$(gen_secret_key)"

  echo "Deploying current branch to Heroku"
  git_branch="$(git rev-parse --abbrev-ref HEAD)"
  git push heroku "$git_branch:master" --force

  echo "Enter info for superuser account on newly created app (use this to log in):"

  read -p "Username: " -r
  username=$REPLY

  read -p "Email: " -r
  email=$REPLY

  read -p "Password: " -s -r
  password=$REPLY

  echo "Creating superuser..."
  run_management_command createsuperusernoinput --username="$username" --email="$email" --password="$password"

  if [ $? -eq 0 ]
  then
    echo "App and superuser created. Visit https://$app_domain/ to see your new app"
    echo ""
    exit 0
  else
    echo "Failed to create superuser. That's bad!"
    exit 1
  fi
}

function sub_iss_set_config {
  iss_set_config $1 $2
}

ProgName=$(basename $0)

subcommand=$1
case $subcommand in
    "" | "-h" | "--help")
        sub_help
        ;;
    *)
        shift
        sub_${subcommand} $@
        if [ $? = 127 ]; then
            echo "Error: '$subcommand' is not a known subcommand." >&2
            echo "       Run '$ProgName --help' for a list of known subcommands." >&2
            exit 1
        fi
        ;;
esac

