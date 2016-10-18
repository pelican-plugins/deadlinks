# Dead Links

This plugin scans for links and checks status code of requested url.
For responses such as 403 or 404, the plugin adds a "disabled" class
to the anchor, extends anchor with a span label and dumps warning to 
the logger.

# Installation

Edit configuration file:

:::python

    PLUGINS_PATH = [
        # [...]
        'path/to/dead_link_parent'
    ]
    PLUGINS = [
         # [...]
        'dead_link'
    ]

# Settings

To enable dead link checker, set the `DEADLINK_VALIDATE` option in your 
Pelican configuration file to True.

Additionally following options might be changed:

:::python

    DEADLINK_OPTS = {
        'disable_anchors': True,
        'add_labels': True,
    }
   
