# -*- coding: utf-8 -*-

"""
    PyLucid lexivon models
    ~~~~~~~~~~~~~~~~~~~~~~

    Last commit info:
    ~~~~~~~~~
    $LastChangedDate: 2009-08-11 15:39:06 +0200 (Di, 11 Aug 2009) $
    $Rev: 2264 $
    $Author: JensDiemer $

    :copyleft: 2009 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v2 or above, see LICENSE for more details
"""

from django.db import models
from django.core import urlresolvers
from django.db.models import signals
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

# http://code.google.com/p/django-tagging/
#import tagging
from tagging.fields import TagField

from pylucid_project.pylucid_plugins import update_journal

from pylucid.shortcuts import failsafe_message
from pylucid.markup.converter import apply_markup
from pylucid.models import PageContent, Language, PluginPage
from pylucid.models.base_models import AutoSiteM2M, UpdateInfoBaseModel
#from PyLucid.tools.content_processors import apply_markup, fallback_markup
#from PyLucid.models import Page


TAG_INPUT_HELP_URL = \
"http://google.com/search?q=cache:django-tagging.googlecode.com/files/tagging-0.2-overview.html#tag-input"

class Links(UpdateInfoBaseModel):
    url = models.URLField(verify_exists=True, max_length=255)
    title = models.CharField(_('Title'), help_text=_("Url title"), max_length=255)
    entrie = models.ForeignKey("LexiconEntry")

class LexiconEntry(AutoSiteM2M, UpdateInfoBaseModel):
    """
    A lexicon entry.

    inherited attributes from AutoSiteM2M:
        sites     -> ManyToManyField to Site
        on_site   -> sites.managers.CurrentSiteManager instance
        site_info -> a string with all site names, for admin.ModelAdmin list_display

    inherited attributes from UpdateInfoBaseModel:
        createtime     -> datetime of creation
        lastupdatetime -> datetime of the last change
        createby       -> ForeignKey to user who creaded this entry
        lastupdateby   -> ForeignKey to user who has edited this entry
    """
    term = models.CharField(_('Term'), help_text=_("Term in primitive form"), max_length=255)
    lang = models.ForeignKey(Language)
    alias = TagField(# from django-tagging
        help_text=mark_safe(
            _('alias for this entry. <a href="%s" class="openinwindow"'
            ' title="Information about tag splitting.">tag format help</a>') % TAG_INPUT_HELP_URL
        )
    )
    tags = TagField(# from django-tagging
        help_text=mark_safe(
            _('tags for this entry. <a href="%s" class="openinwindow"'
            ' title="Information about tag splitting.">tag format help</a>') % TAG_INPUT_HELP_URL
        )
    )
    short_definition = models.CharField(_('Short definition'),
        help_text=_("A short explain."), max_length=255
    )
    content = models.TextField(_('Content'), help_text=_("Explain the term"))
    markup = models.IntegerField(
        max_length=1, choices=PageContent.MARKUP_CHOICES,
        help_text="the used markup language for this entry",
    )

    is_public = models.BooleanField(
        default=True, help_text="Is post public viewable?"
    )

    def get_update_info(self):
        """ update info for update_journal.models.UpdateJournal used by update_journal.save_receiver """
        if not self.is_public: # Don't list non public articles
            return

        return {
            "lastupdatetime": self.lastupdatetime,
            "user_name": self.lastupdateby,
            "lang": self.lang,
            "object_url": self.get_absolute_url(),
            "title": _("New lexicon entry '%s'.") % self.term,
        }

    def get_absolute_url(self):
        viewname = "Lexicon-detail_view"
        reverse_kwargs = {"term":self.term} #slugify(self.term)
        try:
            # This only worked inner lucidTag
            return urlresolvers.reverse(viewname, kwargs=reverse_kwargs)
        except urlresolvers.NoReverseMatch:
            # Use the first PluginPage instance
            try:
                return PluginPage.objects.reverse("lexicon", viewname, kwargs=reverse_kwargs)
            except urlresolvers.NoReverseMatch:
                return "?lexicon=%s" % self.term

    def get_html(self):
        """
        returns the generate html code from the content applyed the markup.
        """
        return apply_markup(self.content, self.markup, failsafe_message)

    def __unicode__(self):
        return self.term

    class Meta:
        unique_together = (("lang", "term"),)
        ordering = ('term',)


signals.post_save.connect(receiver=update_journal.save_receiver, sender=LexiconEntry)

# Bug in django tagging?
# http://code.google.com/p/django-tagging/issues/detail?id=151#c2
#try:
#    tagging.register(BlogEntry)
#except tagging.AlreadyRegistered: # FIXME
#    pass