from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time
import numpy as np
from . import widgets_base as wb


class DataPlotterWidget(QtWidgets.QMainWindow):
    def __init__(self, dataplotter):
        super(DataPlotterWidget, self).__init__()
        self.dlg = dataplotter

        self.graph = pg.GraphicsWindow(title="DataPlotter")
        self.plot_item = self.graph.addPlot(title="DataPlotter", axisItems={
            'bottom': wb.TimeAxisItem(orientation='bottom')})
        self.plot_item.showGrid(y=True, alpha=1.)
        self.setCentralWidget(self.graph)

        self._dock_tree = MyDockTreeWidget(dataplotter)
        self.tree = self._dock_tree.tree
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self._dock_tree)

        self.show()

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

class PlotterItem(wb.MyTreeItem):
    COLORS = ['red', 'green', 'blue', 'cyan', 'magenta']
    N_CHANNELS = 0

    def initialize(self, channel):
        color = self.COLORS[self.N_CHANNELS % len(self.COLORS)]
        self.setBackground(0, QtGui.QColor(color))
        self.channel = channel

        self.curve = self.dlg.widget.plot_item.plot(pen=color[0])
        self.curve.setVisible(channel.visible)
        self.N_CHANNELS += 1

        self.plot_points(self.channel.values, self.channel.times)

    def plot_points(self, vals, times):
        self.values = [val for val in vals]
        self.times = [time for time in times]

        self.curve.setData(self.times, self.values)


class PlotterTree(wb.MyTreeWidget):
    item_class = PlotterItem

    def __init__(self, dataplotter):
        super(wb.MyTreeWidget, self).__init__()
        self.setHeaderLabels(["Channel", "Visible"])
        self.setColumnCount(2)
        self.dlg = dataplotter
        self.itemChanged.connect(self.update)
        self.setSortingEnabled(True)

    def update(self):
        for channel in self.dlg.channels.values():
            channel.visible = channel.widget.checkState(1) == 2


class MyControlWidget(QtWidgets.QWidget):
    def __init__(self, dataplotter):
        super(MyControlWidget, self).__init__()
        self.dlg = dataplotter
        self.lay_v = QtWidgets.QVBoxLayout()
        self.setLayout(self.lay_v)
        self.lay_h = QtWidgets.QHBoxLayout()
        self.lay_v.addLayout(self.lay_h)

        self.label = QtWidgets.QLabel("# of days to display")
        self.lay_h.addWidget(self.label)
        self.spinbox = QtWidgets.QSpinBox()
        self.lay_h.addWidget(self.spinbox)
        self.lay_h.addStretch()

        self.tree = PlotterTree(self.dlg)
        self.lay_v.addWidget(self.tree)
        self.spinbox.setValue(self.dlg.days_to_show)

        self.spinbox.valueChanged.connect(self.update_days_to_show)

    def update_days_to_show(self):
        days = self.spinbox.value()
        self.dlg.days_to_show = days
        print('dts updated')
        self.update_plot()
        #self.tree.

    def create_channel(self, channel):
        return self.tree.create_channel(channel)

    def update_plot(self):
        itemno = len(self.dlg.channels)
        for i in range (0, itemno):
            item = self.tree.topLevelItem(i)
            item.plot_points(item.channel.values, item.channel.times)

class MyDockTreeWidget(QtWidgets.QDockWidget):
    def __init__(self, dataplotter):
        super(MyDockTreeWidget, self).__init__()

        self.mycontrolwidget = MyControlWidget(dataplotter)
        self.tree = self.mycontrolwidget.tree
        self.setWidget(self.mycontrolwidget)
