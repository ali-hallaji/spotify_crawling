from cerberus import Validator


pi_schema = {
    'next': {
        'type': 'string',
        'required': False,
        'empty': True,
        'nullable': True
    }
}

p_schema = {
    'playlists': {
        'type': 'dict',
        'required': True,
        'empty': False,
        'nullable': False,
        'schema': pi_schema
    }
}
