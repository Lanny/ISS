# Developing ISS

The easiest and recommended way to get started with developing ISS is use docker compose. If you have docker installed, simply run:

```sh
docker compose -f docker-compose.dev.yml up --build
```

to start up ISS in development mode. This will start a postgres instance and init a schema, start up the frontend build pipeline in watch mode, and start the webserver in devmode. Changing files should automatically trigger a fast rebuild. There is no hot reloading in the browser however, so you'll generally manually refresh a page after making a change.

By default, the server will be accessible at http://127.0.0.1:8000/

## Data setup

Starting the dev compose configuration above will create a running development server with an instantiated DB schema. However the database won't contain any records (users, posts, forums, etc.) and you won't be able to do most of the things you might want to use forum software for. To fix this you'll either want to seed the database, or you can set up your initial configuration manually.

### Seeding the Database 

The easiest way to get a basic data setup is to seed the database with some precreated testing data using the following command:

```sh
docker exec -i $(docker ps | grep postgres | awk '{ print $1 }') psql -U iss_user -v -d iss < seed-data.sql
```

You may need to restart the dev server after this to run any migrations that have been created since the last seed DB snapshot was taken.

Most of the configuration that's created will be obvious, the following is a list of users that will be created, the password on each account is `password`:

- `admin` - Super user account with access to the admin interface

To take a new snapshot of the local dev database:

```sh
docker exec -it $(docker ps | grep postgres | awk '{ print $1 }') pg_dump -U iss_user iss > seed-data.sql
```

### Manually Creating Records

The first thing you need to do is to create a super user, this account will have access to the admin interface and generally have all the permissions available within the system. All commands from this point will assume that you have the dev compose configuration up and running. To create your super user, run the following command:

```sh
docker exec -it $(docker ps | grep iss_web | awk '{ print $1 }') /opt/ISS/src/manage.py createsuperuser
```

You'll be prompted to enter a username, email address, and password. The email address does not need to be reachable, `test@example.com` will work just fine. Once you complete this process you can log in as this user.

With your superuser in hand, you'll then want to create your first categories and forums. A forum is a collection of threads, and a category is a collection of forums. To get started, visit the admin interface at http://127.0.0.1:8000/admin and log in. You'll see a number of record types that can be managed from the admin interface, but generally you'll only be interacting with users, forums, and categories.

First, click the "Add" link on the "Category" line. On the resulting page enter a category name (e.g. "General"). You can set a priority, this field determines the order that categories will appear on the home page, lower values appear first.

Next return to the [admin interface](http://127.0.0.1:8000/admin/) and click "Add" next to the "Forum" record type. Repeat the process here, selecting your recently created category, picking a name and description. Repeat this process one more time, creating a forum, and checking the "Is Trash" checkbox. A trash forum is necessary for spam control, and where trashed threads will be sent.

After this, you should have a pair of forums visible on the home page, and be able to create threads, posts, polls, etc. and generally test out the features of ISS.

## Testing

You can run the tests by standing up the docker container and running the following command:

```
docker exec -w /opt/ISS/src -it $(docker ps | grep iss_web | awk '{ print $1 }') bash -c 'export ISS_SETTINGS_FILE=/opt/ISS/config/test_settings && ./manage.py test'
```
