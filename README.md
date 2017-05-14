# ISS
[![Build Status](https://travis-ci.org/RyanJenkins/ISS.svg?branch=master)](https://travis-ci.org/RyanJenkins/ISS)

Oldschool Forum Software. Design tenets are:

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
postgres driver. ~~If you'd like to use a different DB edit the file
appropriately~~ the search functionality depends on postgres' text search and
indexing behavior in a non-driver-portable way. If you disable migration 0014
the rest of the code should work in theory but this configuration is not
"officially" supported.

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

# Configuration
Every ISS instance must define a `FORUM_CONFIG` setting. Default values exist
for every key so it may be empty. Here is a list of the recognized properties
and what each does:

- `forum_name` - The name of the site as presented to users. Used in a couple of places, notably breadcrumbs and page titles.
- `banner_dir` - A path, relative to the static dir (in the src tree) that contains an arbitrary number of forum banners in jpg, gif, or png format. One of the files from this dir will be randomly selected for the page banner on each page load.
- `min_post_chars` - The minimum length, in characters, of a post. Validation is only done when making a post through the typical web form.
- `min_thread_title_chars` - The minimum length, in characters, of a thread title. Validation is only done when making a post through the new thread form.
- `threads_per_forum_page` - The number of threads to show on the thread list for a forum.
- `posts_per_thread_page` - The number of posts to show on each page of a thread. Note that changing this breaks post links that were generated previously.
- `general_items_per_page` - The number of items per page for lists of things that don't have their own per-page config property.
- `ninja_edit_grace_time` - The amount of time, in seconds, after post creation that a user can edit their post without it being branded with an edit notice and timestamp.
- `private_message_flood_control` - The number of seconds users must wait after sending a private message before they can send a new one.
- `title_ladder` - A sequence of 2-tuples in (int, string) format. Indicates the user title a user without a custom user title will receive after having made that many posts.
- `recaptcha_settings` - Either `None` or a 2-tuple with your reCAPTCHA site(public) and secret keys in that order to be used at registration time. If this is None users will be able to register without solving a captcha.
