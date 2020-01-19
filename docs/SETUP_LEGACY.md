# Setting it up (without Docker)

Using a virutal env is encouraged for your sanity but entirely optional.

You'll need pip, node/npm, and postgres installed. On debian based distros you can do:

```
$ sudo apt-get install python-pip postgresql npm
```

IDE entirely optional:

```
$ sudo snap install pycharm-community --classic
```

Alternately (preferred):

```
$ notepad.exe
```

Start by cloning the project. Copy the `test_settings.py` file into the ISS app directory and rename it `settings.py`. This defines a test forum and uses the postgres driver. ~~If you'd like to use a different DB edit the file
appropriately~~ the search functionality depends on postgres' text search and indexing behavior in a non-driver-portable way. You could probably use another DB with some minor fiddling with the source but only postgres is being tested against.

Next install serverside dependencies from the top level of the project:

```
$ pip install -r requirements.txt
```

If you are just developing, use this as a reference for creating the DB:
```
$ sudo -u postgres psql
# create database iss_db;
# create user iss_user with password 'iss_pass';
# grant all privileges on database iss_db to iss_user;
```

Next run the migrations to init the DB (Don't forget to fill in the DB details in settings.py):

```
$ ./manage.py migrate
```

We also use a DB cache so you need to create that table separately:

```
$ ./manage.py createcachetable
```

The default settings also specify a `default` cache as a LocMemCache. If you're running in a production environment you're encouraged to use Redis or memcahced as these will be significantly more performant if you're running multiple WS instances. After setting up caches you can create yourself an account:

```
$ ./manage.py createsuperuser
Username: Lanny
Email: l@l.lol
Password: 
Password (again): 
Superuser created successfully.
```

Install the frontend dependencies and build the frontend assets:

```
$ cd ISS/static-src
$ npm install
$ gulp generate
```

The `gulp watch` task is also defined for file watching/rebuilding.

Once all that's done you can start up the dev server and start making changes:

```
$ ./manage.py runserver
```

If you want rotating banners drop them in `ISS/static/banners` and restart the server. You can make up some test data using thing admin interface (url `/admin/`)

# Production Notes
- As with any Django project *be sure `DEBUG` in settings.py is false*
  - Also be sure to your `SECRET_KEY` is not in any repo (e.g. copied out of test_settings.py)
- Set up redis or memcachd for the default cache
- Set up the email settings (see https://docs.djangoproject.com/en/2.2/topics/email/)
- You want to run nginx in front of ISS, Python should not be serving static assets
- To produce production ready statics:
  - Build the assets using `gulp generate --optimizeAssets` (from the static-src directory)
  - Set `STATIC_ROOT` to point to some writable directory to hold generated statics
  - Run `./manage.py collectstatic` to schlep files over to `STATIC_ROOT`
