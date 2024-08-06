import os


class InputFileReader:
    def read_lines(self, file_path: str) -> list:
        lines = []
        if not os.path.exists(file_path):
            return []
        with open(file_path, "r") as file:
            for line in file.readlines():
                if line != "\n":
                    line = line.split("\n")[0]
                    lines.append(line)

        return lines
