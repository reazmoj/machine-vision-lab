# Machine Vision Lab

A comprehensive desktop application built with PyQt6 for various computer vision tasks including object detection and person re-identification (ReID). The application provides an intuitive graphical interface for performing complex vision tasks with ease.

## 🌟 Features

- **Object Detection**
  - Support for multiple detection models (YOLOv5, YOLOv8, YOLOv9, RCNN)
  - Real-time detection capabilities
  - Customizable detection parameters
  - Visual result display

- **Person Re-Identification (ReID)**
  - Advanced person re-identification using FSRA (Feature Space Re-Arrangement) model
  - Gallery management for person images
  - Efficient person matching and retrieval
  - Visual result presentation

- **User Interface**
  - Modern and intuitive interface built with PyQt6
  - Dark and light theme support
  - Responsive design
  - Easy navigation between different functionalities

## 🛠️ Requirements

### Software Requirements
- Python 3.8 or higher
- CUDA compatible GPU (recommended for optimal performance)
- CUDA Toolkit and cuDNN (for GPU acceleration)

### Python Packages
```bash
pip install -r app/config/requirements.txt
```

Main dependencies include:
- PyQt6==6.6.0
- PyQt6-WebEngine==6.6.0
- torch (compatible with your CUDA version)
- torchvision
- opencv-python
- numpy
- Other dependencies as listed in requirements.txt

### Model Files
Place the following model files in the `app/models/` directory:

#### Detection Models
-  YOLOv models weights

#### ReID Models
- `net_119.pth` - FSRA model weights for person re-identification

## 🚀 Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/reazmoj/machine-vision-lab.git
cd machine-vision-lab
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r app/config/requirements.txt
```

4. Download model files:
   - Download the required model files mentioned above
   - Place them in the `app/models/` directory

5. Configure the application:
   - Review and adjust settings in `app/config/config.json`
   - Ensure all paths in the configuration point to valid locations

## 🎯 Usage

1. Start the application:
```bash
python app/view/main_window.py
```

2. Navigate through different interfaces:
   - Home Page: Overview and quick access to features
   - Detection: Object detection interface
   - ReID: Person re-identification interface
   - Settings: Application configuration

## 📋 Project Structure

```
app/
├── common/          # Common utilities and configurations
├── components/      # Reusable UI components
├── config/         # Configuration files
├── models/         # Model weights and configurations
├── utils/          # Utility functions for ML operations
└── view/           # UI interfaces and main application windows
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Contact

For any queries or suggestions, please open an issue in the GitHub repository.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped with the development
- Special thanks to the creators of PyQt6 and the machine learning models used in this project
