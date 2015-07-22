""" WebServicesPFGAdapter, basic Zope Product Initialization """

__author__ = 'Paul Rentschler <par117@psu.edu>'
__docformat__ = 'plaintext'


import sys
import logging
logger = logging.getLogger("WebServicesPFGAdapter")


from Products.Archetypes.public import process_types, listTypes
from Products.CMFCore import utils

from collective.webservicespfgadapter.config import PROJECT_NAME, \
    WSA_ADD_CONTENT_PERMISSION
from Products.PloneFormGen.config import ADD_CONTENT_PERMISSION


def initialize(context):
    """ Initializer called when used as a Zope 2 product. """
    import content

    content_types, constructors, ftis = process_types(
        listTypes(PROJECT_NAME),
        PROJECT_NAME
        )
    allTypes = zip(content_types, constructors)
    for atype, constructor in allTypes:
        kind = "%s: %s" % (PROJECT_NAME, atype.archetype_name)
        if atype.portal_type == 'SalesforcePFGAdapter':
            permission = SFA_ADD_CONTENT_PERMISSION
        else:
            permission = ADD_CONTENT_PERMISSION
        utils.ContentInit(
            kind,
            content_types      = (atype, ),
            permission         = permission,
            extra_constructors = (constructor, ),
            fti                = ftis,
            ).initialize(context)
