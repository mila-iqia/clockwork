#!/bin/sh

# See "main.md" or "internationalization.md" for more details about this script.
# This script is just a way to avoid copy/pasting two big pybabel command lines
# every time that we have some new strings displayed to the user through clockwork_web
# and we need to specify what the French version of some English text is going to be.

# Generate the translation template file (`.pot` file)
pybabel extract -F clockwork_web/babel.cfg -o clockwork_web/static/locales/messages.pot clockwork_web/
# Update the pre-existing translation file(s) (`.po` file(s))
pybabel update -i clockwork_web/static/locales/messages.pot -d clockwork_web/static/locales/
