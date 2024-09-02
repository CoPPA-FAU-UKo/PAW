import sys
import random
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox, QComboBox, QListWidget, QGroupBox, QFileDialog
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize
import qtmodern.styles
import qtmodern.windows

import src.Backend.GenerateBPMN
from src.Backend import GenerateBPMN  # Assuming your generate_BPMN function is here


class BPMNWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.generation_para_list = []
        self.bpmn_models = []
        self.initUI()

    def initUI(self):
        # Set the widget window title and size
        self.setWindowTitle("BPMN model generator")

        # Set the initial size of the window
        self.setGeometry(100, 100, 800, 600)

        # Create the main layout
        main_layout = QVBoxLayout(self)

        # Create the top layout that holds input fields and list widget
        top_layout = QHBoxLayout()

        # Create the left layout for input fields
        input_layout = QVBoxLayout()

        # Create labels and line edits for 7 float inputs
        generation_parameters_name = [
            "Total number of tasks", "Branching ratio", "Sequence ratio",
            "Exclusive gateway ratio", "Parallel gateway ratio", "Loop ratio",
            "Empty loop ratio", "Number of generated models"
        ]

        # Initialize the inputs
        self.inputs = []
        for i in range(8):
            field_layout = QHBoxLayout()
            label = QLabel(generation_parameters_name[i])
            input_field = QLineEdit(self)

            # Set placeholder text and random initial values
            if i == 0:
                initial_value = random.randint(5, 20)  # Example: 5-20 tasks
            elif i == 7:
                initial_value = random.randint(1, 10)  # Example: 1-10 models
            else:
                initial_value = 0.0

            if i == 1:  # Branching ratio
                initial_value = random.uniform(0.1, 0.9)
            if i in range(2, 6):  # Sequence ratio, Exclusive gateway ratio, Parallel gateway ratio, Loop ratio
                input_field.setPlaceholderText("Enter a float value between 0.0 and 1.0")
            else:
                if i == 7:
                    input_field.setPlaceholderText("Enter an integer value")

            # Set the initial value to the input field and store it in self.inputs
            input_field.setText(str(initial_value))
            input_layout.addWidget(label)
            input_layout.addWidget(input_field)
            input_layout.addLayout(field_layout)
            self.inputs.append(input_field)

        # Add a boolean parameter using QComboBox for True/False selection
        bool_layout = QHBoxLayout()
        bool_label = QLabel("Fix task names across models:")
        self.bool_input = QComboBox(self)
        self.bool_input.addItems(["True", "False"])
        bool_layout.addWidget(bool_label)
        bool_layout.addWidget(self.bool_input)
        input_layout.addLayout(bool_layout)

        # Adjust the values so that Sequence ratio + Exclusive gateway ratio + Parallel gateway ratio + Loop ratio = 1
        self.randomize_parameters()

        # Collect and check the input values
        self.collect_inputs()

        # Create a randomize button
        randomize_button = QPushButton("Randomize", self)
        randomize_button.clicked.connect(self.randomize_parameters)
        input_layout.addWidget(randomize_button)

        # Create a submit button
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.submit)
        input_layout.addWidget(submit_button)

        # Create a generate button
        generate_button = QPushButton("Generate", self)
        generate_button.clicked.connect(self.generate_models)
        input_layout.addWidget(generate_button)

        # Create a save models button
        save_button = QPushButton("Save models", self)
        save_button.clicked.connect(self.save_models)
        input_layout.addWidget(save_button)

        # Add input layout to top layout
        top_layout.addLayout(input_layout)

        # Create a group box for the output list widget with a title
        output_group_box = QGroupBox("Seeds of generated model")
        output_layout = QVBoxLayout()
        self.output_list_widget = QListWidget(self)  # Use QListWidget instead of QTextEdit
        output_layout.addWidget(self.output_list_widget)

        # Add the group box to the top layout
        output_group_box.setLayout(output_layout)
        top_layout.addWidget(output_group_box)

        # Create a "Visualize model" button
        visualize_button = QPushButton("Visualize model", self)
        visualize_button.clicked.connect(self.visualize_model)
        output_layout.addWidget(visualize_button)

        # Add top layout to main_layout
        main_layout.addLayout(top_layout)

        # Add the graph visualization area at the bottom
        self.graph_label = QLabel(self)
        self.graph_label.setAlignment(Qt.AlignCenter)
        self.graph_label.setText("Visualization will appear here")
        self.graph_label.setMinimumHeight(400)  # Set a minimum height for the graph label
        self.graph_label.setScaledContents(False)  # Auto-fit the PNG image to the QLabel size
        main_layout.addWidget(self.graph_label)  # Allocate more space to the graph label

    def randomize_parameters(self):
        # Randomize parameters as during initialization
        self.inputs[0].setText(str(random.randint(5, 20)))  # Total number of tasks
        self.inputs[7].setText(str(random.randint(1, 10)))  # Number of generated models

        # Set random ratios and normalize them
        ratios = [random.uniform(0.1, 1.0) for _ in range(4)]
        total = sum(ratios)
        ratios = [r / total for r in ratios]

        # Set the adjusted ratios to the corresponding fields
        for i, ratio in enumerate(ratios):
            self.inputs[i + 2].setText(f"{ratio:.2f}")

    def collect_inputs(self):
        # Collect and check the input values
        values = []
        for i, input_field in enumerate(self.inputs):
            if i < 7:  # These should be floats
                value = float(input_field.text())
            else:  # This should be an integer
                value = int(input_field.text())
            values.append(value)

        # Get the boolean value
        bool_value = self.bool_input.currentText() == "True"
        values.append(bool_value)
        self.generation_para_list = values

    def submit(self):
        try:
            # Collect and check the input values
            self.collect_inputs()
            # Show a success message
            QMessageBox.information(self, "Success", "All parameters saved for generation")

        except ValueError:
            # Show an error message if any input is not a valid float or integer
            QMessageBox.critical(self, "Error", "Please enter valid values in all fields.")

    def generate_models(self):
        # Call generate_BPMN with the saved parameters and store the result
        try:
            self.bpmn_models = GenerateBPMN.generate_BPMN(*self.generation_para_list)
            number_of_models = len(self.bpmn_models)

            # Clear the list widget before populating it
            self.output_list_widget.clear()

            # Display generated BPMN model seeds in the list widget with prefix
            for i, model in enumerate(self.bpmn_models):
                self.output_list_widget.addItem(f"Model {i + 1}: {model[1]}")  # Add the model seed with prefix

            # Show a success message
            QMessageBox.information(self, "Success", f"{number_of_models} BPMN models generated.")

        except Exception as e:
            # Handle any errors that occur during the generation process
            QMessageBox.critical(self, "Error", f"An error occurred during BPMN model generation: {e}")

    def visualize_model(self):
        # Get the selected item
        selected_item = self.output_list_widget.currentRow()
        if selected_item != -1:  # Check if an item is selected
            selected_model = self.bpmn_models[selected_item][0]  # Get the corresponding model from the list
            # Call the visualize function with the selected model
            gviz = GenerateBPMN.visualization(selected_model)
            if gviz:
                self.display_graph(gviz)
        else:
            QMessageBox.warning(self, "Warning", "Please select a model seed to visualize.")

    def display_graph(self, gviz):
        # Save the graph as a PNG file
        png_path = "../../Graph/temp_graph"
        gviz.render(filename=png_path, format="png", cleanup=True)

        # Load the PNG image and get its dimensions
        pixmap = QPixmap(png_path + ".png")

        # Set the scaled pixmap to the QLabel
        self.graph_label.setPixmap(pixmap.scaledToWidth(self.graph_label.width(), Qt.SmoothTransformation))

    def save_models(self):
        # Open a file dialog for the user to select a folder
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", "../../models/")

        if folder_path:  # If a folder is selected
            try:
                src.Backend.GenerateBPMN.write_bpmn_to_file(self.bpmn_models, folder_path)

                QMessageBox.information(self, "Success", "Models saved successfully.")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while saving the models: {e}")
        else:
            QMessageBox.information(self, "Info", "Save operation canceled.")

    def resizeEvent(self, event):
        if self.graph_label.pixmap():
            png_path = "../../Graph/temp_graph"
            pixmap = QPixmap(png_path + ".png")
            self.graph_label.setPixmap(pixmap.scaledToWidth(self.graph_label.width(), Qt.SmoothTransformation))

        super().resizeEvent(event)


def main():
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)

    modern_window = BPMNWidget()

    # Show the widget as a window
    modern_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
