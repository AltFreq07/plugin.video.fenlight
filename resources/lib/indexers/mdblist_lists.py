# mdblist_lists.py
# -*- coding: utf-8 -*-

import sys
from indexers.movies import Movies
from indexers.tvshows import TVShows
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from modules import kodi_utils
from modules.utils import paginate_list
from modules.settings import paginate, page_limit
from apis import mdblist_api
add_dir = kodi_utils.add_dir
external = kodi_utils.external
sleep = kodi_utils.sleep
get_icon = kodi_utils.get_icon
mdblist_icon, set_property = get_icon('mdblist'), kodi_utils.set_property
fanart = kodi_utils.get_addon_fanart()
set_category, home, folder_path = kodi_utils.set_category, kodi_utils.home, kodi_utils.folder_path
set_content, set_sort_method, set_view_mode, end_directory = kodi_utils.set_content, kodi_utils.set_sort_method, kodi_utils.set_view_mode, kodi_utils.end_directory
make_listitem, build_url, add_items = kodi_utils.make_listitem, kodi_utils.build_url, kodi_utils.add_items
nextpage_landscape = kodi_utils.nextpage_landscape

def handle_mdblist_error(handle, lists):
    """
    Helper function to handle MDBList API errors.

    :param handle: Kodi handle
    :param lists: Response from MDBList API
    :return: True if error was handled, False otherwise
    """
    if isinstance(lists, dict):
        error_message = f'Error: {lists["detail"]}'
        error_listitem = make_listitem()
        error_listitem.setLabel(error_message)
        error_listitem.setArt({'icon': 'DefaultIconError.png', 'fanart': 'DefaultIconError.png'})
        add_items(handle, [(error_message, error_listitem, True)])
        end_directory(handle)
        return True
    return False

def process_lists(lists):
    for _list in lists:
        cm = []
        item_count = _list.get('items', 0)
        if item_count == 0: continue
        list_id = _list['id']
        list_name, user = _list['name'], _list.get('user_name', '')
        list_name_upper = list_name.upper()
        if not list_id: continue
        display = f'{list_name_upper} | [I]{user} (x{str(item_count)})[/I]'
        url = build_url({'mode': 'mdblist.list.build_mdblist', 'list_name': list_name,'id': list_id})
        listitem = make_listitem()
        listitem.addContextMenuItems(cm)
        listitem.setLabel(display)
        listitem.setArt({'icon': mdblist_icon, 'poster': mdblist_icon, 'thumb': mdblist_icon, 'fanart': fanart, 'banner': fanart})
        info_tag = listitem.getVideoInfoTag()
        info_tag.setPlot(' ')
        yield (url, listitem, True)


def get_mdblist_my_lists():
    """
    Fetches and displays MDBList user lists in Kodi using threading for efficient processing.
    
    :return: None
    :raises: Exception if there is an error fetching the lists.
    """

    handle = int(sys.argv[1])
    lists = mdblist_api.mdblist_my_lists()
    if handle_mdblist_error(handle, lists):
        return
    add_items(handle, list(process_lists(lists)))
    set_content(handle, 'files')
    set_category(handle, 'MDblist Lists')
    end_directory(handle)
    set_view_mode('view.main')

def get_mdblist_top_lists():

    """
    Fetches and displays MDBList top lists in Kodi using threading for efficient processing.
    
    :return: None
    :raises: Exception if there is an error fetching the lists.
    """

    handle = int(sys.argv[1])
    lists = mdblist_api.mdblist_top_lists()
    if handle_mdblist_error(handle, lists):
        return
    add_items(handle, list(process_lists(lists)))
    set_content(handle, 'files')
    set_category(handle, 'MDblist Lists')
    end_directory(handle)
    set_view_mode('view.main')



def build_mdblist(params):
    def _process(function, _list):
        item_list_extend(function(_list).worker())


    def _paginate_list(data, page_no, paginate_start):
        if use_result: total_pages = 1
        elif paginate_enabled:
            limit = page_limit(is_home)
            data, total_pages = paginate_list(data, page_no, limit, paginate_start)
            if is_home: paginate_start = limit
        else: total_pages = 1
        return data, total_pages, paginate_start
    handle = int(sys.argv[1])
    is_external = external()
    is_home = home()
    list_name = params.get('list_name')
    item_list = []
    item_list_extend = item_list.extend
    paginate_enabled = paginate(is_home)
    use_result = 'result' in params
    page_no, paginate_start = int(params.get('new_page', '1')), int(params.get('paginate_start', '0'))
    if page_no == 1 and not is_external: set_property('fenlight.exit_params', folder_path())
    if use_result: result = params.get('result', [])
    else:
        list_id = params.get('id')
        result = mdblist_api.mdblist_list_items(list_id)
    content = 'movies' if len(result.get('movies', [])) > len(result.get('shows', [])) else 'tvshows'
    result = result.get('movies', []) if len(result.get('movies', [])) > len(result.get('shows', [])) else result.get('shows')
    process_list, total_pages, paginate_start = _paginate_list(result, page_no, paginate_start)
    if content == 'movies':
        movie_list = {'list': [(i['rank'], {'tmdb': i.get('tmdb_id', ''), 'imdb': i.get('imdb_id', ''), 'tvdb': i.get('tvdb_id', '')}) for i in process_list], 'id_type': 'trakt_dict', 'custom_order': 'true'}
        with ThreadPoolExecutor(max_workers = min(cpu_count(), 8)) as executor:
            executor.submit(_process, Movies, movie_list)

    else:
        tvshow_list = {'list': [(i['rank'], {'tmdb': i.get('tmdb_id', ''), 'imdb': i.get('imdb_id', ''), 'tvdb': i.get('tvdb_id', '')}) for i in process_list], 'id_type': 'trakt_dict', 'custom_order': 'true'}
        with ThreadPoolExecutor(max_workers = min(cpu_count(), 8)) as executor:
            executor.submit(_process, TVShows, tvshow_list)

    item_list.sort(key=lambda k: k[1])
    if use_result: return [i[0] for i in item_list]
    add_items(handle, [i[0] for i in item_list])
    if total_pages > page_no:
        new_page = str(page_no + 1)
        new_params = {'mode': 'mdblist.list.build_mdblist', 'list_name': list_name, 'id': list_id, 'paginate_start': paginate_start, 'new_page': new_page}
        add_dir(new_params, f'Next Page ({new_page}) >>', handle, 'nextpage', nextpage_landscape)
    set_content(handle, content)
    set_category(handle, list_name)
    end_directory(handle, cacheToDisc=not is_external)
    if not is_external:
        if params.get('refreshed') == 'true':
            set_property('fenlight.refresh', 'true')
        set_view_mode(f'view.{content}', content, is_external)

