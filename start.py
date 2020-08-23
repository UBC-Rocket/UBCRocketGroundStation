from com_window.main import *

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = comWindow()
    window.show()
    sys.exit(app.exec_())
