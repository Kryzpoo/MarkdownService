import time
from multiprocessing import Process

import os

from document import DocumentStatus, DocumentType
import storage


class Processor(Process):
    """
    Separated process
    """

    def __init__(self, process_period, storage_name):
        """
        :param process_period: period to wait between processing
        :param storage_name: name to initialize storage
        """
        super().__init__()
        self.running = True
        self.period = process_period
        self.storage_name = storage_name

    def run(self):
        # Init db from this process
        storage.init(self.storage_name)
        while self.running:
            self.infinite_process()

    def stop(self):
        """
        Mark process to stop
        """
        self.running = False

    def infinite_process(self):
        """
        File processing
        """
        documents_to_process = storage.get_processing_documents()
        for doc_name, doc_type, content in documents_to_process:
            # Process file depending on doc_type
            file_content = ContentProcessor.process(doc_type, content)
            with open("posts/{}.html".format(doc_name), "w+") as f:
                f.write(file_content)
            storage.set_document_status(doc_name, DocumentStatus.PROCESSED)
        time.sleep(self.period)


class ContentProcessor:
    """
    Entry point to process files
    """

    @classmethod
    def process(cls, doc_type, content):
        """
        Processing of file content

        :param doc_type: document type from document.DocumentType enum
        :param content: content to process, string
        :return: processed content, string
        """
        processor = None

        # Document types (to add)
        if doc_type == DocumentType.MD.name:
            processor = MDProcessor

        if processor is None:
            raise ValueError("Processor not defined by document type {doc_type}."
                             "Available types: {types}".format(doc_type=doc_type,
                                                               types=[t.name for t in DocumentType]))
        return processor.transform_content(content)


class MDProcessor:

    @classmethod
    def transform_content(cls, content: str):
        """
        Transform .md file content to .html file content

        :param content: string
        :return: .html content string
        """
        content = cls.set_html_headers(content)
        content = cls.set_html_ul(content)  # Only unordered lists starting with "+"
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

    @classmethod
    def set_html_headers(cls, content):
        """
        Transfrom .md headers to .html headers

        :param content: string
        :return: string
        """
        md_content_lines = content.splitlines()
        html_content_lines = []

        for idx, line in enumerate(content.splitlines()):

            # Processing headers starting with '#'
            if line.lstrip().startswith("#"):
                h_level = 1
                for letter in line[1:]:
                    if letter == "#":
                        h_level += 1
                        # Max header level is 6
                        if h_level > 6:
                            break
                    elif letter == " ":
                        break
                if h_level > 6:
                    # Header incorrect. Append raw line
                    html_content_lines.append(line)
                    break
                html_content_lines.append("<h{h_level}>{line}</h{h_level}>".format(h_level=h_level,
                                                                                   line=line[h_level + 1:]))
            else:
                html_content_lines.append(line)

            # Processing underlined headers
            for md_header, html_header in (("=", "h1"), ("-", "h2")):
                if len(line) > 1 and line.strip().count(md_header) == len(line.strip()):
                    if idx > 0:
                        prev_line = md_content_lines[idx - 1]
                        html_content_lines = html_content_lines[:-2]
                        html_content_lines.append("<{header}>{line}</{header}>".format(header=html_header,
                                                                                       line=prev_line))
        return os.linesep.join(html_content_lines)

    @classmethod
    def _is_start_li(cls, line):
        return line.lstrip().startswith("+ ")

    @classmethod
    def _is_same_level(cls, level1, level2):
        return level1 == level2

    @classmethod
    def _is_empty_line(cls, line):
        return len(line.strip()) == 0

    @classmethod
    def _append_li(cls, html_content_lines, line):
        html_content_lines.append("<li>" + line[line.find("+ ") + 2:] + "</li>")

    @classmethod
    def _start_ul(cls, md_content_lines, html_content_lines, prev_list_levels, line):
        html_content_lines.append("<ul>")

        while line is not None:
            if cls._is_start_li(line):
                cur_list_level = len(line) - len(line.lstrip())
                if cls._is_same_level(cur_list_level, prev_list_levels[-1]):
                    cls._append_li(html_content_lines, line)
                else:
                    if cur_list_level in prev_list_levels:
                        html_content_lines.append("</ul>")
                        cls._append_li(html_content_lines, line)
                        return
                    else:
                        prev_list_levels.append(cur_list_level)
                        cls._start_ul(md_content_lines, html_content_lines, prev_list_levels, line)  # Recursion
            else:
                if cls._is_empty_line(line):
                    html_content_lines.append(line)
                    break
                else:
                    html_content_lines.append("</ul>")
                    html_content_lines.append(line)
                    return
            line = next(md_content_lines, None)
        html_content_lines.append("</ul>")

    @classmethod
    def set_html_ul(cls, content):
        """
        Transform .md unordered lists to .html unordered lists

        :param content: string
        :return: string
        """
        md_content_lines = iter(content.splitlines())
        html_content_lines = []

        line = True
        while line is not None:
            line = next(md_content_lines, None)
            if line:
                if cls._is_start_li(line):
                    cur_list_level = len(line) - len(line.lstrip())
                    cls._start_ul(md_content_lines, html_content_lines, [cur_list_level], line)
                else:
                    html_content_lines.append("<p>" + line + "</p>")

        return os.linesep.join(html_content_lines)
