import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QMessageBox, QLabel, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
import pandas as pd
import qtmodern.styles
import qtmodern.windows
from src.Backend import DataProcessing


class FeatureEngineeringWidget(QWidget):
    encoded = pyqtSignal(list)

    def __init__(self, dataframes_dict, encoders=None):
        super().__init__()
        self.dataframes_dict = dataframes_dict
        self.initUI()
        self.encoders = encoders
        if self.encoders is None:
            self.encoders = {}

    def initUI(self):
        # Set the widget window title and size
        self.setWindowTitle("Feature Engineering")
        self.setGeometry(100, 100, 800, 400)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # List widget to select multiple DataFrames
        self.df_list_widget = QListWidget(self)
        self.df_list_widget.setSelectionMode(QListWidget.MultiSelection)
        for df_name in self.dataframes_dict.keys():
            self.df_list_widget.addItem(QListWidgetItem(df_name))
        main_layout.addWidget(QLabel("Select DataFrames:", self))
        main_layout.addWidget(self.df_list_widget)

        # Dropdown to select an encoding technique
        self.encoding_combo_box = QListWidget(self)
        self.encoding_combo_box.addItem("One-Hot Encoding")
        self.encoding_combo_box.addItem("Label Encoding")
        main_layout.addWidget(QLabel("Select Encoding Technique:", self))
        main_layout.addWidget(self.encoding_combo_box)

        # List widget to display columns that will be encoded
        self.column_list_widget = QListWidget(self)
        self.column_list_widget.setSelectionMode(QListWidget.MultiSelection)
        main_layout.addWidget(QLabel("Columns to Encode:", self))
        main_layout.addWidget(self.column_list_widget)

        # Update the columns list when different DataFrames are selected
        self.df_list_widget.itemSelectionChanged.connect(self.update_column_list)

        # Apply button to perform encoding
        apply_button = QPushButton("Apply Encoding", self)
        apply_button.clicked.connect(self.apply_encoding)
        main_layout.addWidget(apply_button)

        # Update the column list initially
        self.update_column_list()

    def update_column_list(self):
        # Update the list widget to show columns of the selected DataFrames
        self.column_list_widget.clear()

        selected_dfs = self.df_list_widget.selectedItems()
        if selected_dfs:
            # Collect columns from all selected DataFrames
            all_columns = set()
            for item in selected_dfs:
                df_name = item.text()
                df = self.dataframes_dict[df_name]
                all_columns.update(df.columns)

            self.column_list_widget.addItems(sorted(all_columns))

    def apply_encoding(self):
        selected_dfs = [item.text() for item in self.df_list_widget.selectedItems()]
        encoding_type = self.encoding_combo_box.currentItem().text()
        columns_to_encode = [item.text() for item in self.column_list_widget.selectedItems()]

        if selected_dfs and columns_to_encode:
            try:
                for df_name in selected_dfs:
                    df = self.dataframes_dict[df_name]
                    encoded_df = None
                    encoders = None
                    if encoding_type == "One-Hot Encoding":
                        encoded_df, encoders = DataProcessing.onehot_encode(df, columns_to_encode)
                    elif encoding_type == "Label Encoding":
                        encoded_df, encoders = DataProcessing.label_encode(df, columns_to_encode)

                    # Update the DataFrame in the dictionary
                    self.dataframes_dict[df_name] = encoded_df
                    self.encoders[df_name] = encoders

                self.encoded.emit([self.dataframes_dict, self.encoders])

                QMessageBox.information(self, "Success", f"{encoding_type} applied successfully to selected DataFrames.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred during encoding: {e}")
        else:
            QMessageBox.warning(self, "Warning", "Please select DataFrames and columns to encode.")


def main():
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    widget = FeatureEngineeringWidget({"df1": pd.DataFrame(), "df2": pd.DataFrame()})  # Example DataFrame dictionary
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
