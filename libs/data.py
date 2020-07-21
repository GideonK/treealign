#!/usr/bin/python3

import re, sys

class Dicts:
    def get_values_if_any(self, dict, key):
        return dict.get(key, [])
