from PySide2.QtCore import Signal, QThread, Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QVBoxLayout, QProgressBar, QLabel, QDialog

from globals import config
from qdarkstyle import load_stylesheet as load_darkstyle


class _Worker(QThread):
    finished = Signal()
    incrfil = Signal()
    incrfol = Signal()

    def __init__(self, fn):
        super().__init__()
        self.func = fn

    def run(self):
        self.func(self)
        self.finished.emit()

class _PopUP(QDialog):
    def __init__(self, title, label, func):
        super().__init__()
        if config["darkTheme"] == "True":
            self.setStyleSheet(load_darkstyle())
        self.setWindowTitle(title)
        self.setGeometry(1920 // 2 - 150, 1080 // 2 - 25, 300, 50)
        # self.setWindowIcon(QIcon(ICON))
        self.Label = QLabel(label)
        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(0)
        layout = QVBoxLayout()
        layout.addWidget(self.Label)
        layout.addWidget(self.progressbar)
        self.setLayout(layout)
        self.func = func
        self.nfiles, self.nfolders = 0, 0

    def start_func(self):
        self.worker = _Worker(self.func)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(lambda: self.close())
        self.worker.incrfol.connect(self.increasefolders)

        self.worker.incrfil.connect(self.increasefiles)
        self.worker.start()

    def changeText(self):
        self.Label.setText("Files found: {0}\nFolders found: {1}".format(self.nfiles, self.nfolders))

    def increasefolders(self):
        self.nfolders += 1
        self.changeText()

    def increasefiles(self):
        self.nfiles += 1
        self.changeText()


def ProgressDialog(title, text, func):
    app = QApplication.instance()
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    window = _PopUP(title, text, func)
    window.show()
    window.start_func()

