import time
from multiprocessing import Process

import os

from document import DocumentStatus, DocumentType
import storage


class Processor(Process):

    remove_marker = "~TO REMOVE~"

    def __init__(self, process_period, storage_name):
        super().__init__()
        self.running = True
        self.period = process_period
        self.storage_name = storage_name

    def run(self):
        storage.init(self.storage_name)
        while self.running:
            self.infinite_process()

    def stop(self):
        self.running = False

    def infinite_process(self):
        documents_to_process = storage.get_processing_documents()
        for doc_name, doc_type, content in documents_to_process:
            file_content = DocumentType[doc_type].process(content)
            with open("posts/{}.html".format(doc_name), "w+") as f:
                f.write(file_content)
            storage.set_document_status(doc_name, DocumentStatus.PROCESSED)
        time.sleep(self.period)


class ContentProcessor:

    @classmethod
    def process(cls, doc_type, content):
        processor = None
        if doc_type == DocumentType.MD:
            processor = MDProcessor
        if processor is None:
            raise ValueError("Processor not defined by document type {doc_type}."
                             "Available types: {types}".format(doc_type=doc_type,
                                                               types=[t.value for t in DocumentType]))
        return processor.process(content)


class MDProcessor:

    @classmethod
    def process(cls, content: str):
        content = cls.set_html_headers(content)
        content = cls.set_html_lists(content)
        content = content.replace(os.linesep + Processor.remove_marker, "")
        return """
            <!DOCTYPE html>
            <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <title>Post</title>
                </head>
                <body>
                    {}
                </body>
            </html>
        """.format(content)

    @staticmethod
    def set_html_headers(content):
        for idx, line in enumerate(content.splitlines()):
            if line.lstrip().startswith("#"):
                h_level = 1
                for letter in line[1:]:
                    if letter == "#":
                        h_level += 1
                        if h_level == 6:
                            break
                    else:
                        break
                content = content.replace(line,
                                          "<h{h_level}>{line}</h{h_level}>".format(
                                              h_level=h_level,
                                              line=line[h_level:]))

            for md_header, html_header in (("=", "h1"), ("-", "h2")):
                if line and line.strip().count(md_header) == len(line.strip()):
                    if idx > 0:
                        split_content = content.splitlines()
                        prev_line = split_content[idx-1]
                        content = content.replace(prev_line,
                                                  "<{header}>{line}</{header}>".format(
                                                      header=html_header,
                                                      line=prev_line))
                        content = content.replace(line, Processor.remove_marker)

        return content

    @staticmethod
    def set_html_lists(content):
        return content
