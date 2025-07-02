import os
from datetime import datetime, time
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (QGridLayout, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout)

class LiveGraphs(QWidget):
    """ Real-time graphs with live stats and CSV export. """

    # --------------------- Initialization ---------------------

    def __init__(self):
        super().__init__()
        self.start_time = None
        self.setWindowTitle("EyeTracker Analyzer")
        self.setStyleSheet("background-color: #121212; color: white;")

        self.num_rows, self.num_cols = 2, 3
        self.plots, self.curves = [], []
        self.x_data, self.y_data = [], []
        self.stats_labels = []
        self.running = False

        self._setup_layout()

    def _setup_layout(self):
        """Builds the main layout: grid of plots + control buttons."""
        layout = QGridLayout()
        self.setLayout(layout)
        self._init_plots(layout)
        self._init_buttons(layout)

    def _init_plots(self, layout):
        """Initializes plot widgets, curves, and stat labels."""
        colors = ['r', 'g', 'b', 'c', 'm', 'y']
        labels = ["ΔX", "ΔY", "ΔR", "Sx", "Sy", "Sr"]

        for i in range(self.num_rows * self.num_cols):
            plot_layout = QVBoxLayout()

            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('k')
            plot_widget.showGrid(x=True, y=True)
            plot_widget.setLabel('bottom', 'Time', units='s')
            plot_widget.setLabel('left', labels[i], units='')
            plot_widget.setYRange(0, 10)
            plot_widget.setXRange(0, 10)

            curve = plot_widget.plot(pen=colors[i])
            stat_label = QLabel("Min: 0.00  Max: 0.00  Avg: 0.00")
            stat_label.setStyleSheet("color: white; font-size: 10px;")

            plot_layout.addWidget(plot_widget)
            plot_layout.addWidget(stat_label)

            container = QWidget()
            container.setLayout(plot_layout)
            layout.addWidget(container, i // self.num_cols, i % self.num_cols)

            self.plots.append(plot_widget)
            self.curves.append(curve)
            self.x_data.append([])
            self.y_data.append([])
            self.stats_labels.append(stat_label)

    def _init_buttons(self, layout):
        """Adds Start/Stop and Export buttons to the bottom of the layout."""
        button_layout = QHBoxLayout()

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.clicked.connect(self.toggle_timer)
        button_layout.addWidget(self.start_stop_button)

        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout, self.num_rows, 0, 1, self.num_cols)

    # --------------------- Runtime Control ---------------------

    def toggle_timer(self):
        """Toggles between start and stop. Records the starting timestamp."""
        now = datetime.now()
        midnight = datetime.combine(now.date(), time(0, 0, 0))
        timestamp = (now - midnight).total_seconds()

        self.running = not self.running
        self.start_time = timestamp if self.running else None
        self.start_stop_button.setText("Stop" if self.running else "Start")

    def update_graphs(self, data, timestamp):
        """Updates all graphs. """
        if not self.running or self.start_time is None:
            return

        current_time = timestamp - self.start_time
        for i in range(self.num_rows * self.num_cols):
            self._append_data(i, current_time, data[i])
            self._update_stats(i)
            self._refresh_plot(i, current_time)

    # --------------------- Plot Update Internals ---------------------

    def _append_data(self, i, time_point, value):
        """Appends one data point to a graph; trims history to [max_history] points."""
        max_history = 1000

        self.x_data[i].append(time_point)
        self.y_data[i].append(value)

        if len(self.x_data[i]) > max_history:
            self.x_data[i] = self.x_data[i][-max_history:]
            self.y_data[i] = self.y_data[i][-max_history:]

    def _update_stats(self, i):
        """Updates min/max/avg labels and Y-axis range for a plot."""
        if not self.y_data[i]:
            return

        ymin = np.min(self.y_data[i])
        ymax = np.max(self.y_data[i])
        yavg = np.mean(self.y_data[i])
        self.stats_labels[i].setText(f"Min: {ymin:.2f}  Max: {ymax:.2f}  Avg: {yavg:.2f}")
        self.plots[i].setYRange(ymin, ymax)

    def _refresh_plot(self, i, current_time):
        """Scrolls the X-axis and updates the plotted data."""
        if current_time > 10:
            self.plots[i].setXRange(current_time - 10, current_time)
        self.curves[i].setData(self.x_data[i], self.y_data[i])

    # --------------------- Export ---------------------

    def export_to_csv(self):
        """Exports each graph’s time/value data to a CSV file."""
        for idx, (x, y) in enumerate(zip(self.x_data, self.y_data)):
            if x and y and len(x) == len(y):
                os.makedirs("exports", exist_ok=True)
                filename = f"exports/plot_{idx}_{datetime.now().strftime('%H%M%S')}.csv"
                np.savetxt(filename, np.column_stack((x, y)), delimiter=",", header="Time,Value", comments='')