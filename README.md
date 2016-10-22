# ISS
Oldschool Forum Software. Design tennants are:

- Performance and correctness over feature richness
- Django admin is an acceptable moderation tool in most cases
- Javascript should be optional
- Responsive pages, mobile-specific designs are shit, 1-col 4 lyfe
- Slugs are dumb, pks are all anyone has ever needed.
- You get one theme, rice it yourself if you care
- Development using notepad is highly encouraged

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

- ~~Login~~
- Registartion
  - ~~base functionality~~
  - email verificiation
  - password reset
- Forum index
    - ~~make it work~~
    - ~~admin configurable ordering~~
    - figure out what to do with that "new" column that isn't slow
- ~~Thread locks~~
- Links to admin site
- User active status check before thread/post creation
- Thread page
    - ~~make it work~~
    - ~~pagination~~
- Forum thread list
    - ~~make it work~~
    - ~~order by updated time~~
    - pagination
    - go to newest post
    - go to oldest unread post
- ~~New Thread~~
- New Post
    - ~~Make it work~~
    - Quotes
        - Fix quote pyramids
        - In quick reply (ajax)
        - ~~no-js mode over to new-reply page~~
- Users
    - image embed option(s?) 
    - profile page
    - avatars
    - list of posts
    - make user titles work
- Unread Posts in Thread / Thread Subscriptions
- View Subscriptions (UserCP) 
- Private Messages
    - View
    - New
    - Reply
    - "Alerts"
- Navigation
    - Breadcrumbs
    - Sitemap? Whatever SEO magic the cool kids are into these days
- More than one usertitle
- Thanks
    - AJAX
    - nojs reload
    - list of thanked posts
- Markdown in posts
- Static pages (FAQ, whatever)
- New posts
