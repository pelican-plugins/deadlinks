# Dead Links

This plugin scans for links and checks status code of requested url.
For responses such as 403 or 404, the plugin adds a "disabled" class
to the anchor, extends anchor with a span label and dumps warning to
the logger.


# Requirements

BeautifulSoup4

# Installation

Clone repository somewhere (let's assume destination is ./plugins/custom/deadlinks)
and edit configuration file:

```python
    PLUGINS_PATH = [
        # [...]
        'plugins/custom'
    ]
    PLUGINS = [
         # [...]
        'deadlinks'
    ]
```

# Settings

To enable dead link checker, set the `DEADLINK_VALIDATION` option in your
Pelican configuration file to True.

Additionally following options might be changed:

```python
    DEADLINK_OPTS = {
        'archive':  True,
        'classes': ['custom-class1', 'disabled'],
        'labels':   True
    }
```

Options:

| Name | Description | Default value |
| ------ | ----------- | ------------- |
| `archive` | True/False. When enabled invalid links will be replaced with proper archive.org entry | True |
| `classes` | List of classes to be add to anchor element | Empty list |
| `labels` | Insert bootstrap's label after the anchor element | False |

