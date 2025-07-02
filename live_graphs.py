from datetime import datetime
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (QGridLayout, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout)

# A dashboard that displays six real-time graphs
class LiveGraphs(QWidget):
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.setWindowTitle("EyeTracker Analyzer")
        self.setStyleSheet("background-color: #121212; color: white;")

        layout = QGridLayout()
        self.setLayout(layout)

        self.num_rows = 2
        self.num_cols = 3
        self.plots = []
        self.curves = []
        self.x_data = []
        self.y_data = []
        self.stats_labels = []
        self.running = False

        colors = ['r', 'g', 'b', 'c', 'm', 'y']
        labels = ["ΔX", "ΔY", "ΔR", "Sx", "Sy", "Sr"]
        counter = 0

        # Create 9 plots
        for row in range(self.num_rows):
            for col in range(self.num_cols):

                plot_layout = QVBoxLayout()

                plot_widget = pg.PlotWidget()
                plot_widget.setBackground('k')
                plot_widget.showGrid(x=True, y=True)
                plot_widget.setLabel('bottom', 'Time', units='s')

                plot_widget.setLabel('left', labels[counter], units='')
                plot_widget.setYRange(0, 10)
                plot_widget.setXRange(0, 10)

                curve = plot_widget.plot(pen=colors[row * self.num_cols + col])

                stat_label = QLabel("Min: 0.00  Max: 0.00  Avg: 0.00")
                stat_label.setStyleSheet("color: white; font-size: 10px;")

                plot_layout.addWidget(plot_widget)
                plot_layout.addWidget(stat_label)

                container = QWidget()
                container.setLayout(plot_layout)

                layout.addWidget(container, row, col)

                self.plots.append(plot_widget)
                self.curves.append(curve)
                self.x_data.append([])
                self.y_data.append([])
                self.stats_labels.append(stat_label)

                counter = counter + 1

        # Buttons
        button_layout = QHBoxLayout()

        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.clicked.connect(self.toggle_timer)
        button_layout.addWidget(self.start_stop_button)

        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout, 3, 0, 1, 3)

    def toggle_timer(self):
        self.running = not self.running
        if self.running:
            now = datetime.now()
            milliseconds_since_midnight = (
                    now.hour * 3600_000 +
                    now.minute * 60_000 +
                    now.second * 1_000 +
                    now.microsecond // 1_000
            )
            self.start_time = milliseconds_since_midnight / 1000
            self.start_stop_button.setText("Stop")
        else:
            self.start_stop_button.setText("Start")

    # Append new data to each graph if recording is active
    def update_graphs(self, data, datatime, x_offset, y_offset):
        if self.running:
            current_time = datatime - self.start_time

            if len(data) <= len(self.curves):
                for i in range(6):
                    self.x_data[i].append(current_time)
                    self.y_data[i].append(data[i])


                    if len(self.x_data[i]) > 1000:
                        self.x_data[i] = self.x_data[i][-1000:]
                        self.y_data[i] = self.y_data[i][-1000:]

                    if current_time > 10:
                        self.plots[i].setXRange(current_time - 10, current_time)

                    # Update live stats
                    if self.y_data[i]:
                        ymin = np.min(self.y_data[i])
                        ymax = np.max(self.y_data[i])
                        yavg = np.mean(self.y_data[i])
                        self.stats_labels[i].setText(f"Min: {ymin:.2f}  Max: {ymax:.2f}  Avg: {yavg:.2f}")
                        self.plots[i].setYRange(ymin, ymax)

                    self.curves[i].setData(self.x_data[i], self.y_data[i])


    def export_to_csv(self):
        for idx, (x, y) in enumerate(zip(self.x_data, self.y_data)):
            if x and y:
                np.savetxt(f"plot_{idx}_data.csv", np.column_stack((x, y)), delimiter=",", header="Time,Value", comments='')