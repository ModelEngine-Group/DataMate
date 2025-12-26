from . import data_juicer_wrapper, datamate_wrapper

WRAPPERS = {
    "ray": data_juicer_wrapper,
    "default": data_juicer_wrapper,
    "datamate": datamate_wrapper
}
