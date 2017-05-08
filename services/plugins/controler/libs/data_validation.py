from cerberus import Validator

p_schema = {
        'playlists': {
            'type': 'dict',
            'required': True,
            'empty': False,
            'nullable': False,
            'schema': item
        }
}
pi_schema = {
        'next': {
            'type': 'string',
            'required': False,
            'empty': True,
            'nullable': True
        }
}
