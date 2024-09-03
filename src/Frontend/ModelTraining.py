import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QListWidget, QListWidgetItem, QMessageBox, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
import qtmodern.styles
import qtmodern.windows
from src.Backend import TrainModel  # Assuming the backend code is placed in `ModelBackend.py`


class ModelTraining(QWidget):
    res_ready = pyqtSignal(dict)
    def __init__(self, trace_dict, training_config):
        super().__init__()
        self.trace_dict = trace_dict  # The dataset (log) for training
        self.training_config = training_config  # The configuration parameters for training
        self.res_dict = {}
        self.initUI()

    def initUI(self):
        # Set the widget window title and size
        self.setWindowTitle("Model Training")
        self.setGeometry(100, 100, 600, 800)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # Display the training parameters at the top
        self.parameters_text = QTextEdit(self)
        self.parameters_text.setReadOnly(True)
        main_layout.addWidget(QLabel("Training Parameters:", self))
        main_layout.addWidget(self.parameters_text)
        self.display_training_parameters()

        # List widget to display columns and allow selection
        self.feature_list_widget = QListWidget(self)
        self.feature_list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.populate_feature_list()
        main_layout.addWidget(QLabel("Select Features:", self))
        main_layout.addWidget(self.feature_list_widget)

        # Button to start training
        self.start_button = QPushButton("", self)  # No title for the button
        self.start_button.setText("🚀 Start Training")  # Add an icon or symbol instead of a title
        self.start_button.clicked.connect(self.start_training)
        main_layout.addWidget(self.start_button)

        # Area to display validation statistics
        self.val_stat_text = QTextEdit(self)
        self.val_stat_text.setReadOnly(True)
        main_layout.addWidget(QLabel("Validation Statistics:", self))
        main_layout.addWidget(self.val_stat_text)

        # Table widget to display test statistics
        self.test_stat_table = QTableWidget(self)
        self.test_stat_table.setColumnCount(2)  # For metric names and values
        self.test_stat_table.setHorizontalHeaderLabels(["Metric", "Value"])
        main_layout.addWidget(QLabel("Test Statistics:", self))
        main_layout.addWidget(self.test_stat_table)

    def populate_feature_list(self):
        """Populate the list widget with columns from the data."""
        if self.trace_dict:
            # Assume the trace_dict contains DataFrames; take the first one to get the columns
            first_trace = list(self.trace_dict.values())[0]
            columns = first_trace.columns
            for column in columns:
                item = QListWidgetItem(column)
                self.feature_list_widget.addItem(item)

    def display_training_parameters(self):
        """Display the training parameters in the text area."""
        self.parameters_text.clear()
        self.parameters_text.append("Model: " + self.training_config["model"])
        self.parameters_text.append("Task Type: " + self.training_config["task"])
        self.parameters_text.append("Training Ratio: " + str(self.training_config["training_ratio"]))
        self.parameters_text.append("Validation Ratio: " + str(self.training_config["validation_ratio"]))
        self.parameters_text.append("Test Ratio: " + str(self.training_config["test_ratio"]))
        self.parameters_text.append("Label: " + self.training_config["label"])
        self.parameters_text.append("Encoding: " + self.training_config["encoding"])

        if self.training_config["model"] == "XGBoost":
            self.parameters_text.append("Early Stopping Rounds: " + str(self.training_config["early_stopping_rounds"]))
            self.parameters_text.append("Subsample Rate: " + str(self.training_config["subsample_rate"]))
            self.parameters_text.append("Tree Method: " + self.training_config["tree_method"])
        elif self.training_config["model"] == "LSTM":
            self.parameters_text.append("Hidden Size: " + str(self.training_config["hidden_size"]))
            self.parameters_text.append("Learning Rate: " + str(self.training_config["learning_rate"]))
            self.parameters_text.append("Optimizer: " + self.training_config["optimizer"])

    def start_training(self):
        # Get the selected features from the list widget
        selected_items = self.feature_list_widget.selectedItems()
        selected_features = [item.text() for item in selected_items]

        if not selected_features:
            QMessageBox.warning(self, "Warning", "Please select at least one feature.")
            return

        # Update the training configuration with the selected features
        self.training_config["feature"] = selected_features

        self.val_stat_text.clear()
        self.test_stat_table.clearContents()  # Clear the test statistics table
        self.test_stat_table.setRowCount(0)  # Reset the table row count

        # Call the training pipeline
        try:
            for name, trace in self.trace_dict.items():
                predictor, val_stat, test_score = TrainModel.training_pipline(trace, self.training_config)

                # Display validation statistics
                if val_stat is not None:
                    if self.training_config["model"] == "XGBoost":
                        self.val_stat_text.append(f"{name} Validation Set Statistics:\n")
                        for key, value in val_stat.items():
                            self.val_stat_text.append(f"{key}: {value}")
                    else:
                        self.val_stat_text.append(f"{name} Validation Set Statistics: {val_stat} \n")
                else:
                    self.val_stat_text.append("No validation statistics available.")

                # Display test statistics in the table
                if test_score is not None:
                    if self.training_config["task"] == "Regression":
                        metrics = [("Mean Absolute Error (MAE)", test_score[0])]
                        self.res_dict[name] = {"Mean Absolute Error (MAE)": test_score[0]}
                    elif self.training_config["task"] == "Classification":
                        precision, recall, f1 = test_score
                        metrics = [
                            ("Data set", name),
                            ("Precision", precision),
                            ("Recall", recall),
                            ("F1 Score", f1)
                        ]
                        self.res_dict[name] = {"Precision": precision, "Recall": recall, "F1": f1}

                    for metric_name, metric_value in metrics:
                        row_position = self.test_stat_table.rowCount()
                        self.test_stat_table.insertRow(row_position)
                        self.test_stat_table.setItem(row_position, 0, QTableWidgetItem(metric_name))
                        self.test_stat_table.setItem(row_position, 1, QTableWidgetItem(str(metric_value)))
                    row_position = self.test_stat_table.rowCount()
                    self.test_stat_table.insertRow(row_position)
                else:
                    QMessageBox.warning(self, "Warning", "No test statistics available.")
            self.res_ready.emit(self.res_dict)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"{e}")


