import yaml
from pathlib import Path

import safitty as sf


class ImageReader:
    def __init__(self, width: int = 1024, height: int = 1024, grayscale: bool = False):
        self.width = width
        self.height = height
        self.grayscale = grayscale

    def __str__(self) -> str:
        return f"({self.height, self.width}), grayscale = {self.grayscale}"


if __name__ == "__main__":
    with open("config.yml") as stream:
        config = yaml.load(stream)

    path = sf.safe_get(config, "paths", "images", default="images/", transform=Path)
    print(type(path))  # pathlib.PosixPath

    if sf.safe_get(config, "reader", "need_reader", default=False):
        reader = sf.safe_get(config, "reader", "params", apply=ImageReader)
        print(reader)  # ((521, 512)), grayscale = True
