from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import os.path

CONFIGURATION_DIRECTORY = '~/etc/'


class _ConfigurationFileSystemEventHandler(FileSystemEventHandler):

    def __init__(self):
        self.configurationObservers = dict()
        super(_ConfigurationFileSystemEventHandler, self).__init__()

    def register_observer(self, configuration_file, observer, call=False):
        self.configurationObservers[configuration_file] = observer
        if call:
            src_path = os.path.join(
                CONFIGURATION_DIRECTORY, configuration_file)
            observer(src_path)

    def _callObserver(self, event):
        filename = os.path.basename(event.src_path)
        observer = self.configurationObservers.get(filename, None)
        if observer is not None:
            observer(event.src_path)

    def on_modified(self, event):
        self._callObserver(event)

    def on_created(self, event):
        self._callObserver(event)

_file_handler = _ConfigurationFileSystemEventHandler()
_observer = Observer()
_observer.schedule(
    _file_handler, path=CONFIGURATION_DIRECTORY, recursive=False)
_observer.start()


def register_observer(configuration_file, observer):
    _file_handler.register_observer(configuration_file, observer)
