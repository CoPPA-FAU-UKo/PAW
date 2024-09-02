import sys
import os
import pandas as pd
import pickle
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QAction, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QTreeWidget, QTreeWidgetItem, QDockWidget,
    QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QMessageBox, QLabel, QTextEdit, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QColor
import qtmodern.styles
import qtmodern.windows
from src.Frontend import LoadLogJSON, BPMN, DataPreprocessing, TraceGeneration, TrainingConfig, ModelTraining


class CoppaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dataframes_dict = {}  # Dictionary to store DataFrames from JsonLoaderApp
        self.traces_dict = {}
        self.encoders = {}
        self.training_parameter = {}
        self.res = {}
        self.initUI()

    def initUI(self):
        # Set the main window title and initial size
        self.setWindowTitle("CoPPA Trainer")
        self.setGeometry(100, 100, 1200, 800)  # Increase height to accommodate the performance table widget

        # Create a central widget (e.g., a table widget)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout(central_widget)

        self.central_table_widget = QTableWidget(self)
        central_layout.addWidget(self.central_table_widget)

        # Create a horizontal layout for training parameters display and start button
        training_layout = QHBoxLayout()

        # Create a text area at the bottom to display training parameters
        self.training_params_display = QTextEdit(self)
        self.training_params_display.setReadOnly(True)
        self.training_params_display.setFixedHeight(150)  # Adjust height as needed
        training_layout.addWidget(QLabel("Training Parameters:", self))
        training_layout.addWidget(self.training_params_display)

        # Add the training_layout to the central_layout
        central_layout.addLayout(training_layout)

        # Add the "Experiment result" table widget
        performance_layout = QHBoxLayout()
        self.performance_table_widget = QTableWidget(self)
        performance_layout.addWidget(QLabel("Experiment Result:", self))
        performance_layout.addWidget(self.performance_table_widget)

        # Create the "Save result" button
        save_button = QPushButton("Save Result", self)
        save_button.clicked.connect(self.save_result_to_excel)
        performance_layout.addWidget(save_button)

        # Add the performance_layout to the central_layout
        central_layout.addLayout(performance_layout)

        # Create a menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        load_preset_action = QAction("Load Preset", self)
        load_preset_action.triggered.connect(self.load_preset)
        save_preset_action = QAction("Save Preset", self)
        save_preset_action.triggered.connect(self.save_preset)
        file_menu.addAction(load_preset_action)
        file_menu.addAction(save_preset_action)

        # Add actions to the menu bar
        model_action = QAction("Generate BPMN", self)
        model_action.triggered.connect(self.open_models_app)
        load_action = QAction("Load JSON", self)
        load_action.triggered.connect(self.open_json_loader_app)
        roll_trace_action = QAction("Generate event trace", self)
        roll_trace_action.triggered.connect(self.open_trace_app)
        feature_action = QAction("Feature engineering", self)
        feature_action.triggered.connect(self.open_feature_engineering_app)
        configure_action = QAction("Configure training", self)
        configure_action.triggered.connect(self.open_configuration_app)
        train_action = QAction("Model training", self)
        train_action.triggered.connect(self.open_training_app)

        # Create a toolbar
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)
        toolbar.addAction(model_action)
        toolbar.addAction(load_action)
        toolbar.addAction(roll_trace_action)
        toolbar.addAction(feature_action)
        toolbar.addAction(configure_action)
        toolbar.addAction(train_action)

        # Create a status bar
        self.statusBar().showMessage("No log file loaded")

        # Create the DataFrames Explorer as a dockable widget
        self.dock_widget = QDockWidget("Eventlog Explorer", self)
        self.dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # Create a widget to hold the two tree widgets
        tree_container_widget = QWidget()
        tree_layout = QVBoxLayout(tree_container_widget)

        # Create a tree widget for the "Raw logs"
        self.raw_log_widget = QTreeWidget()
        self.raw_log_widget.setHeaderLabel("Raw logs")
        tree_layout.addWidget(self.raw_log_widget)

        # Create a tree widget for the "Traces"
        self.traces_widget = QTreeWidget()
        self.traces_widget.setHeaderLabel("Traces")
        tree_layout.addWidget(self.traces_widget)

        # Set the container widget as the widget for the dock widget
        self.dock_widget.setWidget(tree_container_widget)

        # Add the dock widget to the main window
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget)

        # Create a "View" menu to toggle the explorer visibility
        view_menu = menu_bar.addMenu("View")
        toggle_explorer_action = QAction("Toggle DataFrames Explorer", self)
        toggle_explorer_action.triggered.connect(self.toggle_explorer_visibility)
        view_menu.addAction(toggle_explorer_action)

        # Connect double-click signal to a method that displays DataFrame content
        self.raw_log_widget.itemDoubleClicked.connect(self.display_dataframe_content)
        self.traces_widget.itemDoubleClicked.connect(self.display_dataframe_content)

    def open_json_loader_app(self):
        self.json_loader_app = LoadLogJSON.JsonLoaderApp()
        self.json_loader_app.dataframes_ready.connect(self.receive_dataframes)
        self.json_loader_app.show()

    def open_feature_engineering_app(self):
        self.feature_engineering_app = DataPreprocessing.FeatureEngineeringWidget(self.traces_dict)
        self.feature_engineering_app.encoded.connect(self.receive_encoded)
        self.feature_engineering_app.show()

    def open_trace_app(self):
        self.trace_generation_app = TraceGeneration.TraceGenerationWidget(self.dataframes_dict)
        self.trace_generation_app.trace_generated.connect(self.receive_traces)
        self.trace_generation_app.show()

    def open_configuration_app(self):
        columns = []
        if self.traces_dict:
            columns = self.traces_dict[list(self.traces_dict.keys())[0]].columns
        self.configuration_app = TrainingConfig.TrainingConfigure(columns)
        self.configuration_app.config_generated.connect(self.receive_config)
        self.configuration_app.show()

    def open_training_app(self):
        self.training_app = ModelTraining.ModelTraining(self.traces_dict, self.training_parameter)
        self.training_app.res_ready.connect(self.receive_res)
        self.training_app.show()

    def open_models_app(self):
        self.model_app = BPMN.BPMNWidget()
        self.model_app.show()

    @pyqtSlot(dict)
    def receive_dataframes(self, dataframes_dict):
        self.dataframes_dict = dataframes_dict
        self.update_tree_widget()

    @pyqtSlot(dict)
    def receive_traces(self, traces):
        self.traces_dict = traces
        self.update_tree_widget()

    @pyqtSlot(list)
    def receive_encoded(self, encode_res):
        self.traces_dict = encode_res[0]
        self.encoders = encode_res[1]

    @pyqtSlot(dict)
    def receive_config(self, config):
        self.training_parameter = config
        self.update_training_params_display()

    @pyqtSlot(dict)
    def receive_res(self, res):
        self.res = res
        self.update_performance_table()

    def update_tree_widget(self):
        self.raw_log_widget.clear()
        self.traces_widget.clear()

        for name, df in self.dataframes_dict.items():
            df_item = QTreeWidgetItem(self.raw_log_widget)
            df_item.setText(0, name)
            for column in df.columns:
                column_item = QTreeWidgetItem(df_item)
                column_item.setText(0, f"Column: {column}")
            rows_item = QTreeWidgetItem(df_item)
            rows_item.setText(0, f"Rows: {len(df)}")

        for name, df in self.traces_dict.items():
            trace_item = QTreeWidgetItem(self.traces_widget)
            trace_item.setText(0, f"{name}")
            for column in df.columns:
                column_item = QTreeWidgetItem(trace_item)
                column_item.setText(0, f"Column: {column}")
            rows_item = QTreeWidgetItem(trace_item)
            rows_item.setText(0, f"Rows: {len(df)}")

    def toggle_explorer_visibility(self):
        if self.dock_widget.isVisible():
            self.dock_widget.hide()
        else:
            self.dock_widget.show()

    def save_preset(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Preset", "../../presets", "Pickle Files (*.pkl);;All Files (*)", options=options)
        if save_path:
            with open(save_path, 'wb') as f:
                pickle.dump({'traces_dict': self.traces_dict, 'encoders': self.encoders,
                             'parameters': self.training_parameter, 'res': self.res}, f)
            QMessageBox.information(self, "Success", f"Preset saved to {save_path}")

    def load_preset(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        load_path, _ = QFileDialog.getOpenFileName(self, "Load Preset", "../../presets", "Pickle Files (*.pkl);;All Files (*)", options=options)
        if load_path:
            with open(load_path, 'rb') as f:
                data = pickle.load(f)
                self.traces_dict = data['traces_dict']
                self.encoders = data['encoders']
                self.training_parameter = data['parameters']
                self.res = data.get('res', {})  # Load model performance if available
                self.update_tree_widget()
                self.update_training_params_display()
                self.update_performance_table()
            QMessageBox.information(self, "Success", f"Preset loaded from {load_path}")

    def display_dataframe_content(self, item):
        df_name = item.text(0)
        if df_name in self.dataframes_dict:
            df = self.dataframes_dict[df_name]
        elif df_name in self.traces_dict:
            df = self.traces_dict[df_name]
        else:
            QMessageBox.warning(self, "Warning", "DataFrame not found.")
            return

        # Display the DataFrame content in the central table widget
        self.central_table_widget.clear()
        self.central_table_widget.setRowCount(len(df))
        self.central_table_widget.setColumnCount(len(df.columns))
        self.central_table_widget.setHorizontalHeaderLabels(df.columns)

        for i in range(len(df)):
            for j in range(len(df.columns)):
                self.central_table_widget.setItem(i, j, QTableWidgetItem(str(df.iat[i, j])))

        self.central_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.central_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_training_params_display(self):
        if self.training_parameter:
            display_text = "\n".join(f"{key}: {value}" for key, value in self.training_parameter.items())
            self.training_params_display.setText(display_text)
        else:
            self.training_params_display.setText("No training parameters configured.")

    def update_performance_table(self):
        #print(self.res)
        """Update the performance table widget with the results stored in self.res."""
        self.performance_table_widget.clearContents()
        self.performance_table_widget.setRowCount(0)

        if self.res:
            if self.training_parameter["task"] == "Regression":
                self.performance_table_widget.setColumnCount(2)  # For metric names and values
                self.performance_table_widget.setHorizontalHeaderLabels(["Trace", "MAE"])
            else:
                self.performance_table_widget.setColumnCount(4)  # For metric names and values
                self.performance_table_widget.setHorizontalHeaderLabels(["Trace", 'Precision', 'Recall', 'F1'])
            for trace_name, metrics in self.res.items():
                row_position = self.performance_table_widget.rowCount()
                self.performance_table_widget.insertRow(row_position)
                column_count = 1
                self.performance_table_widget.setItem(row_position, 0, QTableWidgetItem(f"{trace_name}"))
                for metric_name, metric_value in metrics.items():
                    self.performance_table_widget.setItem(row_position, column_count, QTableWidgetItem(str(metric_value)))
                    column_count = column_count + 1

            self.performance_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.performance_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        else:
            self.performance_table_widget.setRowCount(0)
            self.performance_table_widget.setColumnCount(0)

    def save_result_to_excel(self):
        options = QFileDialog.Options()
        #options |= QFileDialog.DontUseNativeDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Result", "../../results", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if save_path:
            try:
                df = pd.DataFrame(self.res).T  # Transpose to have traces as rows and metrics as columns
                df.to_excel(save_path)
                QMessageBox.information(self, "Success", f"Result saved to {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save result: {e}")

    def closeEvent(self, event):
        if hasattr(self, 'json_loader_app') and self.json_loader_app.isVisible():
            self.json_loader_app.close()
        event.accept()


def main():
    pd.options.mode.chained_assignment = None  # default='warn'
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    main_window = CoppaMainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
