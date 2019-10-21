#!/usr/bin/env python
# -*- coding: utf-8 -*-

# base_api = "http://stage.pep.gvpi.net/api"
base_api = "http://127.0.0.1:9100"

def base_plus_endpoint_encoded(endpoint):
    ret_val = base_api + endpoint
    return ret_val


