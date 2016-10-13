# ISS
Oldschool Forum Software. Design tennants are:

- Performance and correctness over feature richness
- Django admin is an acceptable moderation tool in most cases
- Javascript should be optional
- Responsive pages, mobile-specific designs are shit, 1-col 4 lyfe
- Slugs are dumb, pks are all anyone has ever needed.

# Setting it up

You'll need pip and npm installed to grab dependencies, both should be available
through your OS's package manager.

Start by cloning the project. Copy the `test_settings.py` file into the ISS app
directory and rename it `settings.py`. This defines a test forum and uses the
sqlite driver, if you'd like to use a different DB edit the file appropriately.

Next install serverside dependencies from the top level of the project:

```
$ pip install -r requirements.txt
```

Using a virutal env is encouraged for your sanity but entirely optional.  Note
that if you want to use sqlite for development you can temporarily remove the
psychopg dependency from requirements.txt, but please do not check this change
in.

Next run the migrations to init the DB:

```
$ ./manage.py migrate
```

And create yourself an account:

```
$ ./manage.py createsuperuser
Username: Lanny
Email: l@l.lol
Password: 
Password (again): 
Superuser created successfully.
```

Install the frontend dependencies:

```
$ cd ISS/static-src
$ npm install
```

And build the frontend assets:

```
$ cd ISS/static-src
$ gulp generate
```

The `gulp watch` task is also defined for file watching/rebuilding.

Once all that's done you can start up the dev server and start making changes:

```
$ ./manage.py runserver
```

If you want rotating banners drop them in `ISS/static/banners` and restart the 
server. You can make up some test data using thing admin interface (url
`/admin/`)

# TODO
In no particular order:

- Login
- Registartion
- New Thread
- New Post
- Unread Posts in Thread / Thread Subscriptions
- View Subscriptions (UserCP) 
- Private Messages
    - View
    - New
    - Reply
    - "Alerts"
- Navigation
