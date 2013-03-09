'''
To do:
- When it happens, log it
- just... Something!


@author: ozbolt
'''

class ResourceBusy(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class ResourceUnavaliable(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class ResourceEmpty(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
