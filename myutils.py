import logging

# Merge the "new_values" dictionary recursively into the "base_values" dictionary,
# assigning where new_values is assigned but not fully overwriting nested dictionaries
# (hence recursive)
def merge_dictionary(new_values, base_values):
    for key in new_values:
        if key in base_values and isinstance(base_values[key], dict) and isinstance(new_values[key], dict):
            merge_dictionary(new_values[key], base_values[key])
        else:
            base_values[key] = new_values[key]

# Set the DEFAULT logging level based on a string representation of it
def set_logging_level(level_str):
    level = getattr(logging, level_str.upper(), None)
    if not isinstance(level, int):
        raise ValueError('Invalid logging level: %s' % level_str)
    logging.basicConfig(level=level)