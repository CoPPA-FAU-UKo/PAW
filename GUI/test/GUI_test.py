import sys
import os
import json

import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QMainWindow
)
import qtmodern.styles
import qtmodern.windows

from src.Backend import LoadLogFile


class JsonLoaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.json_data = None  # This will store the JSON data after loading
        self.train = None
        self.val = None
        self.test = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('CoPPA')
        self.setGeometry(200, 200, 800, 600)

        # Set up layout
        layout = QVBoxLayout()

        # Create a table widget to display the DataFrame content
        self.table_widget = QTableWidget(self)
        layout.addWidget(self.table_widget)


        button_layout = QHBoxLayout()

        # Create a button to load the JSON file
        load_button = QPushButton('Load JSON File', self)
        load_button.clicked.connect(self.load_json_file)
        # Set the size and position of the button
        load_button.setGeometry(50, 100, 100, 20)  # (x, y, width, height)
        layout.addWidget(load_button)

        feature_button = QPushButton('Select categorical feature encoder', self)
        feature_button.clicked.connect(self.load_json_file)
        # Set the size and position of the button
        feature_button.setGeometry(100, 100, 100, 20)  # (x, y, width, height)
        layout.addWidget(feature_button)

        # Set the layout for the main window
        self.setLayout(layout)

        # Make the table widget resize with the window
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Enable the window to be resizable
        self.setMinimumSize(400, 300)  # Optional: set a minimum size


    def load_json_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open JSON File', "../../data/", 'JSON Files (*.json);;All Files (*)')

        if file_name:
            try:
                print(file_name)
                self.json_data = pd.read_json(file_name)  # Store the JSON data in the class attribute
                QMessageBox.information(self, 'Success', 'JSON file loaded successfully!')
                self.train, self.val, self.test, le = LoadLogFile.prepare_log(self.json_data)
                self.display_dataframe()
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"Could not load JSON file:\n{e}")

    def display_dataframe(self):
        if self.json_data is not None:
            try:
                # Get the first 5 rows of the DataFrame
                first_five_rows = self.train.drop(columns=['endDate'])

                # Set up the table widget with the data
                self.table_widget.setRowCount(first_five_rows.shape[0])
                self.table_widget.setColumnCount(first_five_rows.shape[1])
                self.table_widget.setHorizontalHeaderLabels(first_five_rows.columns)

                for i in range(first_five_rows.shape[0]):
                    for j in range(first_five_rows.shape[1]):
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(first_five_rows.iat[i, j])))

                # Adjust header size to fit contents
                self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f"Could not display DataFrame:\n{e}")

    def get_json_data(self):
        # Method to retrieve the stored JSON data
        return self.json_data

def main():
    app = QApplication(sys.argv)

    # Apply qtmodern style
    qtmodern.styles.dark(app)

    viewer = JsonLoaderApp()

    viewer.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
