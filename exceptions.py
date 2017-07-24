import logging


# base class of API exceptions 
class APIError(Exception):
    def __init__(self, e, data = None, message = ''):
        super(APIError,self).__init__(message)
        self.error = e
        self.data = data
        self.message = message

class APIValueError(APIError):
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('Invalid API Value', field, message)

class APINotFountError(APIError):
    def __init__(self, field, message=''):
        super(APIValueError, self).__init__('API Not Found', field, message)

class APIPermissionError(APIError):
    def __init__(self,  message=''):
        super(APIValueError, self).__init__('Permission Denied', 'permission', message)