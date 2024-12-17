# -*- coding: utf-8 -*-
import json
import requests
from modules import settings
from caches.lists_cache import lists_cache_object
from modules.utils import remove_accents, replace_html_codes

mdblist_api_key = settings.mdblist_api_key()
API_ENDPOINT = 'https://api.mdblist.com/%s'
timeout = 20

def check_mdblist_api_key():
	"""
	Check if MDBList API key is set.
	:return: Result web request
	"""
	res = call_mdblist('lists/top',  {'apikey': mdblist_api_key})
	return res

def mdblist_list_items(id):
	"""
	Fetch list items from MDBList.
	:param id: The MDBList list ID
	:return: A list of items in the list. If no API key is found, returns an empty object ({}).
	"""
	if not mdblist_api_key:
		return []
	string = 'mdblist_list_items_%s' % (id)
	params = {
		'path': 'lists/%s/items' % id,
		'params': {'apikey': mdblist_api_key}
	}
	return lists_cache_object(get_mdblist, string, params)

def mdblist_top_lists():
	"""
	Fetch top lists from MDBList.
	:return: A list of top lists. If no API key is found, returns an empty object ({}).
	"""
	if not mdblist_api_key:
		return []
	string = 'mdblist_top_lists_%s' % mdblist_api_key
	params = {
		'path': 'lists/top',
		'params': {'apikey': mdblist_api_key}
	}
	return lists_cache_object(get_mdblist, string, params)

def mdblist_my_lists():
	"""
	Fetch a user's lists from MDBList.
	:param user_id: The MDBList user ID or username
	:return: A list of the user's custom lists. If no API key is found, returns an empty object ({}).
	"""
	if not mdblist_api_key:
		return []
	string = 'mdblist_my_lists_%s' % ( mdblist_api_key)
	params = {
		'path': 'lists/user',
		'params': {'apikey': mdblist_api_key}
	}
	return lists_cache_object(get_mdblist, string, params)

def get_mdblist(params):
	"""
	Helper function to process MDBList API requests and clean results.
	"""
	result = call_mdblist(params['path'], params=params.get('params', {}))
	return _clean_mdblist_results(result)

def call_mdblist(path, params=None):
	if params is None:
		params = {}
	try:
		url = API_ENDPOINT % path
		response = requests.get(url, timeout=timeout, params=params)
		data = response.json()
	except:
		data = []
	return data

def _clean_mdblist_results(results):
    if isinstance(results, dict):
        cleaned = {}
        for k, v in results.items():
            cleaned[k] = _clean_mdblist_results(v)
        return cleaned
    elif isinstance(results, list):
        cleaned = []
        for item in results:
            cleaned.append(_clean_mdblist_results(item))
        return cleaned
    elif isinstance(results, str):
        return remove_accents(replace_html_codes(results))
    else:
        return results
