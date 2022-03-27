"""
This library contains the classes and functions related to the watchdog file watcher.
"""

import time
import os

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from app import instances, functions
from app import models
from app.lib import albumslib
from app import api
from app.lib import folderslib


class OnMyWatch:
    """
    Contains the methods for initializing and starting watchdog.
    """

    directory = os.path.expanduser("~")

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.directory, recursive=True)
        self.observer.start()

        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


def add_track(filepath: str) -> None:
    """
    Processes the audio tags for a given file ands add them to the music dict.

    Then creates a folder object for the added track and adds it to api.FOLDERS
    """
    tags = functions.get_tags(filepath)

    if tags is not None:
        instances.songs_instance.insert_song(tags)
        tags = instances.songs_instance.get_song_by_path(tags["filepath"])

        api.PRE_TRACKS.append(tags)
        album = albumslib.create_album(tags)
        api.ALBUMS.append(album)

        tags["image"] = album.image
        api.TRACKS.append(models.Track(tags))

        folder = folderslib.create_folder(tags["folder"])

        if folder not in api.FOLDERS:
            api.FOLDERS.append(folder)


def remove_track(filepath: str) -> None:
    """
    Removes a track from the music dict.
    """
    print(filepath)
    try:
        trackid = instances.songs_instance.get_song_by_path(filepath)["_id"]["$oid"]
    except TypeError:
        return

    instances.songs_instance.remove_song_by_id(trackid)

    for track in api.TRACKS:
        if track.trackid == trackid:
            api.TRACKS.remove(track)


class Handler(PatternMatchingEventHandler):
    files_to_process = []

    def __init__(self):
        print("💠 started watchdog 💠")
        PatternMatchingEventHandler.__init__(
            self,
            patterns=["*.flac", "*.mp3"],
            ignore_directories=True,
            case_sensitive=False,
        )

    def on_created(self, event):
        """
        Fired when a supported file is created.
        """
        print("🔵 created +++")
        self.files_to_process.append(event.src_path)

    def on_deleted(self, event):
        """
        Fired when a delete event occurs on a supported file.
        """
        print("🔴 deleted ---")
        remove_track(event.src_path)

    def on_moved(self, event):
        """
        Fired when a move event occurs on a supported file.
        """
        print("🔘 moved -->")
        tr = "share/Trash"

        if tr in event.dest_path:
            print("trash ++")
            remove_track(event.src_path)

        elif tr in event.src_path:
            add_track(event.dest_path)

        elif tr not in event.dest_path and tr not in event.src_path:
            add_track(event.dest_path)
            remove_track(event.src_path)

    def on_closed(self, event):
        """
        Fired when a created file is closed.
        """
        print("⚫ closed ~~~")
        self.files_to_process.remove(event.src_path)
        add_track(event.src_path)


watch = OnMyWatch()