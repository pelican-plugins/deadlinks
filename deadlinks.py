# -*- coding: utf8 -*-

import logging
from bs4 import BeautifulSoup
from pelican import signals
import requests
from requests.exceptions import Timeout, RequestException


log = logging.getLogger(__name__)

UNKNOWN = None
MS_IN_SECOND = 1000.0

DEFAULT_OPTS = {
    'archive':  True,
    'classes':  [],
    'labels':   False,
    'timeout_duration_ms': 1000,
    'timeout_is_error':    False,
}

SPAN_WARNING = u'<span class="label label-warning"></span>'
SPAN_DANGER = u'<span class="label label-danger"></span>'
ARCHIVE_URL = u'http://web.archive.org/web/*/{url}'


def get_status_code(url, opts):
    """
    Open connection to the given url and check status code.

    :param url: URL of the website to be checked
    :return: (availibility, success, HTTP code)
    """
    availibility, success, code = (False, False, None)
    timeout_duration_seconds = get_opt(opts, 'timeout_duration_ms') / MS_IN_SECOND
    try:
        r = requests.get(url, timeout=timeout_duration_seconds)
        code = r.status_code
        availibility = True
        success = code == requests.codes.ok
    except Timeout:
        availibility = False
        success = UNKNOWN
    except RequestException:
        availibility = UNKNOWN
        success = False
    return (availibility, success, code)


def user_enabled(inst, opt):
    """
    Check whether the option is enabled.

    :param inst: instance from content object init
    :param url: Option to be checked
    :return: True if enabled, False if disabled or non present
    """
    return opt in inst.settings and inst.settings[opt]


def get_opt(opts, name):
    """
    Get value of the given option

    :param opts:    Table with options
    :param name:    Name of option
    :return:        Option of a given name from given table or default value
    """
    return opts[name] if name in opts else DEFAULT_OPTS[name]


def add_class(node, name):
    """
    Add class value to a given tag

    :param node:    HTML tag
    :param name:    class attribute value to add
    """
    node['class'] = node.get('class', []) + [name, ]


def change_to_archive(anchor):
    """
    Modify href attribute to point to archive.org instead of url directly.
    """
    src = anchor['href']
    dst = ARCHIVE_URL.format(url=src)
    anchor['href'] = dst


def on_connection_error(anchor, opts):
    """
    Called on connection error (URLError being thrown)

    :param anchor:  Anchor element (<a/>)
    :param opts:    Dict with user options
    """
    classes = get_opt(opts, 'classes')
    for cls in classes:
        add_class(anchor, cls)
    labels = get_opt(opts, 'labels')
    if labels:
        soup = BeautifulSoup(SPAN_DANGER, 'html.parser')
        soup.span.append('not available')
        idx = anchor.parent.contents.index(anchor) + 1
        anchor.parent.insert(idx, soup)
    archive = get_opt(opts, 'archive')
    if archive:
        change_to_archive(anchor)


def on_access_error(anchor, code, opts):
    """
    Called on access error (such as 403, 404)

    :param anchor:  Anchor element (<a/>)
    :param code:    Error code (403, 404, ...)
    :param opts:    Dict with user options
    """
    classes = get_opt(opts, 'classes')
    for cls in classes:
        add_class(anchor, cls)
    labels = get_opt(opts, 'labels')
    if labels:
        soup = BeautifulSoup(SPAN_WARNING, 'html.parser')
        soup.span.append(str(code))
        idx = anchor.parent.contents.index(anchor) + 1
        anchor.parent.insert(idx, soup)
    archive = get_opt(opts, 'archive')
    if archive:
        change_to_archive(anchor)


def content_object_init(instance):
    """
    Pelican callback
    """
    if instance._content is None:
        return
    if not user_enabled(instance, 'DEADLINK_VALIDATION'):
        log.debug("Configured not to validate links")
        return

    settings = instance.settings
    siteurl = settings.get('SITEURL', '')
    opts = settings.get('DEADLINK_OPTS', DEFAULT_OPTS)

    cache = {}
    soup_doc = BeautifulSoup(instance._content, 'html.parser')

    for anchor in soup_doc(['a', 'object']):
        if 'href' not in anchor.attrs:
            continue
        url = anchor['href']

        # local files and other links are not really intresting
        if not url.startswith('http'):
            continue

        # Previous case works also for debugging environment (with SITEURL
        # being empty) This case resolves publish environment with all links
        # starting with http.
        if siteurl and url.startswith(siteurl):
            log.info("Url %s skipped because is starts with %s", url, siteurl)
            continue

        # No reason to query for the same link again
        if url in cache:
            avail, success, code = cache[url]
        else:
            # TODO: No reason to query for sites from already timed-out domain
            avail, success, code = get_status_code(url, opts)
            cache[url] = (avail, success, code)

        if not avail:
            timeout_is_error = get_opt(opts, 'timeout_is_error')
            if timeout_is_error:
                log.warning('Dead link: %s (not available)', url)
                on_connection_error(anchor, opts)
            else:
                log.warning('Skipping: %s (not available)', url)
            continue

        elif not success:
            if code >= 400 and code < 500:
                log.warning('Dead link: %s (error code: %d)', url, code)
                on_access_error(anchor, code, opts)
                continue
            else:
                # Codes other than [400, 500) are ignored
                pass

        # Error codes from out of range [400, 500) are considered good too
        log.debug('Good link: %s (%d)', url, code)

    instance._content = soup_doc.decode()


def register():
    """
    Part of Pelican API
    """
    signals.content_object_init.connect(content_object_init)
