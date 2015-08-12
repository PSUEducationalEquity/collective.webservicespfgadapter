""" config -- shared values """

__author__ = 'Paul Rentschler <par117@psu.edu>'
__docformat__ = 'plaintext'

from Products.CMFCore.permissions import setDefaultRoles


############################################
### Things you might customize for your site

extra_data = {
    'REMOTE_USER': 'Logged in user',
    'REMOTE_REALM': "User's domain",
    'HTTP_X_FORWARDED_FOR': "User's address",
    'HTTP_USER_AGENT': "User's browser",
    'HTTP_REFERER': "Form's address",
    }


### End of likely customizations
### Change anything below and things are likely to break
########################################################

## The Project Name
PROJECT_NAME = 'WebServicesPFGAdapter'


# Permission to create the action adapter
WSA_ADD_CONTENT_PERMISSION = 'PloneFormGen: Add Web Service Adapters'
setDefaultRoles(WSA_ADD_CONTENT_PERMISSION, ('Manager', 'Owner', ))

# Permission to set the submission url
EDIT_URL_PERMISSION = 'PloneFormGen: Edit Web Service URL Settings'
setDefaultRoles(EDIT_URL_PERMISSION, ('Manager', 'Owner', ))

# Permission to manage the failure settings
EDIT_FAILURE_SETTINGS_PERMISSION = 'PloneFormGen: Edit Web Service Adapter Failure Settings'
setDefaultRoles(EDIT_FAILURE_SETTINGS_PERMISSION, ('Manager', ))
