"""
Internationalization support.
"""
from __future__ import unicode_literals

from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils import six


__all__ = [
    'activate', 'deactivate', 'override', 'deactivate_all',
    'get_language',  'get_language_from_request',
    'get_language_info', 'get_language_bidi',
    'check_for_language', 'to_locale', 'templatize', 'string_concat',
    'gettext', 'gettext_lazy', 'gettext_noop',
    'ugettext', 'ugettext_lazy', 'ugettext_noop',
    'ngettext', 'ngettext_lazy',
    'ungettext', 'ungettext_lazy',
    'pgettext', 'pgettext_lazy',
    'npgettext', 'npgettext_lazy',
    'I18nRealBackend', 'I18nNullBackend'
]

# Here be dragons, so a short explanation of the logic won't hurt:
# We are trying to solve two problems: (1) access settings, in particular
# settings.USE_I18N, as late as possible, so that modules can be imported
# without having to first configure Django, and (2) if some other code creates
# a reference to one of these functions, don't break that reference when we
# replace the functions with their real counterparts (once we do access the
# settings).

class I18nRealBackend(object):
    """
    i18n backend to be used when settings.USE_I18N == True.
    This class can also be subclassed to build a custom
    i18n real backend.
    """
    def __getattr__(self, real_name):
        from django.utils.translation import trans_real
        return getattr(trans_real, real_name)

class I18nNullBackend(object):
    """
    i18n backend to be used when settings.USE_I18N != True.
    This class can also be subclassed to build a custom
    i18n null backend.
    """
    def __getattr__(self, real_name):
        from django.utils.translation import trans_null
        return getattr(trans_null, real_name)

def get_i18n_backend(i18n_backend_name, settings):
    """
    Get i18n backend object from settings variables:
    - I18N_BACKEND_REAL
    - I18N_BACKEND_NULL

    Args:
        i18n_backend_name: A string, either I18N_BACKEND_REAL or
            I18N_BACKEND_NULL
        settings: django.conf.settings
    Returns:
        An i18n backend object
    """
    i18n_class = getattr(settings, i18n_backend_name)
    i18n_path = i18n_class.split('.')
    if len(i18n_path) > 1:
        i18n_module_name = '.'.join(i18n_path[:-1])
    else:
        i18n_module_name = '.'
    i18n_module = __import__(i18n_module_name, {}, {}, i18n_path[-1])
    return getattr(i18n_module, i18n_path[-1])()

class Trans(object):
    """
    The purpose of this class is to store the actual translation function upon
    receiving the first call to that function. After this is done, changes to
    USE_I18N will have no effect to which function is served upon request. If
    your tests rely on changing USE_I18N, you can delete all the functions
    from _trans.__dict__.

    Note that storing the function with setattr will have a noticeable
    performance effect, as access to the function goes the normal path,
    instead of using __getattr__.
    """
    def get_trans(self):
        from django.conf import settings
        if settings.USE_I18N:
            i18n_backend_name = 'I18N_BACKEND_REAL'
        else:
            i18n_backend_name = 'I18N_BACKEND_NULL'
        return get_i18n_backend(i18n_backend_name, settings)

    def __getattr__(self, real_name):
        trans = self.get_trans()
        setattr(self, real_name, getattr(trans, real_name))
        return getattr(trans, real_name)

_trans = Trans()

# The Trans class is no more needed, so remove it from the namespace.
del Trans

def gettext_noop(message):
    return _trans.gettext_noop(message)

ugettext_noop = gettext_noop

def gettext(message):
    return _trans.gettext(message)

def ngettext(singular, plural, number):
    return _trans.ngettext(singular, plural, number)

def ugettext(message):
    return _trans.ugettext(message)

def ungettext(singular, plural, number):
    return _trans.ungettext(singular, plural, number)

def pgettext(context, message):
    return _trans.pgettext(context, message)

def npgettext(context, singular, plural, number):
    return _trans.npgettext(context, singular, plural, number)

gettext_lazy = lazy(gettext, str)
ngettext_lazy = lazy(ngettext, str)
ugettext_lazy = lazy(ugettext, six.text_type)
ungettext_lazy = lazy(ungettext, six.text_type)
pgettext_lazy = lazy(pgettext, six.text_type)
npgettext_lazy = lazy(npgettext, six.text_type)

def activate(language):
    return _trans.activate(language)

def deactivate():
    return _trans.deactivate()

class override(object):
    def __init__(self, language, deactivate=False):
        self.language = language
        self.deactivate = deactivate
        self.old_language = get_language()

    def __enter__(self):
        if self.language is not None:
            activate(self.language)
        else:
            deactivate_all()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.deactivate:
            deactivate()
        else:
            activate(self.old_language)

def get_language():
    return _trans.get_language()

def get_language_bidi():
    return _trans.get_language_bidi()

def check_for_language(lang_code):
    return _trans.check_for_language(lang_code)

def to_locale(language):
    return _trans.to_locale(language)

def get_language_from_request(request, check_path=False):
    return _trans.get_language_from_request(request, check_path)

def get_language_from_path(path):
    return _trans.get_language_from_path(path)

def templatize(src, origin=None):
    return _trans.templatize(src, origin)

def deactivate_all():
    return _trans.deactivate_all()

def _string_concat(*strings):
    """
    Lazy variant of string concatenation, needed for translations that are
    constructed from multiple parts.
    """
    return ''.join([force_text(s) for s in strings])
string_concat = lazy(_string_concat, six.text_type)

def get_language_info(lang_code):
    from django.conf.locale import LANG_INFO
    try:
        return LANG_INFO[lang_code]
    except KeyError:
        raise KeyError("Unknown language code %r." % lang_code)
