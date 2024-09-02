import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel, QListWidgetItem, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
import pandas as pd
import qtmodern.styles
import qtmodern.windows
from src.Backend import DataProcessing


class TraceGenerationWidget(QWidget):
    # Define a signal to send generated traces back to the main window
    trace_generated = pyqtSignal(dict)

    def __init__(self, dataframes_dict):
        super().__init__()
        self.dataframes_dict = dataframes_dict
        self.selected_data = {}  # To store the selected DataFrame and features
        self.initUI()

    def initUI(self):
        # Set the widget window title and size
        self.setWindowTitle("Trace Generation")
        self.setGeometry(100, 100, 800, 600)  # Adjusted height to accommodate additional list widget
        self.traces = {}

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # List widget to select multiple DataFrames
        self.df_list_widget = QListWidget(self)
        self.df_list_widget.setSelectionMode(QListWidget.MultiSelection)
        for df_name in self.dataframes_dict.keys():
            self.df_list_widget.addItem(QListWidgetItem(df_name))
        main_layout.addWidget(QLabel("Select DataFrames:", self))
        main_layout.addWidget(self.df_list_widget)

        # ComboBox to select Case ID feature
        self.case_id_combo_box = QComboBox(self)
        main_layout.addWidget(QLabel("Select Case ID feature:", self))
        main_layout.addWidget(self.case_id_combo_box)

        # ComboBox to select Time Stamp feature
        self.timestamp_combo_box = QComboBox(self)
        main_layout.addWidget(QLabel("Select Time Stamp feature:", self))
        main_layout.addWidget(self.timestamp_combo_box)

        # List widget to select additional columns to include in the trace
        self.columns_list_widget = QListWidget(self)
        self.columns_list_widget.setSelectionMode(QListWidget.MultiSelection)
        main_layout.addWidget(QLabel("Select Additional Columns to Include:", self))
        main_layout.addWidget(self.columns_list_widget)

        # Update the ComboBoxes and List widget when different DataFrames are selected
        self.df_list_widget.itemSelectionChanged.connect(self.update_feature_combo_boxes)

        # Apply button to confirm selection
        apply_button = QPushButton("Apply Selection", self)
        apply_button.clicked.connect(self.apply_selection)
        main_layout.addWidget(apply_button)

        # Initialize the ComboBoxes and List widget
        self.update_feature_combo_boxes()

    def update_feature_combo_boxes(self):
        # Clear existing items in the ComboBoxes and List widget
        self.case_id_combo_box.clear()
        self.timestamp_combo_box.clear()
        self.columns_list_widget.clear()

        selected_dfs = self.df_list_widget.selectedItems()
        if selected_dfs:
            # Collect columns from all selected DataFrames
            all_columns = set()
            for item in selected_dfs:
                df_name = item.text()
                df = self.dataframes_dict[df_name]
                all_columns.update(df.columns)

            # Populate both ComboBoxes and the additional columns List widget with the available columns
            sorted_columns = sorted(all_columns)
            self.case_id_combo_box.addItems(sorted_columns)
            self.timestamp_combo_box.addItems(sorted_columns)
            self.columns_list_widget.addItems(sorted_columns)

    def apply_selection(self):
        selected_dfs = [item.text() for item in self.df_list_widget.selectedItems()]
        selected_case_id = self.case_id_combo_box.currentText()
        selected_timestamp = self.timestamp_combo_box.currentText()
        selected_columns = [self.columns_list_widget.item(i).text() for i in range(self.columns_list_widget.count())
                            if self.columns_list_widget.item(i).isSelected()]

        if selected_dfs and selected_case_id and selected_timestamp and selected_columns:
            # Ensure that the Case ID and Time Stamp are always included
            selected_columns = list(set(selected_columns) | {selected_case_id, selected_timestamp})

            # Store the selections and generate traces
            for name in selected_dfs:
                trace_name = name.replace('_df', '_trace')
                self.traces[trace_name] = DataProcessing.generate_trace(self.dataframes_dict[name], selected_timestamp, selected_case_id, selected_columns)

            # Emit the signal with the generated traces
            self.trace_generated.emit(self.traces)

            # Confirm the selections
            QMessageBox.information(self, "Success", f"Event traces generated.")
        else:
            QMessageBox.warning(self, "Warning", "Please select DataFrames and features for both Case ID, Time Stamp and Activity.")

    def closeEvent(self, event):
        # If the widget is closed without applying, emit the signal with current selections
        if self.selected_data:
            self.trace_generated.emit(self.selected_data)
        event.accept()


def main():
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    widget = TraceGenerationWidget({"df1": pd.DataFrame(), "df2": pd.DataFrame()})  # Example DataFrame dictionary
    widget.trace_generated.connect(lambda data: print(f"Received Data: {data}"))  # Example slot
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
