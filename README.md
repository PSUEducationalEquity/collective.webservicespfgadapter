# Introduction

This package provides an action adapter for
[Products.PloneFormGen](https://github.com/smcmahon/Products.PloneFormGen)
which submits the form data to a web service URL and handles potential
failures with the transmission.

Repository for this package is at: https://github.com/PSUEducationalEquity/collective.webservicespfgadapter

Issues are tracked at: https://github.com/PSUEducationalEquity/collective.webservicespfgadapter/issues


# Overview

PloneFormGen is a fantastic product for quickly and easily building online
forms hosted in a Plone web site. But sometimes you want to do more with
the data submitted via these forms than just email it off or store it on
the site. Perhaps you want to pass it to some other application, which is
where this product comes in.

In essence, this product acts as a proxy for resubmitting the form data
(in a modified fashion) to a different URL.

The initial use case for this product was to move all form submission data
off of the web server and into a different, more secure server for permanent
storage and access by certain users.


# Dependencies

Plone: Plone 4.3.6 (only tested with this version)

Requires:

* Plone.API (tested with version 1.5)
* PloneFormGen (tested with version 1.7.17)
* Requests (automatically installed if you install via Python package)


# Installation

* Clone this repository into the /src directory
* Add `collective.webservicespfgadapter` to the eggs section of your buildout configuration
* Add `src/collective.webservicespfgadapter` to the develop section of your buildout configuration
* Run buildout
* Restart Zope
* Go to the Site Setup page in the Plone interface and click on the Add-ons link.
Choose PloneFormGen Web Services Adapter (check its checkbox) and click the
Activate button. If it is not available on the Add-ons list, it usually means
that the product did not load due to missing prerequisites.


# Permissions

The package creates several permissions to provide granular access to what
information various user roles can change.

All information in the adapter can be viewed by a user with editing rights but
those users can only change the fields and extra data that are submitted.

To change the URL that the data is submitted to, the user must have the
`PloneFormGen: Edit Web Service URL Settings` permission which is granted to
the Manager and Owner roles by default.

To change the settings related to how the adapter behaves when the submission
to the web service failes, the user must have the
`PloneFormGen: Edit Web Service Adapter Failure Settings` permission which is
granted only to the Manager role by default.


# Preventing data loss due to submission failures

Passing information between servers is not a process that is guaranteed to
work every single time; problems happen. In it's default installation the
Web Services Adapter will raise an exception if the connection to the url
fails. This may or may not be an ideal result given that for most site
visitors Plone will display a very generic error message.

The option also exists to "Fail silently" meaning that the exception is
surpressed and the form, to the site visitor, appears to have processed
correctly and successful.

Failing silently along is probably not a good idea as it could very easily
result in lost form submissions that no one knows about.

To know about the failed submissions, provide one or more email addresses
(separated by a comma) in the "Notify on failure" field.

The last part of preventing data loss is to configure one or more of the
other PloneFormGen action adapters such as the Mailer or Save Data Adapter.
When used in combination with the "Run disabled adapters" setting, they
can be used to only capture failed submissions.

_Note:_ A disabled adapter is one that exists in the FormFolder but when
you edit the FormFolder the checkbox next to the action adapter is unchecked.
(It is checked by default when you add it to the FormFolder.)

If you are looking or a secure way of preventing data loss, consider using
a disabled Mailer adapter with GPG encryption turned on. This will result
in an email being sent only when the Web Services Adapter fails and the
contents of the form submission will be encrypted in the email to prevent
unauthorized access. For information on setting up GPG encryption with the
Mailer adapter, consult the PloneFormGen documentation.


# Credits

Steve McMahon and all the contributors to Products.PloneFormGen for creating
and continually maintaining such a great product.

Kenneth Reitz and the other contributors to the Requests library.

Jon Baldivieso, Andrew Burkhalter, Brian Gershon, David Glick, Jesse Snyder,
and Alex Tokar; the authors of
[Products.salesforcepfgadapter](https://github.com/collective/Products.salesforcepfgadapter)
from which I borrowed much of the fallback ideas and code.


# License

Developed at the Pennsylvania State University and licensed as open source.

See LICENSE.txt for details.
