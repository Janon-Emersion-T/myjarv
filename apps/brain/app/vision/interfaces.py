from dataclasses import dataclass


@dataclass(slots=True)
class VisionRequest:
    image_path: str
    task: str


class VisionProvider:
    def analyze(self, request: VisionRequest) -> dict:
        raise NotImplementedError

