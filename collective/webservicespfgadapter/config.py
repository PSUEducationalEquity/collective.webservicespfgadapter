""" config -- shared values """

__author__ = 'Paul Rentschler <par117@psu.edu>'
__docformat__ = 'plaintext'

from Products.CMFCore.permissions import setDefaultRoles



### End of likely customizations
### Change anything below and things are likely to break
########################################################

## The Project Name
PROJECT_NAME = 'WebServicesPFGAdapter'


# Permission to create the action adapter
WSA_ADD_CONTENT_PERMISSION = 'PloneFormGen: Add Web Service Adapters'
setDefaultRoles(WSA_ADD_CONTENT_PERMISSION, ('Manager', 'Owner', ))

