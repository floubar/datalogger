from qtpy import QtWidgets, QtCore, QtGui
import pyqtgraph as pg
import asyncio
import time, datetime
import numpy as np
from . import widgets_base as wb
import os.path as osp

class DataPlotterWidget(QtWidgets.QMainWindow):
    def __init__(self, dataplotter):
        super(DataPlotterWidget, self).__init__()
        self.dlg = dataplotter #this dataplotter does not contain any channels yet

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
        self.plot_points(self.channel.values, self.channel.times)

        PlotterItem.N_CHANNELS += 1

    def plot_points(self, vals, times):
        time_span = (times > self.channel.parent.earliest_point) * (times < self.channel.parent.latest_point)

        self.values = [val for val in vals[time_span]]
        self.times = [time for time in times[time_span]]

        if self.channel.visible:
            self.curve.setData(self.times, self.values)
        self.curve.setVisible(self.channel.visible)

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

        self.real_time_button = QtWidgets.QRadioButton('Set real-time')
        self.calendar_button = QtWidgets.QRadioButton('Select start date')


        for widget in [self.real_time_button, self.calendar_button]:
            self.lay_v.addWidget(widget)
        self.real_time_button.setChecked(self.dlg.show_real_time)
        self.calendar = QtWidgets.QCalendarWidget()
        self.calendar.setSelectedDate(self.dlg.selected_date)
        self.lay_v.addWidget(self.calendar)

        self.real_time_button.clicked.connect(self.real_time_toggled)
        self.calendar_button.clicked.connect(self.real_time_toggled)
        self.calendar.selectionChanged.connect(self.real_time_toggled)

        self.set_green_days()

        self.spinbox.valueChanged.connect(self.update_days_to_show)

    def set_green_days(self):
        """
        Days with existing data are green in the calendar
        """
        font = QtGui.QTextCharFormat()
        font.setBackground(QtGui.QColor('green'))
        for day in self.dlg.days_with_data:
            self.calendar.setDateTextFormat(day, font)

    def real_time_toggled(self):
        real_time =  self.real_time_button.isChecked()
        self.dlg.show_real_time = real_time
        self.calendar.setEnabled(not real_time)

        if not real_time:
            date = self.calendar.selectedDate()

        else:
            date = QtCore.QDate.now()

        print(date.toPyDate())
        self.dlg.selected_date = date.toPyDate()

    def update_days_to_show(self):
        days = self.spinbox.value()
        self.dlg.days_to_show = days

    def create_channel(self, channel):
        return self.tree.create_channel(channel)


class MyDockTreeWidget(QtWidgets.QDockWidget):
    def __init__(self, dataplotter):
        super(MyDockTreeWidget, self).__init__()
        self.mycontrolwidget = MyControlWidget(dataplotter)
        self.tree = self.mycontrolwidget.tree
        self.setWidget(self.mycontrolwidget)
