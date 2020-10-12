```python
# For the following sets of routes:
'/'
'/health'
'/auth'
'/admin'
'/admin/users'

'/api/assets'
'/api/assets/{asset_id}'
'/api/assets/satellites/{asset_id}'
'/api/assets/antennae/{asset_id}'
'/api/assets/{asset_id}/{asset_component}'

'/api/calendar/{api_version}'
'/api/calendar/{api_version}/{sort_style}'
'/api/calendar/{api_version}/events'
'/api/calendar/{api_version}/events/{date}'
'/api/calendar/{api_version}/events/{date}/{sort_style}'


# These would be the lookup tables...
_static_lookup = {
    '/': bare_handler,
    '/health': health_handler,
    '/auth': auth_handler,
    '/admin': admin_handler,
    '/admin/users': users_handler,

    '/api/assets': asset_bare_handler,
}


_dynamic_lookup = {
    'api': {
        'assets': {
            CAPTURE_SEGMENT: {
                # '/api/assets/{asset_id}'
                TERMINATOR: asset_id_handler,

                CAPTURE_SEGMENT: {
                    # '/api/assets/{asset_id}/{asset_component}'
                    TERMINATOR: asset_component_handler
                }
            },

            'satellites': {
                CAPTURE_SEGMENT: {
                    # '/api/assets/satellites/{asset_id}'
                    TERMINATOR: satellites_handler
                }
            },

            'antennae': {
                CAPTURE_SEGMENT: {
                    # '/api/assets/antennae/{asset_id}'
                    TERMINATOR: antennae_handler
                }
            },
        },

        'calendar': {
            CAPTURE_SEGMENT: {
                # '/api/calendar/{api_version}'
                TERMINATOR: calendar_handler,
                CAPTURE_SEGMENT: {
                    # '/api/calendar/{api_version}/{sort_style}'
                    TERMINATOR: calendar_sorted_handler,
                },
                'events': {
                    # '/api/calendar/{api_version}/events'
                    TERMINATOR: event_handler,
                    CAPTURE_SEGMENT: {
                        # '/api/calendar/{api_version}/events/{date}'
                        TERMINATOR: event_date_handler,
                        CAPTURE_SEGMENT: {
                            # '/api/calendar/{api_version}/events/{date}/{sort_style}'
                            TERMINATOR: event_date_sorted_handler
                        }
                    }
                }
            }
        }
    }
}
```
