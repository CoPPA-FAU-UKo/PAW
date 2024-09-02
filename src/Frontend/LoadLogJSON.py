import sys
import os
import json
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QMenu
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
import qtmodern.styles
import qtmodern.windows

class DeselectableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        # Deselect all items on right-click
        self.clearSelection()

class InspectDataFrameApp(QWidget):
    def __init__(self, dataframe, file_name):
        super().__init__()
        self.dataframe = dataframe
        self.file_name = file_name
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f'Inspecting: {self.file_name}')
        self.setGeometry(150, 150, 600, 400)  # Initial window size

        # Main layout
        layout = QVBoxLayout()

        # Entry widget for 'n' rows
        entry_layout = QHBoxLayout()
        self.n_entry = QLineEdit(self)
        self.n_entry.setPlaceholderText("Enter number of rows")
        self.n_entry.setText("5")  # Default value
        entry_layout.addWidget(QLabel("Number of rows:"))
        entry_layout.addWidget(self.n_entry)
        layout.addLayout(entry_layout)

        # Table to display DataFrame rows
        self.table_widget = QTableWidget(self)
        layout.addWidget(self.table_widget)

        # Button to display rows
        display_button = QPushButton("Display Rows", self)
        display_button.clicked.connect(self.display_rows)
        layout.addWidget(display_button)

        self.setLayout(layout)

    def display_rows(self):
        try:
            n = int(self.n_entry.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for rows.")
            return

        if n <= 0:
            QMessageBox.warning(self, "Invalid Input", "Number of rows must be greater than zero.")
            return

        df_head = self.dataframe.head(n)
        self.table_widget.setRowCount(df_head.shape[0])
        self.table_widget.setColumnCount(df_head.shape[1])
        self.table_widget.setHorizontalHeaderLabels(df_head.columns)

        for i in range(df_head.shape[0]):
            for j in range(df_head.shape[1]):
                self.table_widget.setItem(i, j, QTableWidgetItem(str(df_head.iat[i, j])))

class JsonLoaderApp(QWidget):
    dataframes_ready = pyqtSignal(dict)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.json_data_dict = {}  # Dictionary to store loaded JSON data keyed by file name
        self.dataframes_dict = {}  # Dictionary to store converted DataFrames
        self.selection_timer = QTimer()
        self.selection_timer.setSingleShot(True)
        self.selection_timer.timeout.connect(self.enforce_single_selection)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('CoPPA JSON Loader')
        self.setGeometry(100, 100, 800, 600)  # Initial window size

        # Set up main layout
        main_layout = QVBoxLayout()

        # Create labels for list widgets
        json_label = QLabel("Loaded JSON Files:")
        converted_label = QLabel("Converted DataFrames:")

        # Add labels to the main layout
        main_layout.addWidget(json_label)

        # Create a list widget to display loaded JSON file names
        self.file_list_widget = DeselectableListWidget(self)
        self.file_list_widget.setSelectionMode(QListWidget.MultiSelection)  # Allow multiple selection
        self.file_list_widget.itemSelectionChanged.connect(self.deselect_other_list)
        main_layout.addWidget(self.file_list_widget)

        main_layout.addWidget(converted_label)

        # Create a list widget to display converted DataFrame file names
        self.converted_list_widget = DeselectableListWidget(self)
        self.converted_list_widget.setSelectionMode(QListWidget.MultiSelection)  # Allow multiple selection
        self.converted_list_widget.itemSelectionChanged.connect(self.deselect_other_list)
        self.converted_list_widget.itemSelectionChanged.connect(self.handle_selection_change)
        self.converted_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.converted_list_widget.customContextMenuRequested.connect(self.handle_right_click)
        main_layout.addWidget(self.converted_list_widget)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        # Create buttons
        load_button = QPushButton('Load JSON File', self)
        remove_button = QPushButton('Remove Selected Files', self)
        convert_button = QPushButton('Convert', self)
        inspect_button = QPushButton('Inspect Log', self)

        # Add buttons to the horizontal layout
        button_layout.addWidget(load_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(convert_button)
        button_layout.addWidget(inspect_button)

        # Connect buttons to their respective functions
        load_button.clicked.connect(self.load_json_file)
        remove_button.clicked.connect(self.remove_selected_files)
        convert_button.clicked.connect(self.convert_json_data)
        inspect_button.clicked.connect(self.inspect_selected_log)

        # Add the horizontal layout to the main layout
        main_layout.addLayout(button_layout)

        # Set the layout for the main window
        self.setLayout(main_layout)

        # Enable the window to be resizable
        self.setMinimumSize(400, 300)

    def deselect_other_list(self):
        if self.sender() == self.file_list_widget:
            self.converted_list_widget.clearSelection()
        elif self.sender() == self.converted_list_widget:
            self.file_list_widget.clearSelection()

    def handle_selection_change(self):
        if len(self.converted_list_widget.selectedItems()) == 1:
            # If only one item is selected, start a timer to enforce single selection after a delay
            self.selection_timer.start(100)  # Short delay to allow for potential multi-selection dragging
        else:
            # If more than one item is selected, stop the timer
            self.selection_timer.stop()

    def enforce_single_selection(self):
        selected_items = self.converted_list_widget.selectedItems()
        if len(selected_items) > 1:
            # Keep only the most recently selected item
            last_selected = selected_items[-1]
            self.converted_list_widget.clearSelection()
            last_selected.setSelected(True)

    def load_json_file(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, 'Open JSON Files', "../../data/", 'JSON Files (*.json);;All Files (*)')
        loaded_files = []

        for file_name in file_names:
            if file_name:
                try:
                    with open(file_name, 'r') as file:
                        data = json.load(file)  # Load the JSON data
                        base_name = os.path.basename(file_name)  # Get the base file name
                        name = base_name
                        self.json_data_dict[name] = data  # Store the JSON data in the dictionary

                        # Add the file name to the list widget
                        if not self.file_list_widget.findItems(base_name, Qt.MatchExactly):
                            self.file_list_widget.addItem(base_name)
                        loaded_files.append(base_name)

                except Exception as e:
                    QMessageBox.critical(self, 'Error', f"Could not load JSON file:\n{e}")

        if loaded_files:
            QMessageBox.information(self, 'Success', f'{len(loaded_files)} file(s) loaded successfully!')

    def remove_selected_files(self):
        selected_items_json = self.file_list_widget.selectedItems()
        selected_items_converted = self.converted_list_widget.selectedItems()
        removed_files_json = []
        removed_files_converted = []

        # Remove selected original JSON files
        for item in selected_items_json:
            file_name = item.text()
            if file_name in self.json_data_dict:
                del self.json_data_dict[file_name]  # Remove the JSON data from the dictionary
                removed_files_json.append(file_name)
            self.file_list_widget.takeItem(self.file_list_widget.row(item))  # Remove the item from the list widget

        # Remove selected converted DataFrames
        for item in selected_items_converted:
            file_name = item.text()
            if file_name in self.dataframes_dict:
                del self.dataframes_dict[file_name]  # Remove the DataFrame from the dictionary
                removed_files_converted.append(file_name)
            self.converted_list_widget.takeItem(self.converted_list_widget.row(item))  # Remove the item from the list widget

        if removed_files_json or removed_files_converted:
            QMessageBox.information(self, 'Info', f'{len(removed_files_json)} original file(s) and {len(removed_files_converted)} converted file(s) removed.')

    def convert_json_data(self):
        if not self.json_data_dict:
            QMessageBox.warning(self, 'Warning', 'No JSON files loaded.')
            return

        converted_files = []

        for file_name, data in self.json_data_dict.items():
            try:
                converted_file_name = file_name.replace('.json', '_df')
                # Convert JSON data to a Pandas DataFrame
                df = pd.DataFrame(data)
                self.dataframes_dict[converted_file_name] = df  # Store the DataFrame in the dictionary


                if not self.converted_list_widget.findItems(converted_file_name, Qt.MatchExactly):
                    self.converted_list_widget.addItem(converted_file_name)
                converted_files.append(file_name)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"Could not convert {file_name}:\n{e}")

        if converted_files:
            QMessageBox.information(self, 'Success', f'{len(converted_files)} file(s) converted to DataFrame(s) successfully!')

    def handle_right_click(self, position):
        self.converted_list_widget.clearSelection()

    def inspect_selected_log(self):
        selected_items = self.converted_list_widget.selectedItems()
        if len(selected_items) != 1:
            QMessageBox.warning(self, 'Warning', 'Please select exactly one file to inspect.')
            return

        selected_item = selected_items[0]
        file_name = selected_item.text().replace('_df', '.json')
        if file_name in self.dataframes_dict:
            df = self.dataframes_dict[file_name]
            self.inspect_dataframe(df, file_name)

    def inspect_dataframe(self, dataframe, file_name):
        self.inspect_app = InspectDataFrameApp(dataframe, file_name)
        self.inspect_app.show()

    def get_json_data(self):
        # Method to retrieve the stored JSON data
        return self.json_data_dict

    def closeEvent(self, event):
        # Emit signal with DataFrames when closing
        self.dataframes_ready.emit(self.dataframes_dict)
        event.accept()

def main():
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    viewer = JsonLoaderApp()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
