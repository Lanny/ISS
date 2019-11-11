# ISS
[![Build Status](https://travis-ci.org/RyanJenkins/ISS.svg?branch=master)](https://travis-ci.org/RyanJenkins/ISS)

Oldschool Forum Software. Design tenets are:

- Should be at least somewhat usable on a potato using an EDGE connection
- Performance and correctness over feature richness
- Javascript should be optional, UI shouldn't second guess user agents
- Responsive pages
- Should be able to withstand the spamocalypse 
- Development using notepad is highly encouraged

# Setting it up

Using a virutal env is encouraged for your sanity but entirely optional.

You'll need to grab a few debendencies for this project:
```
$ sudo apt-get install python-pip postgresql npm gulp
```

IDE entirely optional:
```
$ sudo snap install pycharm-community --classic
```

Start by cloning the project. Copy the `test_settings.py` file into the ISS app directory and rename it `settings.py`. This defines a test forum and uses the postgres driver. ~~If you'd like to use a different DB edit the file
appropriately~~ the search functionality depends on postgres' text search and indexing behavior in a non-driver-portable way. You could probably use another DB with some minor fiddling with the source but only postgres is being tested against.

Next install serverside dependencies from the top level of the project:

```
$ pip install -r requirements.txt
```

If you are just developing, use this as a refrence for creating the DB:
```
$ sudo -u postgres psql
# create database iss_db;
# create user iss_user with password 'iss_pass';
# grant all privileges on database iss_db to iss_user;
```

Next run the migrations to init the DB (Dont forget to fill in the DB details in settings.py):

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

If you want rotating banners drop them in `ISS/static/banners` and restart the server. You can make up some test data using thing admin interface (url `/admin/`)

# Development Tips
- When `DEBUG` is true, you can use ctrl+P on any page to cycle through the available themes.

# Configuration
Every ISS instance must define a `FORUM_CONFIG` setting. Default values exist
for every key so it may be empty. Here is a list of the recognized properties
and what each does:

| Option | Description| Default |
| -- | -- | -- |
| forum_name | The name of the site as presented to users. Used in a couple of places, notably breadcrumbs and page titles. | 'INTERNATIONAL SPACE STATION' |
| forum_domain | Domain used in composing absolute urls (only used in emails) | 'yourdomain.com' |
| default_protocol | Protocol used in composing absolute urls (only used in emails) | 'http' |
| email_host_blacklist | List of email hosts users are not allowed to register new accounts with | [] |
| banner_dir | A path, relative to the static dir (in the src tree) that contains an arbitrary number of forum banners in jpg, gif, or png format. One of the files from this dir will be randomly selected for the page banner on each page load. | 'banners' |
| min_post_chars | The minimum length, in characters, of a post. | 1
| max_post_chars | The maximum length of a post, in characters. Defaults to the number of characters in the first chapter of Dune | 19476 |
| min_thread_title_chars | The minimum length, in characters, of a thread title | 1 |
| threads_per_forum_page | The number of threads to be per page in a thread list like a subforum or in thread searches |
| posts_per_thread_page | The number of posts to show on each page of a thread by default. Users may override this value. | 20 |
| ninja_edit_grace_time | The amount of time, in seconds, after post creation that a user can edit their post without it being branded with an edit notice and timestamp. | 120 |
| private_message_flood_control | The number of seconds users must wait after sending a private message before they can send a new one. | 30 |
| title_ladder | Used for assigning users a user title based on their post count. See utils.py for the format. | see utils.py |
| recaptcha_settings | Either `None` or a 2-tuple with your reCAPTCHA site(public) and secret keys in that order to be used at registration time. If this is None users will be able to register without solving a captcha. | None |
| max_avatar_size | The maximum filesize for avatars, in bytes. Regardless of this value the display size of avatars is constrained to 75px in either dimension | 128kB |
| extensions | A list of forum extensions to be enabled. Currently only 'taboo' is available | [] |
| min_age_to_anonymize | A timedelta indicating how long an account needs to have existed before it can anonymize itself | timedelta(days=28) |
| min_posts_to_anonymize | The minimum number of posts an account must have made before it can anonymize itself | 151 |
| initial_account_period_total | The number of posts an account must have to exit the post rate limiting period | 150 |
| initial_account_period_limit | The number of posts a new account may make within a given time period | 20 |
| initial_account_period_width | The time period in which a new account is allowed to make at most `initial_account_period_limit` posts | timedelta(days=1) |
| captcha_period | The number of posts an account must make before it will no longer need to complete a captcha with each post | 0 |
| enable_registration | Allow new users to register accounts without an invite. | True
| enable_invites | Allow registration of new accounts with invites | False |
| invite_expiration_time | The length of time an invite will remain valid after being generated |
| max_embedded_items | The maximum number of images or videos a single post is allowed to contain. Do not set too high, a page with 100 embedded youtube videos will lock up many browsers | 5
