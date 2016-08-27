# Copyright (c) 2016 Manuel Silva
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# -*- coding: utf-8 -*-

import sys
import urlparse, urllib, urllib2, json
import xbmcgui, xbmcplugin, xbmcaddon

addonID      = 'plugin.audio.optimusdiscos'
ADDON        = xbmcaddon.Addon(id=addonID)
addon_handle = int(sys.argv[1])
icon         = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')

cache = None
try:
    import StorageServer
    cache = StorageServer.StorageServer('optimusdiscos_playlist', ADDON.getSetting('optimus_playlist_cache_duration') )
except:
    cache = None

def build_url(query):
    base_url = sys.argv[0]
    return base_url + '?' + urllib.urlencode(query)

def load_playlist( pl_url ):
    retjson  = {}

    request  = urllib2.Request( pl_url )
    response = None

    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        xbmc.executebuiltin( 'Notification("' + ADDON.getAddonInfo('name') + '", "Failed to load data (status ' + str(e) + ')", 5000, "' + icon + '")')
        response = None
    if ( not( response ) ):
        return retjson

    try:
        retjson = json.loads( response.read() )
        if ( ( 'tracks' not in retjson ) or ( 'albums' not in retjson ) ):
            raise ValueError('Obtained JSON fails format')
    except:
        xbmc.executebuiltin( 'Notification("' + ADDON.getAddonInfo('name') + '", "Invalid data format", 5000, "' + icon + '")')
        retjson = {}
        return retjson

    songs_by_record = {}
    for elem in retjson['tracks']:
        album_id = str( elem['album_id'] )
        if ( album_id not in songs_by_record ):
            songs_by_record[ album_id ] = []

        songs_by_record[ album_id ].append( elem )

    record_info = {}
    albums = []
    for elem in retjson['albums']:
        album_id = str( elem['album_id'] )
        albums.append( album_id )
        elem['__tracklist'] = songs_by_record[ album_id ]
        record_info[ album_id ] = elem

    return { 'album_ids': albums, 'album_details': record_info }

db = cache.cacheFunction( load_playlist, ADDON.getSetting('optimus_playlist_url') ) if cache else load_playlist( ADDON.getSetting('optimus_playlist_url') );

if ( not db ):
    exit( 200 )

args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

if mode is None:
    album_ids = db['album_ids']
    for elem in album_ids:
        album = db['album_details'][elem]
	url = build_url({'mode': 'folder', 'foldername': elem})
	li = xbmcgui.ListItem(album['artist'] + ' - ' + album['album'], iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
    album_id = args['foldername'][0]
    for elem in db['album_details'][album_id]['__tracklist']:
        url = elem['track']
        li = xbmcgui.ListItem(elem['name'], iconImage='DefaultAudio.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
