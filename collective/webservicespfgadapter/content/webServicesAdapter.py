"""
A form action adapter that sends the form submission to a web service.
"""

__author__ = 'Paul Rentschler <par117@psu.edu>'
__docformat__ = 'plaintext'


from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import *

from Products.ATContentTypes.content.base import registerATCT

from Products.CMFCore.permissions import View, ModifyPortalContent

from Products.PloneFormGen.config import *
from Products.PloneFormGen.content.actionAdapter import FormActionAdapter, FormAdapterSchema
from Products.PloneFormGen.interfaces import IPloneFormGenForm

from collective.webservicespfgadapter.config import extra_data

from types import StringTypes

import json, requests


formWebServiceAdapterSchema = FormAdapterSchema.copy() + Schema((
    StringField('url',
        required=1,
        searchable=0,
        read_permission=ModifyPortalContent,
        widget=StringWidget(
            label=u'Web Services Address',
            description=u"""
                Specify the web address of the service that will receive
                the form submission information. It's highly recommended
                that the web address start with 'https://' to ensure the
                form data is transmitted securely.
                """,
            ),
        ),
    LinesField('showFields',
        required=0,
        searchable=0,
        read_permission=ModifyPortalContent,
        vocabulary='allFieldDisplayList',
        widget=PicklistWidget(
            label=u'Include selected fields',
            description=u"""
                Pick the fields whose inputs you would like to include in
                the web service submission. If empty, all fields will be sent.
                """,
            ),
        ),
    LinesField('extraData',
        required=0,
        searchable=0,
        read_permission=ModifyPortalContent,
        vocabulary='extraDataDisplayList',
        widget=MultiSelectionWidget(
            label=u'Extra Data',
            description=u"""
                Pick any extra data you would like included with the
                web service submission.
                """,
            format='checkbox',
            ),
        ),
    BooleanField('failSilently',
        required=0,
        searchable=0,
        default='0',
        read_permission=ModifyPortalContent,
        widget=BooleanWidget(
            label=u'Fail silently',
            description=u"""
                If an error occurs while submitting the data to the web
                service all warnings and error messages WILL BE SUPPRESSED.
                ONLY enable this option if you have configured another action
                adapter, otherwise the form data WILL BE LOST!
                """),
            ),
        ),
    BooleanField('storeFailedSubmissions',
        required=0,
        searchable=0,
        default='0',
        read_permission=ModifyPortalContent,
        widget=BooleanWidget(
            label=u'Store failed submissions locally',
            description=u"""
                If an error occurs while submitting the form data to the web
                service, the entire submission will be stored in this action
                adapter for later retrieval and an email will be sent to the
                address listed in 'Notify on failure'.
                """),
            ),
        ),
    StringField('notifyOnFailure',
        required=0,
        searchable=0,
        read_permission=ModifyPortalContent,
        widget=StringWidget(
            label=u'Notify on failure',
            description=u"""
                Comma separated list of email addresses that will be notified
                if an error occurs while submitting the form data to the web
                service AND 'Store failed submissions locally' is checked.
                """),
            ),
        ),
    BooleanField('runDisabledAdapters',
        required=0,
        searchable=0,
        default='0',
        read_permission=ModifyPortalContent,
        widget=BooleanWidget(
            label=u'Run disabled adapters',
            description=u"""
                If an error occurs while submitting the form data to the web
                service, should any disabled action adapters be run?
                This allows you to setup other action adapters (e.g. Save
                Data Adapter) that are ONLY run when an error occurs while
                submitting to the web service.
                """),
            ),
        ),
    LinesField('failedSubmissions',
        required=0,
        searchable=0,
        read_permission=ModifyPortalContent,
        schemata='failures',
        widget=LinesWidget(
            label=u'Submissions that failed to send to the web service',
            description=u"""
                Submissions that failed to go through to the web service are
                stored here if 'Store failed submissions locally' is checked.
                The submissions are stored one per line in JSON format
                unless an encryption key is present, then they are stored
                one per line with carriage returns replaced by pipes (|).
                """),
            ),
        ),
))

# if gpg is not None:
#     formWebServiceAdapterSchema = formWebServiceAdapterSchema + Schema((
#         StringField('gpg_keyid',
#             schemata='encryption',
#             accessor='getGPGKeyId',
#             mutator='setGPGKeyId',
#             write_permission=USE_ENCRYPTION_PERMISSION,
#             read_permission=ModifyPortalContent,
#             widget=StringWidget(
#                 label=u'Key-Id',
#                 description=u"""
#                     Give your key-id, email address, or whatever works to
#                     match a public key from the current keyring.
#                     It will be used to encrypt the entire failed submission.
#                     Contact the site administrator if you need to install a
#                     new public key.
#                     TEST THIS FEATURE BEFORE GOING PUBLIC!
#                     """),
#                 ),
#             ),
#         ))


class FormWebServiceAdapter(FormActionAdapter):
    """ A form action adapter that sends the form submission to a web service. """

    schema = formWebServiceAdapterSchema
    portal_type = meta_type = 'FormWebServiceAdapter'
    archetype_name = 'Web Service Adapter'
    content_icon = 'FormAction.gif'

    security = ClassSecurityInfo()

    security.declareProtected(View, 'allFieldDisplayList')

    def allFieldDisplayList(self):
        """ returns a DisplayList of all fields """
        return self.fgFieldsDisplayList()


    def __bobo_traverse__(self, REQUEST, name):
        # prevent traversal to attributes we want to protect
        if name == 'submission_pt':
            raise AttributeError
        return super(FormWebServiceAdapter, self).__bobo_traverse__(REQUEST, name)


    security.declareProtected(View, 'extraDataDisplayList')
    def extraDataDisplayList(self):
        """ returns a DisplayList of the extra data options """
        dl = DisplayList()
        for key, value in extra_data.iteritems():
            dl.add(key, value)
        return dl


    security.declarePrivate('_getParentForm')
    def _getParentForm(self):
        """ Gets the IPloneFormGenForm parent of this object. """
        parent = self.aq_parent
        while not IPloneFormGenForm.providedBy(parent):
            try:
                parent = parent.aq_parent
            except AttributeError:
                parent = None
                break;
        return parent


    security.declareProtected(View, 'onSuccess')
    def onSuccess(self, fields, REQUEST=None):
        """ Submits the data to the web service. """
        data = {}
        for f in fields:
            showFields = getattr(self, 'showFields', [])
            if showFields and f.id not in showFields:
                continue
            if not f.isLabel():
                val = REQUEST.form.get(f.fgField.getName(), '')
                if not type(val) in StringTypes:
                    # Zope has marshalled the field into
                    # something other than a string
                    val = str(val)
                data[f.title] = val

        if self.extraData:
            for f in self.extraData:
                data[extra_data[f]] = getattr(REQUEST, f, '')

        pfg = self._getParentForm()
        submission = {
            'form-id': pfg.id,
            'name': pfg.title,
            'url': pfg.absolute_url(),
            'owner': pfg.Creator(),
            'data': json.dumps(data),
            }
        try:
            response = requests.post(
                self.url,
                data=submission,
                timeout=1.5
                )
        except requests.exceptions.ConnectionError:
            print "Ugh! Server's down :("
        except requests.exceptions.Timeout:
            print "Gitty Up! Crack the whip on the server."
        else:
            if response.status_code != 201:
                print "Ack! something went horribly wrong!"


    security.declareProtected(ModifyPortalContent, 'setShowFields')
    def setShowFields(self, value, **kwargs):
        """ Reorder form inputs to match field order. """
        # This wouldn't be necessary if the PickWidget retained order.
        self.showFields = []
        for field in self.fgFields(excludeServerSide=False):
            id = field.getName()
            if id in value:
                self.showFields.append(id)


registerATCT(FormWebServiceAdapter, 'WebServicesPFGAdapter')
