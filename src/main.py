from common import *

class KP:
    @staticmethod
    def run():
        KP.app = QtWidgets.QApplication(sys.argv)

        KP.app.settings = QtCore.QSettings('Koopatlas', 'Newer Team')

        from mapdata import KPMap
        KP.map = KPMap()

        from ui import KPMainWindow

        KP.mainWindow = KPMainWindow()
        KP.mainWindow.show()

        KP.enumerateTilesets()

        KP.app.exec_()


    @classmethod
    def icon(cls, name):
        try:
            cache = cls.iconCache
        except AttributeError:
            cache = {}
            cls.iconCache = cache

        try:
            return cache[name]
        except KeyError:
            icon = QtGui.QIcon('Resources/%s.png' % name)
            cache[name] = icon
            return icon


    @classmethod
    def enumerateTilesets(cls):
        try:
            registry = cls.knownTilesets
        except AttributeError:
            registry = {}
            cls.knownTilesets = registry
            cls.loadedTilesets = {}

        path = os.path.join(os.getcwd(), 'Tilesets')
        if not os.path.exists(path):
            os.mkdir(path)

        foundAnyTilesets = False
        for file in os.listdir(path):
            name = file[:-4]

            if file.endswith('.arc'):
                foundAnyTilesets = True
                filepath = os.path.join(path, file)
                registry[name] = {'path': filepath}

        if not foundAnyTilesets:
            QtWidgets.QMessageBox.warning(None, 'Warning', "Your Tilesets folder seems to be empty. You won't be able to load any world maps without them! You can get Newer Wii's world map and tileset files at <a href=\"https://github.com/Newer-Team/NewerSMBW/tree/no-translations/NewerResources\">https://github.com/Newer-Team/NewerSMBW/tree/no-translations/NewerResources</a>.")


    @classmethod
    def loadTileset(cls, name):
        from hashlib import sha256 as sha

        if name in cls.loadedTilesets:
            return True

        if name not in cls.knownTilesets:
            QtWidgets.QMessageBox.critical(None, 'Error', "Could not find the tileset \"%s\" in the Tilesets folder. Please put it there, restart Koopatlas, and try again." % name)
            return False

        filepath = cls.knownTilesets[name]['path']
        data = open(filepath, 'rb').read()

        tsInfo = cls.knownTilesets[name]
        newHash = sha(data).hexdigest()
        if 'hash' in tsInfo and tsInfo['hash'] == newHash:
            # file hasn't changed
            return True

        tsInfo['hash'] = newHash

        from tileset import KPTileset

        import time
        b = time.time()

        cls.loadedTilesets[name] = KPTileset.loadFromArc(data)

        e = time.time()
        print("Loading set: {0} in {1}".format(name, e-b))

        return True


    @classmethod
    def tileset(cls, name):
        cache = cls.loadedTilesets

        try:
            return cache[name]
        except KeyError:
            if cls.loadTileset(name):
                return cache[name]
            else:
                return None

