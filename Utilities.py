import ctypes
import ctypes.wintypes
import math
import os
from pathlib import Path

import win32api
import win32con
import win32gui
import win32ui
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide2 import QtCore
from PySide2.QtCore import QMetaObject, QRect, Qt, QSize
from PySide2.QtGui import QPixmap, QBrush, QPainter, QColor
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QFileDialog, QFrame, QStyledItemDelegate
from win32com.shell import shell
import win32com.client as com


from globals import bgcolor, sizebarcolor


class UiLoader(QUiLoader):
    def __init__(self, baseinstance, customWidgets=None):
        QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets

    def createWidget(self, class_name, parent=None, name=''):
        if parent is None and self.baseinstance:
            return self.baseinstance
        else:
            if class_name in self.availableWidgets():
                widget = QUiLoader.createWidget(self, class_name, parent, name)
            else:
                try:
                    widget = self.customWidgets[class_name](parent)
                except:
                    return None
            if self.baseinstance:
                setattr(self.baseinstance, name, widget)
            return widget


def loadUi(uifile, baseinstance=None, customWidgets=None, workingDirectory=None):
    loader = UiLoader(baseinstance, customWidgets)
    if workingDirectory is not None:
        loader.setWorkingDirectory(workingDirectory)
    widget = loader.load(uifile)
    QMetaObject.connectSlotsByName(widget)
    return widget


def open_prop(file):
    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = (("cbSize", ctypes.wintypes.DWORD), ("fMask", ctypes.c_ulong),
                    ("hwnd", ctypes.wintypes.HANDLE), ("lpVerb", ctypes.c_char_p),
                    ("lpFile", ctypes.c_char_p), ("lpParameters", ctypes.c_char_p),
                    ("lpDirectory", ctypes.c_char_p), ("nShow", ctypes.c_int),
                    ("hInstApp", ctypes.wintypes.HINSTANCE), ("lpIDList", ctypes.c_void_p),
                    ("lpClass", ctypes.c_char_p), ("hKeyClass", ctypes.wintypes.HKEY),
                    ("dwHotKey", ctypes.wintypes.DWORD), ("hIconOrMonitor", ctypes.wintypes.HANDLE),
                    ("hProcess", ctypes.wintypes.HANDLE))

    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = 76
    sei.lpVerb = "properties".encode('utf-8')
    sei.lpFile = file.encode('utf-8')
    ctypes.windll.shell32.ShellExecuteEx(ctypes.byref(sei))


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    i = int(math.floor(math.log(size_bytes, 1024)))
    if i:
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, ("B", "KB", "MB", "GB", "TB", "PB", "EB")[i])
    else:
        return "%s B" % (int(size_bytes))


def select_directory():
    return str(QFileDialog.getExistingDirectory(None, "Select Directory"))


def insort(lst, el, key):
    i = 0
    n = len(lst)
    while i < n:
        if key(el) < key(i):
            lst.insert(i, el)
            break
    else:
        lst.append(el)


def open_config_file():
    os.startfile('config.conf')
    

def get_icon(PATH):
    try:
        _, info = shell.SHGetFileInfo(PATH, 0, 0x000001000 | 0x000000100 | 0x00002)
        hIcon = info[0]
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_x)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbmp)
        hdc.DrawIcon((0, 0), hIcon)
        win32gui.DestroyIcon(hIcon)

        bmpinfo = hbmp.GetInfo()
        # Image.frombuffer("RGBA", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), hbmp.GetBitmapBits(True), "raw", "BGRA", 0, 1).save("image.png")
        return QPixmap.fromImage(ImageQt(Image.frombuffer("RGBA", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), hbmp.GetBitmapBits(True), "raw", "BGRA", 0, 1)))
    except:
        return QPixmap()


def get_size_universal(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        try:
            return com.Dispatch("Scripting.FileSystemObject").GetFolder(path).size
        except:
            total_size = os.path.getsize(path)
            for item in os.listdir(path):
                itempath = os.path.join(path, item)
                if os.path.isfile(itempath):
                    total_size += os.path.getsize(itempath)
                elif os.path.isdir(itempath):
                    total_size += get_size_universal(itempath)
            return total_size



def get_brush(rat):
    pixmap = QPixmap(QSize(450, 30))
    pixmap.fill(bgcolor)
    QPainter(pixmap).fillRect(0, 0, int(rat*450), 30, sizebarcolor)
    return QBrush(pixmap)
