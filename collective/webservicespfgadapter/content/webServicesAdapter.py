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

from Products.TemplateFields import ZPTField as ZPTField

from types import StringTypes


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
    LinesField('info_headers',
        required=0,
        searchable=0,
        read_permission=ModifyPortalContent,
        vocabulary=DisplayList((
            ('REMOTE_ADDR', 'IP address of the user who completed the form', ),
            ('REMOTE_USER', 'Logged in user (when applicable)', ),
            ('REMOTE_REALM', 'Domain of the logged in user (when applicable)', ),
            ('PATH_INFO', 'PATH_INFO', ),
            ('HTTP_X_FORWARDED_FOR', 'HTTP_X_FORWARDED_FOR', ),
            ('HTTP_USER_AGENT', "Description of the user's browser", ),
            ('HTTP_REFERER', 'Web page the user visited before filling out the form', ),
            ), ),
        widget=MultiSelectionWidget(
            label=u'HTTP Headers',
            description=u"""
                Select any items from the HTTP headers that you would like
                included with the form submission data.
                """,
            format='checkbox',
            ),
        ),
    ZPTField('submission_pt',
        schemata='template',
        write_permission=EDIT_TALES_PERMISSION,
        read_permission=ModifyPortalContent,
        widget=TextAreaWidget(
            label=u'Submission template',
            description=u"""
                This is the Zope Page Template used for rendering of the
                submission JSON. You don\'t need to modify it, but if you know
                TAL (Zope\'s Template Attribute Language) you have the full
                power to customize your submission to the web service.
                """,
            rows=20,
            visible={'edit': 'visible', 'view': 'invisible'},
            ),
        validators=('zptvalidator', ),
        ),
))


class FormWebServiceAdapter(FormActionAdapter):
    """ A form action adapter that sends the form submission to a web service. """

    schema = formWebServiceAdapterSchema
    portal_type = meta_type = 'FormWebServiceAdapter'
    archetype_name = 'Web Service Adapter'
    content_icon = 'FormAction.gif'

    security = ClassSecurityInfo()

    def __bobo_traverse__(self, REQUEST, name):
        # prevent traversal to attributes we want to protect
        if name == 'submission_pt':
            raise AttributeError
        return super(FormWebServiceAdapter, self).__bobo_traverse__(REQUEST, name)


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

        if self.info_headers:
            for f in self.info_headers:
                data[f] = getattr(REQUEST, f, '')

        pfg = self._getParentForm()
        submission = {
            'id': pfg.id,
            'title': pfg.title,
            'owner': pfg.getOwner().getUserName(),
            'data': data,
            }


    security.declareProtected(View, 'allFieldDisplayList')
    def allFieldDisplayList(self):
        """ returns a DisplayList of all fields """
        return self.fgFieldsDisplayList()


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
