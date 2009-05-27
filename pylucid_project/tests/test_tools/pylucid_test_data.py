# coding:utf-8

import os

if __name__ == "__main__":
    # run unittest directly
    os.environ['DJANGO_SETTINGS_MODULE'] = "pylucid_project.settings"

from django.http import HttpRequest
from django.contrib.auth.models import User#, AnonymousUser
from django.contrib.sites.models import Site#
from django.conf import settings

from dbtemplates.models import Template

from pylucid.models import PageTree, PageMeta, PageContent, PluginPage, Design, \
                                            EditableHtmlHeadFile, Language

SITEINFO_TAG = "***unittest siteinfo tag***"

TEST_SITES = [("test site 1", "test1.tld"), ("test site 2", "test2.tld")]
TEST_LANGUAGES = [("en", "english"), ("de", "deutsch")]


class TestSites(object):
    """
    Iterator over all existing Sites. Set settings.SITE_ID in iteration.
    Usage e.g.:
        for site in TestSites(verbosity=True):
            print "Activated site:", site
    """
    def __init__(self, verbosity=False):
        self.verbosity = verbosity
        self.index = 1
        
    def __iter__(self):
        return self
    
    def next(self):
        try:
            site_name, domain = TEST_SITES[self.index]
        except IndexError:
            raise StopIteration

        self.index += 1

        site, created = Site.objects.get_or_create(
            id=self.index, defaults={"name": site_name, "domain": domain}
        )
        if self.verbosity:
            if created:
                print("sites entry '%s' created." % site)
            else:
                print("sites entry '%s' exist." % site)

            print "Activate site: %r (ID:%s)" % (site, site.pk)
            
        settings.SITE_ID = site.pk
        Site.objects.clear_cache()
        
        current_site = Site.objects.get_current()
        assert current_site == site
    
        return site
        

class TestLanguages(object):
    """
    Interator over all test languages using get_or_create()
    """
    def __init__(self, verbosity=False):
        self.verbosity = verbosity
        self.index = 0
        
    def __iter__(self):
        return self
    
    def next(self):
        try:
            lang_code, description = TEST_LANGUAGES[self.index]
        except IndexError:
            raise StopIteration
        
        self.index += 1
        
        language, created = Language.objects.get_or_create(
            code=lang_code, defaults={"description": description}
        )
        if self.verbosity:
            if created:
                print("Language '%s' created." % lang_code)
            else:
                print("Language '%s' exists." % lang_code)
        return language



TEST_USERS = {
    "superuser": {
        "username": "superuser",
        "email": "superuser@example.org",
        "password": "superuser_password",
        "is_staff": True,
        "is_superuser": True,
    },
    "staff": {
        "username": "staff test user",
        "email": "staff_test_user@example.org",
        "password": "staff_test_user_password",
        "is_staff": True,
        "is_superuser": False,
    },
    "normal": {
        "username": "normal test user",
        "email": "normal_test_user@example.org",
        "password": "normal_test_user_password",
        "is_staff": False,
        "is_superuser": False,
    },
}

TEST_TEMPLATES = {
    "site_template/normal.html": {
        "content": \
"""<html><head><title>{{ page_title }} """+SITEINFO_TAG+"""</title>
<meta name="robots" content="{{ robots }}" />
<meta name="keywords" content="{{ page_keywords }}" />
<meta name="description" content="{{ page_description }}" />
<meta name="DC.Date" content="{{ page_lastupdatetime|date:_("DATETIME_FORMAT") }}" />
<meta name="DC.Date.created" content="{{ page_createtime|date:_("DATETIME_FORMAT") }}" />
<meta name="DC.Language" content="{{ page_language }}">
<link rel="canonical" href="{{ page_get_permalink }}" />
{% lucidTag head_files %}
</head>
<body>
{% lucidTag main_menu %}
{% lucidTag search %}
<!-- page_messages -->
{% lucidTag admin_menu %}
<!-- ContextMiddleware breadcrumb -->
{% lucidTag language %}
{% block content %}
    {{ page_content }}
{% endblock content %}
<a href="{{ page_get_permalink }}" title="permalink to this page">permalink</a>

powered by {{ powered_by }}
{{ login_link }}
<!-- script_duration -->
last modified: {{ page_lastupdatetime|date:_("DATETIME_FORMAT") }}
</body></html>"""
    },
}
TEST_HEADFILES = {
    "unittest/test.css": {
        "description": "CSS file for unittests.",
        "content": ".test { color:red; } /* "+SITEINFO_TAG+" */",
    }
}
TEST_DESIGNS = {
    "unittest_design": {
        "template_name": "site_template/normal.html",
        "headfiles": ("unittest/test.css",),
    },
}
TEST_PAGES = [
    {
        "slug": "1-rootpage",
        "sub-pages": [{"slug": "1-1-subpage"}, {"slug": "1-2-subpage"}],
    },
    {
        "slug": "2-rootpage",
        "sub-pages": [
            {"slug": "2-1-subpage"},
            {
                "slug": "2-2-subpage",
                "sub-pages": [{"slug": "2-2-1-subpage"}, {"slug": "2-2-2-subpage"}],
            }
        ],
    },
    {
        "slug": "3-pluginpage",
        "plugin": "pylucid_project.pylucid_plugins.unittest_plugin",
    },
]


def get_user(usertype):
    return User.objects.get(username=TEST_USERS[usertype]["username"])



def create_testusers(verbosity):
    """
    Create all available testusers.
    """
    def create_user(verbosity, username, password, email, is_staff, is_superuser):
        """
        Create a user and return the instance.
        """
        defaults = {'password':password, 'email':email}
        user, created = User.objects.get_or_create(
            username=username, defaults=defaults
        )
        if not created:
            user.email = email
        user.set_password(password)
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        if verbosity:
            print "Test user %r created." % user
        
    for usertype, userdata in TEST_USERS.iteritems():
        create_user(verbosity, **userdata)


def create_templates(verbosity, template_dict, site):
    """ create templates in dbtemplates model """
    template_map = {}
    for template_name, data in template_dict.iteritems():
        template, created = Template.objects.get_or_create(
            name = template_name, defaults = data
        )
        if created:
            template.content = template.content.replace(SITEINFO_TAG, site.name)
            template.save()
            if verbosity:
                print("template '%s' created" % template_name)
        elif verbosity:
                print("template '%s' exist" % template_name)
                
        if verbosity:
            print("add template on site: %s" % site.name)
        template.sites.add(site)
                
        template_map[template_name] = template
    return template_map


def create_headfiles(verbosity, headfile_dict, site, request):
    headfile_map = {}
    for filename, data in headfile_dict.iteritems():
        headfile = EditableHtmlHeadFile(
            filename = filename,
            description = data["description"],
            content = data["content"],
        )
        headfile.save(request)
        headfile.site.add(site)
        if verbosity:
            print("EditableStaticFile '%s' created on site: %s" % (filename, site.name))
        
        headfile_map[filename+site.name] = headfile
    return headfile_map


def create_design(verbosity, design_dict, request, site, template_map, headfile_map):   
    design_map = {}
    for design_name, data in design_dict.iteritems():
        template_name = data["template_name"]
        assert template_name in template_map
        design, created = Design.objects.get_or_create(request,
            name = design_name, defaults = {"template": template_name,}
        )
        if created:
            design.save(request)
            design.site.add(site)
            if verbosity:
                print("design '%s' created." % design_name)
            # Add headfiles
            for filename in data["headfiles"]:
                headfile = headfile_map[filename+site.name]
                design.headfiles.add(headfile)
                if verbosity:
                    print("Add headfile '%s'." % headfile)
            design.save(request)
        elif verbosity:
                print("Design '%s' exist." % design_name)
        
        design_map[design_name] = design
    return design_map


def create_meta(slug, lang_code, site_name, keys):
    """ usefull for auto creating default dicts """
    meta = {}
    for key in keys:
        meta[key] = "%s %s (lang:%s, site:%s)" % (slug, key, lang_code, site_name)
    return meta


def create_pages(verbosity, request, design_map, site, pages, parent=None):
    design = design_map["unittest_design"]
    for page_data in pages:
        slug = page_data["slug"]
        print slug
        
        #____________________________________________________
        if "plugin" in page_data:
            page_type = PageTree.PLUGIN_TYPE
        else:
            page_type = PageTree.PAGE_TYPE
        
        tree_entry, created = PageTree.objects.get_or_create(request,
            site=site, slug=slug, parent=parent,
            defaults={
                "design": design,
                "type": page_type,
            }
        )
        url = tree_entry.get_absolute_url()
        if verbosity:
            if created:
                #tree_entry.save(request)
                print("PageTree '%s' created." % url)
            else:
                print("PageTree '%s' exist." % url)
        
        # Create PageMeta, PageContent for the PageTree entry in all test languages
        for language in TestLanguages():
            # Create PageMeta:
            default_dict = create_meta(slug=tree_entry.slug, lang_code=language.code, site_name=site.name,
                keys = ("title", "description", "keywords")
            )
            pagemeta_entry, created = PageMeta.objects.get_or_create(request,
                page = tree_entry, lang = language,
                defaults = default_dict
            )
            if verbosity:
                if created:
                    #pagemeta_entry.save(request)
                    print("PageMeta '%s' - '%s' created." % (language, tree_entry.slug))
                else:
                    print("PageMeta '%s' - '%s' exist." % (language, tree_entry.slug))

            if tree_entry.type == PageTree.PLUGIN_TYPE:
                # It's a plugin page
                pluginpage, created = PluginPage.objects.get_or_create(request,
                    page = tree_entry,
                    lang = language,
                    defaults = {"pagemeta": pagemeta_entry, "app_label": page_data["plugin"]},
                )
                if verbosity:
                    if created:
                        print("PluginPage '%s' created." % pluginpage)
                    else:
                        print("PluginPage '%s' exist." % pluginpage)
            else:
                # Create PageContent:
                default_dict = create_meta(slug=tree_entry.slug, lang_code=language.code, site_name=site.name,
                    keys = ("content",)
                )
                default_dict["markup"] = PageContent.MARKUP_CREOLE
                content_entry, created = PageContent.objects.get_or_create(request,
                    page = tree_entry,
                    lang = language,
                    pagemeta = pagemeta_entry,
                    defaults = default_dict
                )
                content_entry.content = content_entry.content.replace(SITEINFO_TAG, site.name)
                content_entry.save(request)
                if verbosity:
                    if created:
                        print("PageContent '%s' created." % content_entry)
                    else:
                        print("PageContent '%s' exist." % content_entry)
        
        if "sub-pages" in page_data:
            print "--- create sub pages ---"
            create_pages(verbosity, request, design_map, site,
                pages=page_data["sub-pages"], parent=tree_entry
            )
            print "---"





def create_test_data(request, site, verbosity):
    template_map = create_templates(verbosity, TEST_TEMPLATES, site)
    headfile_map = create_headfiles(verbosity, TEST_HEADFILES, site, request)
    design_map = create_design(verbosity, TEST_DESIGNS, request, site, template_map, headfile_map)
    
    # Create PageTree, PageMeta and PageContent in every test language
    create_pages(verbosity, request, design_map, site, pages=TEST_PAGES)
    


def create_pylucid_test_data(site=None, verbosity=True):
    """ create complete test data for "running" PyLucid """
    if verbosity:
        print "\nCreate complete test data for 'running' PyLucid"
        
    create_testusers(verbosity)
    
    request = HttpRequest()
    request.user = get_user(usertype="superuser")
    
    for site in TestSites(verbosity):
        if verbosity:
            print("------------------------------------")
            print("create test data for site: %r" % site)
            
        create_test_data(request, site, verbosity)

    if verbosity:
        print "Test database filled with test data."
        print


if __name__ == "__main__":
    from django.db import connection
    
    db_name = connection.creation.create_test_db(verbosity=True, autoclobber=False)
    print "\nTest database '%s' created" % db_name
    create_pylucid_test_data()