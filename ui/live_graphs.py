# live_graphs.py
# PySide6 + pyqtgraph window for live gaze/target deltas, stats, and CSV export.

from __future__ import annotations

from datetime import datetime, time as dt_time
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core import config


_NUM_ROWS = 2
_NUM_COLS = 3
_MAX_HISTORY = 1000
_VISIBLE_X_RANGE_SEC = 10.0
_GRAPH_SAMPLE_HZ = 100
_GRAPH_SAMPLE_INTERVAL_SEC = 1.0 / _GRAPH_SAMPLE_HZ


class LiveGraphs(QWidget):
    # Creates the graph window and initializes widgets/state
    def __init__(self):
        super().__init__()

        self._start_time = None
        self._running = False
        self._last_sample_t = None

        self._plots = []
        self._curves = []
        self._x_data = []
        self._y_data = []
        self._stats_labels = []

        self._start_stop_button = None
        self._export_button = None

        self._configure_window()
        self._build_layout()

    # Configures top-level window style/title
    def _configure_window(self):
        self.setWindowTitle("EyeTracker Analyzer")
        self.setStyleSheet("background-color: #121212; color: white;")

    # Builds the main grid layout and populates plots/buttons
    def _build_layout(self):
        layout = QGridLayout()
        self.setLayout(layout)

        self._init_plots(layout)
        self._init_buttons(layout)

    # Initializes all plot widgets and associated data buffers
    def _init_plots(self, layout: QGridLayout):
        colors = ["r", "g", "b", "c", "m", "y"]
        labels = ["ΔX", "ΔY", "ΔR", "Sx", "Sy", "Sr"]

        for i in range(_NUM_ROWS * _NUM_COLS):
            plot_widget = self._create_plot_widget(labels[i])
            curve = plot_widget.plot(pen=colors[i])

            stat_label = QLabel("Min: 0.00  Max: 0.00  Avg: 0.00")
            stat_label.setStyleSheet("color: white; font-size: 10px;")

            container = QWidget()
            vbox = QVBoxLayout()
            vbox.addWidget(plot_widget)
            vbox.addWidget(stat_label)
            container.setLayout(vbox)

            layout.addWidget(container, i // _NUM_COLS, i % _NUM_COLS)

            self._plots.append(plot_widget)
            self._curves.append(curve)
            self._x_data.append([])
            self._y_data.append([])
            self._stats_labels.append(stat_label)

    # Creates a single configured PlotWidget
    def _create_plot_widget(self, y_label: str) -> pg.PlotWidget:
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground("#333333")
        plot_widget.showGrid(x=True, y=True)
        plot_widget.setLabel("bottom", "Time", units="s")
        plot_widget.setLabel("left", y_label, units="")
        plot_widget.enableAutoRange(axis="y", enable=True)
        plot_widget.setXRange(0, _VISIBLE_X_RANGE_SEC)
        return plot_widget

    # Adds Start/Stop and Export buttons at the bottom of the grid
    def _init_buttons(self, layout: QGridLayout):
        hbox = QHBoxLayout()

        self._start_stop_button = QPushButton("Start")
        self._start_stop_button.clicked.connect(self.toggle_timer)
        hbox.addWidget(self._start_stop_button)

        self._export_button = QPushButton("Export to CSV")
        self._export_button.clicked.connect(self.export_to_csv)
        hbox.addWidget(self._export_button)

        layout.addLayout(hbox, _NUM_ROWS, 0, 1, _NUM_COLS)

    # Toggles start/stop and captures the start timestamp (seconds within day)
    def toggle_timer(self):
        now = datetime.now()
        midnight = datetime.combine(now.date(), dt_time(0, 0, 0))
        timestamp = (now - midnight).total_seconds()

        self._running = not self._running
        self._start_time = timestamp if self._running else None
        self._start_stop_button.setText("Stop" if self._running else "Start")

    # Updates graphs at a fixed sampling cadence (e.g., 100 Hz)
    def update_graphs(self, data, timestamp):
        if not self._running or self._start_time is None:
            return

        values = list(data) if data is not None else None
        if not values or len(values) < (_NUM_ROWS * _NUM_COLS):
            return

        t = float(timestamp) - float(self._start_time)

        if self._last_sample_t is None:
            self._last_sample_t = t

        if (t - self._last_sample_t) < _GRAPH_SAMPLE_INTERVAL_SEC:
            return

        self._last_sample_t = t

        for i in range(_NUM_ROWS * _NUM_COLS):
            self._append_data(i, t, values[i])
            self._update_stats(i)
            self._refresh_plot(i, t)

    # Appends a point and trims the buffers to max history
    def _append_data(self, i: int, time_point: float, value):
        if value is None:
            return

        self._x_data[i].append(float(time_point))
        self._y_data[i].append(float(value))

        if len(self._x_data[i]) > _MAX_HISTORY:
            self._x_data[i] = self._x_data[i][- _MAX_HISTORY :]
            self._y_data[i] = self._y_data[i][- _MAX_HISTORY :]

    # Updates min/max/avg label and adjusts y-range with a margin
    def _update_stats(self, i: int):
        ys = self._y_data[i]
        if not ys:
            return

        arr = np.asarray(ys, dtype=float)
        ymin = float(np.min(arr))
        ymax = float(np.max(arr))
        yavg = float(np.mean(arr))

        self._stats_labels[i].setText(f"Min: {ymin:.2f}  Max: {ymax:.2f}  Avg: {yavg:.2f}")

        if ymin == ymax:
            ymin -= 1.0
            ymax += 1.0
        else:
            margin = (ymax - ymin) * 0.1
            ymin -= margin
            ymax += margin

        self._plots[i].setYRange(ymin, ymax)

    # Updates curve data and scrolls the X-axis in a fixed window
    def _refresh_plot(self, i: int, current_time: float):
        if current_time > _VISIBLE_X_RANGE_SEC:
            self._plots[i].setXRange(current_time - _VISIBLE_X_RANGE_SEC, current_time)

        self._curves[i].setData(self._x_data[i], self._y_data[i])
        self._plots[i].getPlotItem().update()

    # Exports all plot buffers into a single CSV file with readable headers
    def export_to_csv(self):
        export_dir = Path(config.PROJECT_ROOT) / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = export_dir / f"live_graphs_{ts}.csv"

        headers = ["Time", "DeltaX", "DeltaY", "DeltaR", "Sx", "Sy", "Sr"]

        max_len = 0
        for xs in self._x_data:
            max_len = max(max_len, len(xs))

        if max_len == 0:
            return

        def _cell(values, idx):
            return values[idx] if idx < len(values) else ""

        rows = []
        for i in range(max_len):
            time_value = _cell(self._x_data[0], i)
            row = [
                time_value,
                _cell(self._y_data[0], i),
                _cell(self._y_data[1], i),
                _cell(self._y_data[2], i),
                _cell(self._y_data[3], i),
                _cell(self._y_data[4], i),
                _cell(self._y_data[5], i),
            ]
            rows.append(row)

        np.savetxt(str(filename), rows, delimiter=",", header=",".join(headers), comments="", fmt="%s")
