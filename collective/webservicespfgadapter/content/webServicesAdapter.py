"""
A form action adapter that sends the form submission to a web service.
"""

__author__ = 'Paul Rentschler <par117@psu.edu>'
__docformat__ = 'plaintext'


from AccessControl import ClassSecurityInfo
from Acquisition import aq_parent

from Products.Archetypes.atapi import *
from Products.ATContentTypes.content.base import registerATCT
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName

from Products.PloneFormGen.config import *
from Products.PloneFormGen.content.actionAdapter import \
    FormActionAdapter, FormAdapterSchema
from Products.PloneFormGen.content.formMailerAdapter import FormMailerAdapter
from Products.PloneFormGen.content.likertField import LikertField
from Products.PloneFormGen.content.saveDataAdapter import FormSaveDataAdapter
from Products.PloneFormGen.interfaces import \
    IPloneFormGenActionAdapter, IPloneFormGenFieldset, IPloneFormGenForm

from collective.webservicespfgadapter.config import *

from collections import OrderedDict
from types import StringTypes

import json, logging, requests, sys, traceback


logger = logging.getLogger("PloneFormGen")

formWebServiceAdapterSchema = FormAdapterSchema.copy() + Schema((
    StringField('url',
        required=1,
        searchable=0,
        write_permission=EDIT_URL_PERMISSION,
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
    StringField('fieldset_separator',
        required=0,
        searchable=0,
        default=' / ',
        read_permission=ModifyPortalContent,
        widget=StringWidget(
            label=u'Fieldset separator',
            description=u"""
                For fields contained in a fieldset, prefix the field name
                with the fieldset title and separate them with these
                characters. If blank, the fieldset title is NOT prepended.
                """
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
        write_permission=EDIT_FAILURE_SETTINGS_PERMISSION,
        read_permission=ModifyPortalContent,
        widget=BooleanWidget(
            label=u'Fail silently',
            description=u"""
                If an error occurs while submitting the data to the web
                service all warnings and error messages will be suppressed.
                ONLY enable this option if you have configured another action
                adapter, otherwise the form data WILL BE LOST!
                """,
            ),
        ),
    StringField('notifyOnFailure',
        required=0,
        searchable=0,
        write_permission=EDIT_FAILURE_SETTINGS_PERMISSION,
        read_permission=ModifyPortalContent,
        widget=StringWidget(
            label=u'Notify on failure',
            description=u"""
                Comma separated list of email addresses that will be notified
                if an error occurs while submitting the form data to the web
                service and 'Fail Silently' is checked.
                """,
            ),
        ),
    BooleanField('runDisabledAdapters',
        required=0,
        searchable=0,
        default='0',
        write_permission=EDIT_FAILURE_SETTINGS_PERMISSION,
        read_permission=ModifyPortalContent,
        widget=BooleanWidget(
            label=u'Run disabled adapters',
            description=u"""
                If an error occurs while submitting the form data to the web
                service and 'Fail Silently' is checked, should the disabled
                action adapters be run?
                This allows you to setup other action adapters (e.g. Save
                Data Adapter) that are ONLY run when an error occurs while
                submitting to the web service.
                """,
            ),
        ),
))


class FormWebServiceAdapter(FormActionAdapter):
    """
    A form action adapter that sends the form submission to a web service.
    """
    schema = formWebServiceAdapterSchema
    portal_type = meta_type = 'FormWebServiceAdapter'
    archetype_name = 'Web Service Adapter'
    content_icon = 'FormAction.gif'

    security = ClassSecurityInfo()

    security.declareProtected(View, 'allFieldDisplayList')


    def allFieldDisplayList(self):
        """
        returns a DisplayList of all fields
        """
        return self.fgFieldsDisplayList()


    def __bobo_traverse__(self, REQUEST, name):
        # prevent traversal to attributes we want to protect
        if name == 'submission_pt':
            raise AttributeError
        return super(FormWebServiceAdapter, self).__bobo_traverse__(REQUEST, name)


    security.declareProtected(View, 'extraDataDisplayList')
    def extraDataDisplayList(self):
        """
        returns a DisplayList of the extra data options
        """
        dl = DisplayList()
        for key, value in extra_data.iteritems():
            dl.add(key, value)
        return dl


    security.declarePrivate('_getParentForm')
    def _getParentForm(self):
        """
        Gets the IPloneFormGenForm parent of this object.
        """
        parent = self.aq_parent
        while not IPloneFormGenForm.providedBy(parent):
            try:
                parent = parent.aq_parent
            except AttributeError:
                parent = None
                break;
        return parent


    def _onSuccess(self, fields, REQUEST=None):
        """
        Submits the form data to the web service.
        """
        data = OrderedDict()
        fieldset = ''
        showFields = getattr(self, 'showFields', [])
        for field in fields:
            if showFields and field.id not in showFields:
                continue
            if field.isLabel() and field.portal_type == 'FieldsetStart':
                fieldset = field.title
            elif field.isLabel() and field.portal_type == 'FieldsetEnd':
                fieldset = ''
            if not field.isLabel():
                val = REQUEST.form.get(field.fgField.getName(), '')
                if isinstance(val, list):
                    pass
                elif isinstance(field.fgField, LikertField):
                    likert_vals = OrderedDict()
                    for index, question in enumerate(field.getLikertQuestions()):
                        try:
                            likert_vals[question] = val[str(index + 1)]
                        except (KeyError, TypeError):
                            likert_vals[question] = 'No answer'
                    val = likert_vals
                elif not type(val) in StringTypes:
                    # Zope has marshalled the field into
                    # something other than a string
                    val = str(val)
                title = field.title
                if IPloneFormGenFieldset.providedBy(field.aq_parent) \
                and self.fieldset_separator != '':
                    title = "%s%s%s" % (
                        field.aq_parent.title,
                        self.fieldset_separator,
                        field.title
                        )
                elif fieldset != '' and self.fieldset_separator != '':
                    title = "%s%s%s" % (
                        fieldset,
                        self.fieldset_separator,
                        field.title
                        )
                if title in data.keys():
                    # start at 2 since the title without a number is 1
                    increment = 2
                    while "%s %s" % (title, increment) in data.keys():
                        increment += 1
                    title = "%s %s" % (title, increment)
                data[title] = val

        if self.extraData:
            for field in self.extraData:
                data[extra_data[field]] = getattr(REQUEST, field, '')

        pfg = self._getParentForm()
        submission = {
            'form-id': pfg.id,
            'name': pfg.title,
            'url': pfg.absolute_url(),
            'owner': pfg.Creator(),
            'data': json.dumps(data, default=lambda obj: obj.__dict__),
            }
        try:
            # timeout is set for 5 seconds which is an eternity on the web
            response = requests.post(
                self.url,
                data=submission,
                timeout=60,
                )
        except:
            raise
        else:
            if response.status_code != 201:
                msg = "Web service submission failed by returning status " \
                    + "code: %s. Was expecting status code 201." % response.status_code
                raise Exception(msg)


    security.declareProtected(View, 'onSuccess')
    def onSuccess(self, fields, REQUEST=None):
        """
        Wrap _onSuccess so fallback behavior can be implemented when calls
        to the web service fail.
        """
        # heavily borrowed from: https://plone.org/products/salesforcepfgadapter

        message = None
        try:
            self._onSuccess(fields, REQUEST)
        except Exception as e:
            # swallow the exception
            t, v = sys.exc_info()[:2]

            # generate a log message regarding the exception
            log_msg = 'Unable to save form data to the web service at (%s). '
            logger.exception(log_msg % '/'.join(self.getPhysicalPath()))

            if not self.failSilently:
                raise

            else:
                # get all the active and inactive save data and mailer adapters
                formFolder = self._getParentForm()
                enabled_adapters = formFolder.getActionAdapter()
                adapters = [o for o in formFolder.objectValues() if IPloneFormGenActionAdapter.providedBy(o)]
                active_savedata = [o for o in adapters if isinstance(o, FormSaveDataAdapter)
                                                       and o.id in enabled_adapters]
                inactive_savedata = [o for o in adapters if isinstance(o, FormSaveDataAdapter)
                                                         and o.id not in enabled_adapters]
                active_mailer = [o for o in adapters if isinstance(o, FormMailerAdapter)
                                                     and o.id in enabled_adapters]
                inactive_mailer = [o for o in adapters if isinstance(o, FormMailerAdapter)
                                                       and o.id not in enabled_adapters]

                # start the failure email message
                message = "Someone submitted this form (%s), but the data " \
                    + "couldn't be saved to the web service due to an exception." \
                    + "\n\n" \
                    + "The data was saved in the following locations:\n"
                message = message % (
                        formFolder.absolute_url(),
                        )

                # add a list of where the data was stored to the email message
                for adapter in active_savedata:
                    message += "  - Save Data Adapter (%s)\n" % adapter.absolute_url()

                if self.runDisabledAdapters:
                    for adapter in inactive_savedata:
                        message += "  - Save Data Adapter (%s)\n" % adapter.absolute_url()
                        # Trigger the adapter since it's disabled.
                        # This can be used to record data *only* when submitting to
                        #   the web service fails.
                        adapter.onSuccess(fields, REQUEST)

                for adapter in active_mailer:
                    message += "  - Mailer Adapter (%s)\n" % adapter.absolute_url()

                if self.runDisabledAdapters:
                    for adapter in inactive_mailer:
                        message += "  - Mailer Adapter (%s)\n" % adapter.absolute_url()
                        # Trigger the adapter since it's disabled.
                        # This can be used to record data *only* when submitting to
                        #   the web service fails.
                        adapter.onSuccess(fields, REQUEST)

                if not active_savedata and not inactive_savedata and \
                   not active_mailer and not inactive_mailer:
                    message += "  - NO WHERE! The data was lost.\n"

                message += "\nTechnical details on the exception:\n"
                message += ''.join(traceback.format_exception_only(t, v))

                # send an email if an address is provided
                if self.notifyOnFailure:
                    # get email configuration from Plone
                    pprops = getToolByName(self, 'portal_properties')
                    site_props = getToolByName(pprops, 'site_properties')
                    portal = getToolByName(self, 'portal_url').getPortalObject()

                    from_addr = site_props.getProperty('email_from_address') or \
                        portal.getProperty('email_from_address')
                    mailer = getToolByName(self, 'MailHost')
                    try:
                        mailer.send(
                            message,
                            mto=self.notifyOnFailure,
                            mfrom=from_addr,
                            subject='Form submission to web service failed',
                            immediate=False,
                            )
                    except Exception as e:
                        logger.exception(e)


    security.declareProtected(ModifyPortalContent, 'setShowFields')
    def setShowFields(self, value, **kwargs):
        """
        Reorder form inputs to match field order.
        """
        # This wouldn't be necessary if the PickWidget retained order.
        self.showFields = []
        for field in self.fgFields(excludeServerSide=False):
            id = field.getName()
            if id in value:
                self.showFields.append(id)


registerATCT(FormWebServiceAdapter, 'WebServicesPFGAdapter')
