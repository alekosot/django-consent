Django Consent
========================================

A Django app for managing privileges that a user has granted the website.
These differ from permissions where the website defines what a user can do,
but rather are what the user gives the website permission to do. This could be
used for example when asking the user if you can post to their twitter, or
send them newsletter updates.

This app has no external requirements beyond Django and Python. Only Django
1.11+, Python 2.7+ and 3.4+ are officialy supported.

Contents
========

.. toctree::
 :maxdepth: 1

 models
 views
 changelog

Installation
========================================

Use pip::

    pip install django-consent


After installing, add 'consent' to your ``INSTALLED_APPS`` and run a migrate.

You will then need to integrate the views into your urls.py. This adds a view
for the user see see all the privileges and also to edit them.

.. doctest::

    from consent.views import ConsentListView, ConsentEditView

    urlpatterns = patterns('',
        url(r'^$', ConsentListView.as_view(), name="privileges"),
        url(r'^edit/$', ConsentEditView.as_view(), name="edit_privileges"),
    )
