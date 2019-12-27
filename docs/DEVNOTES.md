# DEVNOTES

## Code Layout
There are to main parts to the ISS code, the frontend and the backend. The backend consists of the typical Django components, views, models, form etc. The fontend is a gulp pipeline that produces static assets for the site. It lives under the `ISS/static-src` directory. It outputs into the static directory which the backend either serves directly in development mode or processes to be served by something like nginx in production.

## Setting it up

The easiest way to get a development environment up and running is to use the dockerized environment. This removes much of the headache of figuring out dependencies, configuration, and OS specific oddities. To get started make sure you have docker and docker-compose installed (Docker Desktop is the usual way to get these on dev machines) and simply:

```
docker-compose up --build
```

The docker containers use a hefty amount of storage and come with some startup overhead. This is usually not a big deal, but if you'd like to run ISS without dockerization see the [legacy setup instructions](../blob/master/docs/SETUP_LEGACY.md).

### Creating an admin
You can simply:

```
docker exec -it iss_web_1 ./manage.py createsuperuser
```

In general, any time you might want to run a management command or do some operation in the webserver environment, it will look like:

```
docker exec -it iss_web_1 <your command here>
```

Note that the container must be up in order for this to work.

## Development Tips
- When debug mode is on, you can use ctrl+P on any page to cycle through the available themes without reloading a page.

## Configuration
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
