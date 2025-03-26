# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),

## 1.1.0

### Features
- Added in-app captchas to replace google recaptcha, because recaptcha is cancer
- Added `ISS.middleware.CSPMiddleware`. Adopting this middleware is not required, but strongly recommended as it provides valuable XSS mitigation.

### Deprecations
- Removed `recaptcha_settings` from FORUM_CONFIG
  - Captchas are now done in-app and thus are on by default, to disable them entirely set `disable_captchas` to `True` in FORUM_CONFIG
- Removed `banner_dir` from FORUM_CONFIG as this config hasn't been used for some time

### Bugfix/Trivial
- Updated default font size across themes to 14px
- Minor visual updates to user settings page
- Fixed visual z-index bug in auto-suggest dropdowns, noticeable when searching for a user on the user index page
- Fixed several issues in model admin where a select for a related field would enumerate all possible options, even in cases where possible relations might number in the thousands or millions (e.g. selecting the post to which a thanks belongs). Such fields are now read-only

## 1.0.0

Initial versioned release, representing a fully featured piece of performant, low bullshit, well tested forum software built over a decade development, drunkcoding and shitposting. May you use it in the spirit of human community, whatever form that may take.
