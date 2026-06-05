from dataclasses import dataclass


@dataclass(slots=True)
class VisionConfig:
    object_detector: str = "yolo"
    ocr_provider: str = "tesseract"
    image_processor: str = "opencv"
    screenshot_analyzer: str = "opencv"

