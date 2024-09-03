import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QCheckBox, QLineEdit, QLabel, QPushButton, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator, QIntValidator
import qtmodern.styles
import qtmodern.windows


class TrainingConfigure(QWidget):
    config_generated = pyqtSignal(dict)

    def __init__(self, column_names):
        super().__init__()
        self.column_names = column_names
        self.initUI()
        self.config = {}

    def initUI(self):
        # Set the widget window title and size
        self.setWindowTitle("Training Configuration")
        self.setGeometry(100, 100, 800, 400)

        # Create the main layout
        main_layout = QHBoxLayout(self)

        # Left-side layout for data split and task-specific configurations
        left_layout = QVBoxLayout()

        # GroupBox for Data split settings
        data_split_group = QGroupBox("Data split", self)
        data_split_layout = QVBoxLayout(data_split_group)

        # Text entry widgets for Training, Validation, and Test set ratios
        self.training_ratio_entry = self.create_float_entry("Training set ratio:")
        self.validation_ratio_entry = self.create_float_entry("Validation set ratio:")
        self.test_ratio_entry = self.create_float_entry("Test set ratio:")

        # Add the entries to the data split layout
        data_split_layout.addWidget(self.training_ratio_entry["label"])
        data_split_layout.addWidget(self.training_ratio_entry["entry"])
        data_split_layout.addWidget(self.validation_ratio_entry["label"])
        data_split_layout.addWidget(self.validation_ratio_entry["entry"])
        data_split_layout.addWidget(self.test_ratio_entry["label"])
        data_split_layout.addWidget(self.test_ratio_entry["entry"])

        # Checkbox for Temporal ordering
        self.temporal_ordering_checkbox = QCheckBox("Temporal ordering", self)
        self.temporal_ordering_checkbox.setChecked(True)  # Checked by default
        data_split_layout.addWidget(self.temporal_ordering_checkbox)

        # Add the data split group box to the left layout
        left_layout.addWidget(data_split_group)

        # GroupBox for Task specific parameters
        task_specific_group = QGroupBox("Task specific parameters", self)
        task_specific_layout = QVBoxLayout(task_specific_group)

        # ComboBox for selecting a column (provided during initialization)
        self.column_selector = QComboBox(self)
        self.column_selector.addItems(self.column_names)
        task_specific_layout.addWidget(QLabel("Label column:", self))
        task_specific_layout.addWidget(self.column_selector)

        # Checkbox for Next step prediction
        self.next_step_checkbox = QCheckBox("Next step prediction", self)
        task_specific_layout.addWidget(self.next_step_checkbox)

        # ComboBox for selecting task type (Classification or Regression)
        self.task_type_combo_box = QComboBox(self)
        self.task_type_combo_box.addItems(["Classification", "Regression"])
        task_specific_layout.addWidget(QLabel("Task Type:", self))
        task_specific_layout.addWidget(self.task_type_combo_box)

        # Add the task-specific group box to the left layout
        left_layout.addWidget(task_specific_group)

        # Add the left layout to the main layout
        main_layout.addLayout(left_layout)

        # Right-side layout for model-specific parameters
        right_layout = QVBoxLayout()

        # ComboBox for selecting the predictive model
        self.model_combo_box = QComboBox(self)
        self.model_combo_box.addItems(["LSTM", "XGBoost"])
        self.model_combo_box.currentIndexChanged.connect(self.update_model_specific_inputs)
        right_layout.addWidget(QLabel("Select Predictive Model:", self))
        right_layout.addWidget(self.model_combo_box)

        # Create a layout to hold model-specific inputs
        self.model_specific_layout = QVBoxLayout()
        right_layout.addLayout(self.model_specific_layout)

        # Initially, display inputs for the selected model
        self.update_model_specific_inputs()

        # Submit button to validate and confirm the configuration
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.submit_configuration)
        right_layout.addWidget(submit_button)

        # Connect the auto-fill logic for the text entries
        self.training_ratio_entry["entry"].editingFinished.connect(self.auto_fill_ratios)
        self.validation_ratio_entry["entry"].editingFinished.connect(self.auto_fill_ratios)
        self.test_ratio_entry["entry"].editingFinished.connect(self.auto_fill_ratios)

        # Add the right layout to the main layout
        main_layout.addLayout(right_layout)

    def create_float_entry(self, label_text):
        label = QLabel(label_text, self)
        entry = QLineEdit(self)
        entry.setPlaceholderText("Enter a float value between 0.0 and 1.0")
        entry.setValidator(QDoubleValidator(0.0, 1.0, 2))  # Allows floats between 0.0 and 1.0 with 2 decimal places
        return {"label": label, "entry": entry}

    def create_int_entry(self, label_text):
        label = QLabel(label_text, self)
        entry = QLineEdit(self)
        entry.setPlaceholderText("Enter an integer value")
        entry.setValidator(QIntValidator(1, 1000000))  # Example: allows integers between 1 and 1000000
        return {"label": label, "entry": entry}

    def create_combo_box(self, label_text, options):
        label = QLabel(label_text, self)
        combo_box = QComboBox(self)
        combo_box.addItems(options)
        return {"label": label, "combo_box": combo_box}

    def update_model_specific_inputs(self):
        # Clear the current layout
        for i in reversed(range(self.model_specific_layout.count())):
            widget = self.model_specific_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Add inputs specific to the selected model
        if self.model_combo_box.currentText() == "LSTM":
            # Create model-specific input fields (LSTM)
            self.hidden_size_entry = self.create_int_entry("Hidden size:")
            self.batch_size_entry = self.create_int_entry("Batch size:")
            self.num_layers_entry = self.create_int_entry("Number of layers:")
            self.learning_rate_entry = self.create_float_entry("Learning rate:")
            self.max_iter_entry = self.create_float_entry("Maximum iterations:")
            self.patience_entry = self.create_float_entry("Patience iterations:")
            self.optimizer_combo_box = self.create_combo_box("Optimizer:", ["Nadam", "Adam", "SGD"])
            self.model_specific_layout.addWidget(self.hidden_size_entry["label"])
            self.model_specific_layout.addWidget(self.hidden_size_entry["entry"])
            self.model_specific_layout.addWidget(self.num_layers_entry["label"])
            self.model_specific_layout.addWidget(self.num_layers_entry["entry"])
            self.model_specific_layout.addWidget(self.batch_size_entry["label"])
            self.model_specific_layout.addWidget(self.batch_size_entry["entry"])
            self.model_specific_layout.addWidget(self.learning_rate_entry["label"])
            self.model_specific_layout.addWidget(self.learning_rate_entry["entry"])
            self.model_specific_layout.addWidget(self.max_iter_entry["label"])
            self.model_specific_layout.addWidget(self.max_iter_entry["entry"])
            self.model_specific_layout.addWidget(self.patience_entry["label"])
            self.model_specific_layout.addWidget(self.patience_entry["entry"])
            self.model_specific_layout.addWidget(self.optimizer_combo_box["label"])
            self.model_specific_layout.addWidget(self.optimizer_combo_box["combo_box"])

        elif self.model_combo_box.currentText() == "XGBoost":
            # Create model-specific input fields (XGBoost)
            self.early_stopping_entry = self.create_int_entry("Early stopping rounds:")
            self.subsample_rate_entry = self.create_float_entry("Sub-sample rate:")
            self.tree_method_combo_box = self.create_combo_box("Tree method:", ["hist", "approx"])
            self.encoding_combo_box = self.create_combo_box("Encoding technique:", ["Last encoding", "Aggregation"])
            self.model_specific_layout.addWidget(self.early_stopping_entry["label"])
            self.model_specific_layout.addWidget(self.early_stopping_entry["entry"])
            self.model_specific_layout.addWidget(self.subsample_rate_entry["label"])
            self.model_specific_layout.addWidget(self.subsample_rate_entry["entry"])
            self.model_specific_layout.addWidget(self.tree_method_combo_box["label"])
            self.model_specific_layout.addWidget(self.tree_method_combo_box["combo_box"])
            self.model_specific_layout.addWidget(self.encoding_combo_box["label"])
            self.model_specific_layout.addWidget(self.encoding_combo_box["combo_box"])

    def auto_fill_ratios(self):
        try:
            # Get the current values or 0 if empty
            training_ratio = float(self.training_ratio_entry["entry"].text() or 0)
            validation_ratio = float(self.validation_ratio_entry["entry"].text() or 0)
            test_ratio = float(self.test_ratio_entry["entry"].text() or 0)

            # Count how many fields are filled
            filled_count = sum([training_ratio > 0, validation_ratio > 0, test_ratio > 0])

            if filled_count == 2:
                # Automatically calculate the third ratio if two are filled
                if training_ratio == 0:
                    self.training_ratio_entry["entry"].setText(f"{1.0 - validation_ratio - test_ratio:.2f}")
                elif validation_ratio == 0:
                    self.validation_ratio_entry["entry"].setText(f"{1.0 - training_ratio - test_ratio:.2f}")
                elif test_ratio == 0:
                    self.test_ratio_entry["entry"].setText(f"{1.0 - training_ratio - validation_ratio:.2f}")

        except ValueError:
            # Ignore errors during auto-fill if inputs are incomplete or invalid
            pass

    def submit_configuration(self):
        try:
            # Retrieve and validate data split ratios
            training_ratio = float(self.training_ratio_entry["entry"].text())
            validation_ratio = float(self.validation_ratio_entry["entry"].text())
            test_ratio = float(self.test_ratio_entry["entry"].text())

            # Ensure that the sum of the ratios equals 1
            total_ratio = training_ratio + validation_ratio + test_ratio
            if not 0.99 <= total_ratio <= 1.01:
                raise ValueError("The sum of the ratios must equal 1.")

            # Save data split settings in the config dictionary
            self.config["training_ratio"] = training_ratio
            self.config["validation_ratio"] = validation_ratio
            self.config["test_ratio"] = test_ratio
            self.config["temporal_ordering"] = self.temporal_ordering_checkbox.isChecked()
            if self.next_step_checkbox.isChecked():
                self.config["label"] = "Next_" + self.column_selector.currentText()
            else:
                self.config["label"] = self.column_selector.currentText()
            self.config["task"] = self.task_type_combo_box.currentText()

            # Save model-specific settings
            selected_model = self.model_combo_box.currentText()
            self.config["model"] = selected_model

            if selected_model == "LSTM":
                self.config["hidden_size"] = int(self.hidden_size_entry["entry"].text())
                self.config["batch_size"] = int(self.batch_size_entry["entry"].text())
                self.config["num_layers"] = int(self.num_layers_entry["entry"].text())
                self.config["max_iter"] = int(self.max_iter_entry["entry"].text())
                self.config["patience"] = int(self.patience_entry["entry"].text())
                self.config["learning_rate"] = float(self.learning_rate_entry["entry"].text())
                self.config["optimizer"] = self.optimizer_combo_box["combo_box"].currentText()
                self.config["encoding"] = "all"
            elif selected_model == "XGBoost":
                self.config["early_stopping_rounds"] = int(self.early_stopping_entry["entry"].text())
                self.config["subsample_rate"] = float(self.subsample_rate_entry["entry"].text())
                self.config["tree_method"] = self.tree_method_combo_box["combo_box"].currentText()
                self.config["encoding"] = "all"
                if self.encoding_combo_box["combo_box"].currentText() == "Last encoding":
                    self.config["encoding"] = "Last"
                elif self.encoding_combo_box["combo_box"].currentText() == "Aggregation":
                    self.config["encoding"] = "Agg_Mean"

            self.config_generated.emit(self.config)
            # Display confirmation message
            QMessageBox.information(self, "Success", "Training configuration successfully saved.")

        except ValueError as e:
            # Show an error message if the values are not valid floats or do not sum to 1
            QMessageBox.critical(self, "Error", f"Invalid input: {e}")


def main():
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)

    # Example column names
    columns = ["Feature1", "Feature2", "Feature3"]

    # Create the widget
    widget = TrainingConfigure(columns)

    # Wrap the widget in a modern window style
    modern_window = qtmodern.windows.ModernWindow(widget)

    # Show the widget as a window
    modern_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
