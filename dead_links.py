# -*- coding: utf8 -*-

import logging
import urllib
from bs4 import BeautifulSoup
from pelican import signals

logger = logging.getLogger("dead_links")

DEFAULT_OPTS = {
    'disable_anchors': True,
    'add_labels': True,
}


def get_status_code(url):
    """
    Open connection to the given url and check status code.

    :param url: URL of the website to be checked
    :return: (availibility, success, HTTP code)
    """
    try:
        conn = urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        out = (True, False, e.code)
    except urllib.error.URLError as e:
        out = (False, False, None)
    else:
        out = (True, True, 200)
    return out

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


def content_object_init(instance):
    """
    Pelican callback
    """
    if instance._content is None:
        return
    if not user_enabled(instance, 'DEADLINK_VALIDATION'):
        logger.debug("Configured not to validate dead links")
        return

    opts = instance.settings['DEADLINK_OPTS'] if user_enabled(instance, 'DEADLINK_OPTS') else {}
    allowed_to_disable_anchors = get_opt(opts, 'disable_anchors')
    allowed_to_add_labels = get_opt(opts, 'add_labels')

    cache = {}

    content = instance._content
    soup_doc = BeautifulSoup(content, 'html.parser')

    for anchor in soup_doc(['a', 'object']):
        if not 'href' in anchor.attrs:
            continue
        if not anchor['href'].startswith('http'):
            continue

        url = anchor['href']
        if url in cache:
            avail, success, code = cache[url]
        else:
            avail, success, code = get_status_code(url)
            cache[url] = (avail, success, code)

        if not avail:
            logger.warn('Dead link: %s (not available)', url)
            if allowed_to_disable_anchors:
                anchor['class'] = anchor.get('class', []) + ['disabled']
            if allowed_to_add_labels:
                soup_span = BeautifulSoup('<span class="label label-error"></span>', 'html.parser') 
                soup_span.span.append('not available')
                anchor.append(" ")
                anchor.append(soup_span.span)
            continue
        elif not success:
            if code >= 400 and code < 500:
                logger.warn('Dead link: %s (error code: %d)', url, code)
                if allowed_to_disable_anchors:
                    anchor['class'] = anchor.get('class', []) + ['disabled']
                if allowed_to_add_labels:
                    soup_span = BeautifulSoup('<span class="label label-warning"></span>', 'html.parser') 
                    soup_span.span.append('%d' % (code, ))
                    anchor.append(" ")
                    anchor.append(soup_span.span)
                continue
        else:
            code = 200

        # Error codes from out of range [400, 500) are considered good too
        logger.debug('Good link: %s (%d)', url, code)

    instance._content = soup_doc.decode()


def register():
    """
    Part of Pelican API
    """
    signals.content_object_init.connect(content_object_init)
