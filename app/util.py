# util.py

import json
from datetime import datetime, date

class DateTimeEncoder(json.JSONEncoder):
    """JSON Encoder that converts datetime/date to ISO strings."""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def iso_datetime_object_hook(obj):
    """
    object_hook for json.loads. Converts ISO date and datetime strings
    back into datetime or date objects where possible.
    """
    for key, value in obj.items():
        if isinstance(value, str):
            # Try to parse datetime (with time information)
            try:
                obj[key] = datetime.fromisoformat(value)
                continue
            except ValueError:
                pass
            # Try to parse date (no time)
            try:
                obj[key] = date.fromisoformat(value)
            except ValueError:
                pass
    return obj

def json_dumps(data, **kwargs):
    """
    Dumps data to JSON, handling datetime and date objects automatically.
    Additional kwargs are passed to json.dumps.
    """
    return json.dumps(data, cls=DateTimeEncoder, **kwargs)

def json_loads(s, **kwargs):
    """
    Loads JSON string, converting ISO date and datetime strings to objects.
    Additional kwargs are passed to json.loads.
    """
    return json.loads(s, object_hook=iso_datetime_object_hook, **kwargs)
