from pathlib import Path

import safitty


class ImageReader:
    def __init__(self, width: int = 1024, height: int = 1024, grayscale: bool = False):
        self.width = width
        self.height = height
        self.grayscale = grayscale

    def __str__(self) -> str:
        return f"({self.height, self.width}), grayscale = {self.grayscale}"


if __name__ == "__main__":
    config = safitty.load_config("config.yml")

    path = safitty.get(config, "paths", "images", default="images/", apply=Path)
    print(type(path))  # pathlib.PosixPath

    if safitty.get(config, "reader", "need_reader", default=False):
        reader = safitty.get(config, "reader", "params", apply=ImageReader)
        print(reader)  # ((521, 512)), grayscale = True
