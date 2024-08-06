from typing_extensions import override

from powerpwn.copilot.loggers.ilogger import ILogger


class FileLogger(ILogger):
    def __init__(self, file_path: str):
        self.__file_path = file_path

    @override
    def log(self, message: str) -> None:
        with open(self.__file_path, "a") as file:
            file.write(message + "\n\n")

    def read(self) -> None:
        with open(self.__file_path, "r") as file:
            for line in file.readlines():
                if line != "\n":
                    line = line.split("\n")[0]
                    print(line)


if __name__ == "__main__":
    f = FileLogger("temp.txt")
    # f.log("hi")
    # f.log("bi")
    f.read()
