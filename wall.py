#! /usr/bin/python

"""
Usage: python wall.py [OPTIONS] TAGS

OPTIONS:
  -q query or --query query

TAGS is a space delimited list of tags

Wallpaper changer for Ubuntu that downloads wallpapers from wallgig through a Mashape api.
You can chouse a set of wallpapers 
A Mashape authorization key is required.

Tested for Ubuntu 14.04 - Gnome 3

Requires:
 - unirest, install from pip
 - appindicator, install from pip
"""

import urllib, urllib2, urlparse
import os
import sys
import random

import unirest
import json

import gtk
import appindicator

from getopt import getopt, GetoptError

__author__ = "Simone Fisicaro <simonefisicaro@gmail.com>"
__version__ = "0.1"
__date__ = "15-05-2014"

#set wallpaper import - only works without gtk, appindicator
#from gi.repository import Gtk, Gio

#set your screen size
width = 1366
height = 768

ufile = "wallpaper_urls.txt"
wfile = "wallpaper.jpg"
tfile = "wallpaper.tmp"
mashape_key = "Insert-your-api-key"

SCHEMA = 'org.gnome.desktop.background'
KEY = 'picture-uri'

class Wallpy:

    def __init__(self, q, t):

        self.query = q
        self.tags = t

        self.ind = appindicator.Indicator("Wallp", "indicator-messages", appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_icon("distributor-logo")

        self.menu_setup()
        self.ind.set_menu(self.menu)

        self.filemanage = FileManager(ufile, wfile, tfile)

    def main(self):
        gtk.main()
        return 0

    def menu_setup(self):
        self.menu = gtk.Menu()

        self.name = gtk.MenuItem("Wallpy")
        self.name.set_sensitive(False)
        self.name.show()
        self.menu.append(self.name)

        self.new_wallp = gtk.MenuItem("A new wallp?")
        self.new_wallp.connect("activate", self.on_new_wallp_clicked)
        self.new_wallp.show()
        self.menu.append(self.new_wallp)

        self.status = gtk.MenuItem("")        
        self.status.set_sensitive(False)
        self.status.show()
        self.menu.append(self.status)

        self.quit_item = gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)

    def quit(self, widget):
        sys.exit(0)

    def on_new_wallp_clicked(self, widget):
        self.new_wallp.set_sensitive(False)

        check = self.get_wallpgig()
        if check == 1:
            self.load_wallp()
        else:
            self.status.set_label(check)

        self.new_wallp.set_sensitive(True)

    def load_wallp(self):
        temp = open(tfile, 'r')
        wallp = open(wfile, 'w')

        wallp.write(temp.read())

        temp.close()
        wallp.close()
        os.remove(tfile)

        #this solution does not work if I import appindicator and gtk
        #gsettings = Gio.Settings.new(self.SCHEMA)
        #background = os.path.dirname(os.path.abspath(__file__)) + '/' + wfile
        #gsettings.set_string(self.KEY, "file://" + background)

        background = "file://" + os.path.dirname(os.path.abspath(__file__)) + '/' + wfile
        cmd = "gsettings set org.gnome.desktop.background picture-uri " + background
        os.system(cmd)

        #solution for gnome 2
        #gconftool-2 --type=string --set /desktop/gnome/background/picture_filename" + background

        self.status.set_label("Complete.")

    #get wallpaper from wallgig
    def get_wallpgig(self):
        if not self.check_connection():
            return "No internet connection!"

        tags_from_file = self.filemanage.file_get_tags()
        query_from_file = self.filemanage.file_get_query()
        if (set(tags_from_file) == set(self.tags)) & (query_from_file == self.query):
            self.status.set_label("Loading urls...")
            urls = self.filemanage.file_get_urls()
            self.status.set_label("Urls loaded.")
        else:
            self.status.set_label("Downloading urls...")
            urls = self.download_urls()
            self.status.set_label("Urls downloaded.")

        random.shuffle(urls)

        try:
            url = urls[0]
            urllib.urlretrieve(url, tfile)
            urllib.urlcleanup()

            check = 1
        except IndexError:
            check = "No photos for this tags!"
        except urllib2.URLError:
            check = "No internet connection!"

        return check

    def download_urls(self):
        if not self.check_connection():
            return []

        t = ""
        for tag in self.tags:
            t += "&tags[]=" + tag

        try:
            response = unirest.get("https://wallgig-v1.p.mashape.com/wallpapers?q=" + self.query + "&width=" + str(width) + "&height=" + str(height) + "" + t,
                headers={"X-Mashape-Authorization": mashape_key});
        except urllib2.URLError:
            return []

        j = json.loads(response.raw_body)

        wallpapers = j["wallpapers"]
        urls = []
        for w in wallpapers:
            image = w['image']
            original = image['original']
            urls.append(original['url'])

        self.filemanage.file_save_urls(self.query, self.tags, urls)
        return urls

    def check_connection(self):
        try:
            urllib2.urlopen("http://www.google.com").close()
        except urllib2.URLError:
            return False
        else:
            return True

class FileManager:
    def __init__(self, u, w, t):
        self.ufile = u
        self.wfile = w
        self.tfile = t

    def file_save_urls(self, query, tags, urls):
        file = open(ufile, 'w')

        file.write(query + "\n")

        for tag in tags:
            file.write(tag + ' ')

        file.write("\n")

        for url in urls:
            file.write(url + "\n")

        file.close()

    def file_get_query(self):
        try:
            file = open(ufile, 'r')
        except IOError:
            return ""

        lines = file.readlines()

        q = ""
        if len(lines) >= 1:
            q = lines[0].replace('\n', '')

        file.close()
        return q

    def file_get_tags(self):
        try:
            file = open(ufile, 'r')
        except IOError:
            return []

        lines = file.readlines()

        tags = []
        if len(lines) >= 2:
            tags = lines[0].rstrip().split(' ')

        file.close()
        return tags

    def file_get_urls(self):
        file = open(ufile, 'r')

        lines = file.readlines()

        urls = []
        if len(lines) >= 3:
            tags = lines[0]
            for line in lines[1:]:
                urls.append(line.replace('\n', ''))
            pass

        file.close()
        return urls

def main(*argv):
    try:
        (opts, args) = getopt(argv[1:], 'q', ['query'])
    except GetoptError, e:
        print e
        print __doc__
        return 1

    query = ""
    tags = []

    for o, a in opts:
        if o in ('-q' '--query'):
            query = a
        else:
            print "Unknown argument: %s" % o
            print __doc__
            return 1

    tags = [item for item in args]

    indicator = Wallpy(query, tags)
    indicator.main()

if __name__ == '__main__':
    sys.exit(main(*sys.argv)) 
