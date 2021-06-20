

class Pin:
    """
    provides generic pin attributes to be inherited by other pin classes
    for HW sim
    """

    INPUT = 0
    OUTPUT = 1
    NOT_SET = -1

    def __init__(self):
        #could be updated later.  For now, sets the pin_mode to be default as an output
        self.pin_mode = self.NOT_SET

    def set_mode(self, mode):
        """
        sets value of pin_mode to mode -> INPUT = 0, OUTPUT = 1
        """
        if(mode==1):
            self.pin_mode = self.OUTPUT
        if(mode==0):
            self.pin_mode = self.INPUT

    def get_mode(self):
        """
        returns the current pin_mode
        """
        return self.pin_mode