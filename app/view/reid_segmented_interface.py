from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSizePolicy
from qfluentwidgets import SegmentedWidget, HorizontalFlipView, StateToolTip
from .navigation_view_interface import PivotInterface
from ..utils.reid_model import ReIdModelInfrence
import glob

class ReidSegmentedInterface(PivotInterface):

    Nav = SegmentedWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout.removeWidget(self.pivot)
        self.vBoxLayout.insertWidget(0, self.pivot)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    # def create_image_display2(self):
    #     """Override the method to use HorizontalFlipView instead of ClickableLabel."""
    #     self.imageDisplay2 = HorizontalFlipView()
    #     self.imageDisplay2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    #     self.imageDisplay2.setMinimumSize(300, 300)
    #     self.imageDisplay2.hide()
    

    def processImage(self, image_path, model_path, gallery_path):
        if self.stateTool == None:
            self.stateTool = StateToolTip(
                self.tr('Processing Model'), self.tr('Please wait patiently'), self.window())
            self.stateTool.move(self.stateTool.getSuitablePos())
            self.stateTool.show()

        self.detection_thread = ReIdModelInfrence(model_path, image_path, gallery_path)
        self.detection_thread.process_finished.connect(self.show_result)
        self.detection_thread.start()
    
    # def show_result(self, result):
        # image_list = []

        # if self.stateTool:
        #     self.stateTool.setContent(
        #         self.tr('The model processing is complete!'))
        #     self.stateTool.setState(True)
        #     self.stateTool = None  

        # for filename in glob.glob(result + '/*.jpg'):
        #     image_list.append(filename)
        
        # self.imageDisplay2.addImages(image_list)
        # self.imageDisplay2.show()


