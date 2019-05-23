"""Utility functions, decorators and classes"""


def autolabel(dropdown):
    """Automatically set Dropdown label on_click"""
    def callback(value):
        for label, _value in dropdown.menu:
            if value == _value:
                dropdown.label = label
    dropdown.on_click(callback)
    return callback
