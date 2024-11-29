import os
from os.path import join, abspath
import shutil
from subprocess import Popen

import pyperclip
from PySide2.QtCore import Qt, QThread, Signal, QSize
from PySide2.QtGui import QCursor, QPixmap, QIcon
from PySide2.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QAbstractItemView, QMenu, QAction, QMessageBox, QHeaderView, QPushButton
from qdarkstyle import load_stylesheet as load_darkstyle

from Utilities import *
from globals import *
from ProgressDialog import ProgressDialog

###############################################################################
class Worker(QThread):
    finished = Signal()
    done = Signal()

    def init(self, tableWidget, files, totalsize):
        self.tableWidget = tableWidget
        self.files = files
        self.totalsize = totalsize

    def run(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnWidth(0, self.tableWidget.width() / 4 * 3)
        self.tableWidget.setColumnWidth(2, self.tableWidget.width() / 4 - 80)
        # width = self.tableWidget.rowHeight(0)
        # print(width)
        # self.tableWidget.setItemDelegate(Delegate())
        n = 0
        for e in self.files:
            try:
                self.tableWidget.insertRow(n)
                item = QTableWidgetItem()
                item.setBackground(get_brush(e[1]/self.totalsize))
                if e[0].is_dir():
                    ext = ".?"
                else:
                    ext = e[0].suffix
                try:
                    item.setIcon(collected_icons[ext])
                except KeyError:
                    collected_icons[ext] = get_icon(str(e[0]))
                    item.setIcon(collected_icons[ext])
                item.setData(Qt.DisplayRole, e[0].name)
                item.setFlags(item.flags().__xor__(Qt.ItemIsEditable))
                self.tableWidget.setItem(n, 0, item)

                item = QTableWidgetItem()
                item.setData(Qt.DisplayRole, e[1])
                self.tableWidget.setItem(n, 1, item)

                item = QTableWidgetItem(convert_size(e[1]))
                item.setFlags(item.flags().__xor__(Qt.ItemIsEditable))
                item.setTextAlignment(Qt.AlignRight)
                self.tableWidget.setItem(n, 2, item)

                if not n:
                    self.tableWidget.selectRow(0)
                n += 1
            except FileNotFoundError:
                print(e.name, "Not Found", e)
        self.tableWidget.sortByColumn(1, Qt.DescendingOrder)
        self.finished.emit()
        self.done.emit()


def get_files_dir_size(path, files_lst, folders_lst, worker):
    tot_size = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                try:
                    size = os.path.getsize(entry.path)
                except OSError:
                    size = 0
                files_lst.append((Path(entry.path), size))
                worker.incrfil.emit()
                tot_size += size
            elif entry.is_dir():
                size = get_files_dir_size(entry.path, files_lst, folders_lst, worker)
                folders_lst.append((Path(entry.path), size))
                worker.incrfol.emit()
                tot_size += size
        return tot_size
    except PermissionError:
        return 0
    except FileNotFoundError:
        return 0


class MainWindow(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        loadUi("cleaner.ui", self)
        if config["darkTheme"] == "True":
            self.setStyleSheet(load_darkstyle())
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)
        self.setFixedSize(860, 612)
        self.actionSelect_Folder.triggered.connect(self.select_directory)
        self.actionOpen_Config_file.triggered.connect(open_config_file)
        self.openfolderButton.setIcon(QPixmap(r"resources\openfolder.png"))
        self.openexplorerButton.setIcon(QPixmap(r"resources\explorer.png"))
        self.openpropButton.setIcon(QPixmap(r"resources\info.png"))
        self.removeButton.setIcon(QPixmap(r"resources\cross.png"))
        self.refreshButton.setIcon(QPixmap(r"resources\refresh.png"))
        self.openfolderButton.clicked.connect(self.select_directory)
        self.openfolderButton.setToolTip('Open directory')
        self.openexplorerButton.clicked.connect(self.open_explorer)
        self.openexplorerButton.setToolTip('Open Explorer on file/folder')
        self.openpropButton.clicked.connect(self.open_properties)
        self.openpropButton.setToolTip('Open Properties on file/folder')
        self.removeButton.clicked.connect(self.remove_file)
        self.removeButton.setToolTip('Remove selected file')
        self.refreshButton.clicked.connect(self.confirm_refresh)
        self.refreshButton.setToolTip('Rescan all')
        self.softrefreshButton.clicked.connect(self.soft_rescan)
        self.softrefreshButton.setToolTip('Soft Rescan all')


        self.copypathButton.clicked.connect(self.copy_path)
        self.copypathButton.setToolTip('Copy path')
        self.copydirpathButton.clicked.connect(self.copy_dir_path)
        self.copydirpathButton.setToolTip('Copy path')
        self.changemodeButton.clicked.connect(self.change_mode)
        self.changemodeButton.setToolTip('Change mode')
        self.changemodeButton.setIconSize(QSize(16, 16))
        self.backButton.setIcon(QIcon("resources/return.png"))
        self.backButton.setIconSize(QSize(50, 16))
        self.backButton.setVisible(False)
        self.backButton.setToolTip('Return to parent folder')
        self.backButton.setStyleSheet("border-radius: 0px;")

        self.nameline.setReadOnly(True)
        self.nameline.setStyleSheet("border: 1px solid;")
        self.sizeline.setReadOnly(True)
        self.sizeline.setStyleSheet("border: 1px solid;")
        self.pathline.setReadOnly(True)
        self.pathline.setStyleSheet("border: 1px solid;")
        self.analyzedDir.setReadOnly(True)
        self.analyzedDir.setStyleSheet("border: 1px solid;")
        self.totalSize.setReadOnly(True)
        self.totalSize.setStyleSheet("border: 1px solid;")
        self.init_texts()

        self.tableWidget.horizontalHeader().setSortIndicatorShown(True)

        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tableWidget.insertColumn(0)
        self.tableWidget.insertColumn(1)
        self.tableWidget.insertColumn(2)
        self.tableWidget.setColumnHidden(1, True)
        self.tableWidget.setColumnWidth(0, self.tableWidget.width() / 4 * 3)
        self.tableWidget.setColumnWidth(2, self.tableWidget.width() / 4 - 5)
        self.tableWidget.setHorizontalHeaderLabels(("Name", "", "Size"))
        self.tableWidget.horizontalHeader().sectionClicked.connect(lambda i: self.sort_(i))
        self.tableWidget.selectionModel().selectionChanged.connect(self.selection_changed)

        # Cell menu
        self.cellmenu = QMenu(self)
        showinexplorerAction = QAction('Show in Explorer', self)
        showinexplorerAction.triggered.connect(self.open_explorer)
        openpropAction = QAction('Open Properties', self)
        openpropAction.triggered.connect(self.open_properties)
        copypathAction = QAction('Copy Path', self)
        copypathAction.triggered.connect(self.copy_path)

        self.cellmenu.addAction(showinexplorerAction)
        self.cellmenu.addAction(openpropAction)
        self.cellmenu.addAction(copypathAction)

        self.tableWidget.contextMenuEvent = self.contextMenuEvent

        self.mode = 0
        self.can_change_mode = False
        self.next_is_soft = False
        self.mode_str = ("File", "Folder")
        self.something_removed = False
        self.sort_info = (1, 1)
        self.maxFilesListed = int(config["maxFilesListed"])
        self.maxFoldersListed = int(config["maxFoldersListed"])
        self.confirmReloadOnSize = int(config["confirmReloadOnSize"])

        self.path = path
        if self.path:
            self.get_files()

    def init_texts(self):
        self.setWindowTitle("Pc Cleaner")
        self.nameline.setText("")
        self.sizeline.setText("")
        self.pathline.setText("")
        self.changemodeButton.setText("")
        self.labelSelected_actions.setText("Selected File actions:")

    def selection_changed(self, c):
        try:
            row = c.indexes()[0].row()
            p_file = self.now_list[row]
            self.now_selected = row
            self.nameline.setText(p_file[0].name)
            self.sizeline.setText(convert_size(p_file[1]))
            self.pathline.setText(str(p_file[0]))
        except IndexError:
            pass

    def sort_(self, idx):
        col = int(bool(idx))
        self.sort_info = (col, int(not (self.sort_info[1])) if self.sort_info[0] == col else col)
        self.tableWidget.sortByColumn(col, (Qt.AscendingOrder, Qt.DescendingOrder)[self.sort_info[1]])
        self.tableWidget.horizontalHeader().setSortIndicator(idx, (Qt.AscendingOrder, Qt.DescendingOrder)[self.sort_info[1]])

    def select_directory(self):
        self.setEnabled(False)
        self.path = select_directory()
        self.setEnabled(True)
        if self.path:
            self.setWindowTitle("Pc Cleaner - " + self.path.replace("/", "\\"))
            self.analyzedDir.setText(self.path.replace("/", "\\"))
            self.get_files()

    def done_listing(self):
        self.tableWidget.selectRow(0)
        self.tableWidget.setColumnWidth(0, self.tableWidget.width() / 4 * 3)
        self.tableWidget.setColumnWidth(2, self.tableWidget.width() / 4 - 80)
        self.setEnabled(True)

    def list_on_table(self):
        self.worker = Worker()
        self.worker.init(self.tableWidget, self.now_list, self.main_folder[1])
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.done.connect(self.done_listing)
        self.worker.start()

    def change_mode(self):
        print("change mode")
        if self.can_change_mode:
            self.mode = not self.mode
            if self.mode:
                self.now_list = self.folders
            else:
                self.now_list = self.files
            self.changemodeButton.setText(self.mode_str[self.mode])
            self.changemodeButton.setIcon(QIcon((r"resources\fileicon.png", r"resources\foldericon.png")[self.mode]))
            self.labelSelected_actions.setText("Selected " + self.mode_str[self.mode] + " actions:")
            if self.something_removed:
                self.refresh()
                self.something_removed = False
            else:
                self.list_on_table()
        elif not self.path:
            pass
        else:
            QMessageBox.critical(self, "Nothing found", "ERROR!\nThere are no " + self.mode_str[not self.mode] + "s in this folder", QMessageBox.Ok)

    def browse_back(self):
        self.path = self.path[:self.path.rfind("\\")]
        if self.path == self.scanned_path:
            self.backButton.setVisible(False)
        self.get_browse_page()
        self.list_on_table()

    def init_browse_mode(self):
        print("browser mode on")
        self.scanned_path = self.path.replace("/", "\\")
        self.path = self.scanned_path
        self.backButton.setVisible(False)
        self.backButton.clicked.connect(self.browse_back)
        self.tableWidget.doubleClicked.connect(self.browser_change_page)
        # print([e for e in dir(self.tableWidget) if "double" in e])
        self.mode = 2
        self.get_browse_page()
        self.list_on_table()

    def exit_browse_mode(self):
        print("browser mode off")

    def get_browse_page(self):
        # self.now_list = sorted(((Path(e), get_size_universal(e)) for e in (os.path.join(self.path, e) for e in os.listdir(str(self.path)))), key=lambda x: x[1], reverse=True)
        pth = str(self.path).replace("/", "\\")
        self.now_list = [e for e in self.orig_folders if str(e[0].parent) == pth]
        for e in self.orig_files:
            if str(e[0].parent) == pth:
                self.now_list.append(e)
        self.now_list.sort(key=lambda x: x[1], reverse=True)

    def browser_change_page(self):
        p_file = self.now_list[self.now_selected][0]
        if p_file.is_dir():
            self.path = str(p_file)
            if self.path != self.scanned_path:
                self.backButton.setVisible(True)
            self.get_browse_page()
            self.list_on_table()
        else:
            print("file clicked")

    def confirm_refresh(self):
        if self.main_folder[1] > self.confirmReloadOnSize:
            self.setEnabled(False)
            ret = QMessageBox.warning(self, "Confirm reload",
                                      "Are you sure to reload?\nAll files and folders will be scanned again\n(it will take some time, depending on the folder size)",
                                      QMessageBox.Yes | QMessageBox.No)
            self.setEnabled(True)
            if ret == QMessageBox.Yes:
                self.get_files()
        else:
            self.get_files()

    def soft_rescan(self):
        self.next_is_soft = True
        self.setEnabled(False)
        ProgressDialog("Scanning folder...", "Rescanning all files...\n", self.get_files_function)

    def get_files(self):
        if self.path:
            self.setEnabled(False)
            ProgressDialog("Scanning folder...", "Files found:\nFolders found:", self.get_files_function)

    def get_files_function(self, worker):        
        # self.orig_folders = sorted(((Path(x[0]), get_size(x[0], self.files, worker)) for x in os.walk(self.path)), key=lambda x: x[1], reverse=True)
        # self.orig_files = sorted(self.files, key=lambda x: x[1], reverse=True)

        if self.next_is_soft:
            self.next_is_soft = False
            self.orig_folders = [e for e in self.orig_folders if e[0].exists()]
            tmp = []
            for b in self.orig_files:
                if b[0].exists():
                    tmp.append(b)
                else:
                    self.main_folder[1] -= b[1]
            self.orig_files = tmp

        else:
            orig_folders, orig_files = [], []
            self.main_folder = [Path(self.path), get_files_dir_size(self.path, orig_files, orig_folders, worker)]
            orig_folders.sort(key=lambda x: x[1], reverse=True)
            orig_files.sort(key=lambda x: x[1], reverse=True)
            
            self.orig_folders = orig_folders
            self.orig_files = orig_files

        # self.main_folder = self.orig_folders.pop(0)
        self.folders = self.orig_folders[:self.maxFoldersListed]
        self.files = self.orig_files[:self.maxFilesListed]
        self.totalSize.setText(convert_size(self.main_folder[1]))

        if not (self.files or self.folders):
            self.can_change_mode = False
            self.init_texts()
            ret = QMessageBox.warning(self, "Nothing found", "This folder is empty.\nDo you want to select another folder?",
                                      QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.select_directory()
        else:
            if self.files:
                self.mode = 0
                self.now_list = self.files
            else:
                self.mode = 1
                self.now_list = self.folders
            self.list_on_table()
            if self.files and self.folders:
                self.can_change_mode = True
            self.changemodeButton.setText(self.mode_str[self.mode])
            self.changemodeButton.setIcon(QIcon((r"resources\fileicon.png", r"resources\foldericon.png")[self.mode]))
            self.labelSelected_actions.setText("Selected "+self.mode_str[self.mode]+" actions:")

    def contextMenuEvent(self, event):
        pos = event.pos()
        if 43 <= pos.x() <= 562 and 68 <= pos.y() <= min(68 + self.tableWidget.rowHeight(0) * self.tableWidget.rowCount(), 577):
            self.cellmenu.exec_(QCursor.pos())

    def refresh(self):
        to_rem = []
        for e in self.now_list:
            if not e[0].exists():
                to_rem.append(e)
        for e in to_rem:
            self.now_list.remove(e)
        self.list_on_table()

    def open_explorer(self):
        row = self.tableWidget.selectionModel().selectedRows()[0].row()
        Popen(r'explorer /select,' + str(self.now_list[row][0]).replace('/', '\\'))

    def open_properties(self):
        row = self.tableWidget.selectionModel().selectedRows()[0].row()
        open_prop(str(self.now_list[row][0]))

    def copy_path(self):
        # self.init_browse_mode()
        pyperclip.copy(str(self.pathline.text()))

    def copy_dir_path(self):
        pyperclip.copy(str(self.analyzedDir.text()))

    def remove_file(self):
        row = self.tableWidget.selectionModel().selectedRows()[0].row()
        file = self.now_list[row][0]
        self.setEnabled(False)
        if self.mode:
            ret = QMessageBox.warning(self, "Confirm Delete " + self.mode_str[self.mode],
                                      "Delete \"" + file.name + "\" (and ALL CONTENT) PERMANENTLY?", QMessageBox.Yes | QMessageBox.No)
        else:
            ret = QMessageBox.warning(self, "Confirm Delete " + self.mode_str[self.mode], "Delete \"" + file.name + "\" PERMANENTLY?",
                                      QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            print("rem", str(file))
            if self.mode:
                shutil.rmtree(str(file))
            else:
                os.remove(str(file))
            self.tableWidget.selectRow(row + 1)
            self.tableWidget.removeRow(row)
            self.now_list.pop(row)
            self.something_removed = True
            if not self.now_list:
                if self.can_change_mode:
                    QMessageBox.warning(self, "No " + self.mode_str[self.mode] + " left", "No " + self.mode_str[self.mode] + " left.\nChanging to " +
                                        self.mode_str[not self.mode] + " mode", QMessageBox.Ok)
                    self.change_mode()
                    self.can_change_mode = False
                else:
                    self.path = ""
                    self.init_texts()
                    ret = QMessageBox.warning(self, "Nothing left", "Nothing left in current path.\nDo you want to select a new folder?",
                                              QMessageBox.Yes | QMessageBox.No)
                    if ret == QMessageBox.Yes:
                        self.select_directory()
            elif self.mode:
                self.refresh()
        self.setEnabled(True)


if __name__ == "__main__":
    app = QApplication()

    path = None  # select_directory()
    myapp = MainWindow(path)
    myapp.show()
    app.exec_()

    # try:
    #     sys.exit()
    # except SystemExit:
    #     None

# check for bugs in remove (and remove->empty case)
# add browser mode
# browser mode:
# -temporary enable con copy path
# -ottieni file nella path comparando tutti i self.files e self.folders
#     e scegliendo solo quelli direttamente childs (fattibile con metodo "parent" di Path, slow?)

