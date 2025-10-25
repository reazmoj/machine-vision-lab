from app.utils.base_reid import BaseReidModel
import torch

# class FSRAModel(BaseReidModel):
#     def _load_model(self):
#         self.model = torch.load(self.model_path)

#     def predict(self, image):
#         result = self.model.predict(image)
#         return result[0].plot()
