import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTextEdit, QVBoxLayout, QAction, QMenuBar, QToolBar, QStatusBar
import qtmodern.styles


class CoppaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Set the main window title and initial size
        self.setWindowTitle("CoPPA Trainer")
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Set up a layout for the central widget
        layout = QVBoxLayout(central_widget)

        # Add a text editor to the central widget
        self.text_edit = QTextEdit(self)
        layout.addWidget(self.text_edit)

        load_preset_action = QAction("Load Preset", self)

        # Create a menu bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(load_preset_action)

        # Add actions to the menu bar
        load_action = QAction("Load JSON", self)
        feature_action = QAction("Feature engineering", self)


        # Create a toolbar
        toolbar = QToolBar("Main Toolbar", self)
        self.addToolBar(toolbar)
        toolbar.addAction(load_action)
        toolbar.addAction(feature_action)

        # Create a status bar
        self.statusBar().showMessage("No log file loaded")


def main():
    app = QApplication(sys.argv)
    qtmodern.styles.dark(app)
    main_window = CoppaMainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()