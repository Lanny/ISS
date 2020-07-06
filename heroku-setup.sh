#!/bin/bash

function heroku_set_config {
  echo "Setting $1=$2"
  heroku config:set "$1=$2"
  if [ $? -ne 0 ]
  then
    echo "Failed to set $1, bailing"
    exit 1
  fi
}

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

heroku_user="$(heroku whoami)"
if [ $? -eq 0 ]
then
  read -p "Currently logged in to heroku as $heroku_user, continue? (Y/n)" -n 1 -r
  if [[ ! $REPLY =~ ^[Nn]$ ]]
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

existing_app="$(heroku info | grep "===" | awk '{ print $2 }')"
if [ ! -z "$existing_app" ]
then
  echo "Found existing heroku app..."
  read -p "Destroy app before continuing (recommended)? (y/N)" -n 1 -r
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
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

echo "Adding postgres addon..."
heroku addons:create heroku-postgresql:hobby-dev

db_url="$(heroku config | grep DATABASE_URL | awk '{ print $2 }')"

echo "Found DB URL to be $db_url"

echo "Setting instance env vars..."
heroku_set_config "ALLOWED_HOST" $app_domain
heroku_set_config "DJANGO_SETTINGS_MODULE" "heroku-settings"

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
heroku ps:exec DATABASE_URL="$db_url" DJANGO_SETTINGS_MODULE=heroku-settings /app/.heroku/python/bin/python manage.py createsuperusernoinput --username="$username" --email="$email" --password="$password"

echo "App and superuser created. Visit https://$app_domain/ to see your new app\n\n"
echo "Some useful links"
echo "================="
