from powerpwn.copilot.dump.input_extractor.input_file_reader import InputFileReader


class DocumentInputExtractor:
    def __init__(self) -> None:
        self.__input_file_reader = InputFileReader()

    def extract(self, file_path) -> list:
        extracted_documents_names = []
        documents = self.__input_file_reader.read_lines(file_path)
        for document in documents:
            if not document.startswith("["):
                extracted_documents_names.append(document)
            else:
                splitted_doc = document.split("[")
                if len(splitted_doc) > 1:
                    splitted_doc = splitted_doc[1]
                    if "]" in splitted_doc:
                        splitted_doc = splitted_doc.split("]")[0]
                        extracted_documents_names.append(splitted_doc)
        return extracted_documents_names
