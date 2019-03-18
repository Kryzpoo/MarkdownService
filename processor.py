import re
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
        storage.close()

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

    header_symbol = "#"
    header_matcher = "^\s*" + header_symbol + "{1,6}\s+"

    @classmethod
    def _is_start_header(cls, line):
        return re.search(cls.header_matcher, line) is not None

    @classmethod
    def _get_header_level(cls, line: str):
        return len(line.lstrip()[:line.rfind("#")]) + 1

    @classmethod
    def _get_header_content(cls, line: str):
        return line.lstrip(" #\t")

    @classmethod
    def _append_header(cls, html_content_lines, line, header_level):
        html_content_lines.append("<h{level}>{line}</h{level}>".format(level=header_level,
                                                                       line=cls._get_header_content(line)))

    @classmethod
    def _is_line_consists_of(cls, line, md_header_symbol):
        return len(line) > 1 and line.strip().count(md_header_symbol) == len(line.strip())

    @classmethod
    def set_html_headers(cls, content):
        """
        Transform .md headers to .html headers

        :param content: string
        :return: string
        """
        html_content_lines = []

        for line in (content.splitlines()):

            # Processing headers starting with '#'
            if cls._is_start_header(line):
                header_level = cls._get_header_level(line)
                cls._append_header(html_content_lines, line, header_level)
            else:
                # Processing underlined headers
                for md_header_symbol, header_level in (("=", "h1"), ("-", "h2")):
                    if cls._is_line_consists_of(line, md_header_symbol):
                        html_content_lines.pop()
                        cls._append_header(html_content_lines, line, header_level)
                else:
                    # Append common line
                    html_content_lines.append(line)
        return os.linesep.join(html_content_lines)

    list_markers = ("+ ", "- ", "* ")
    all_list_markers = "".join(list_markers)

    @classmethod
    def _is_start_li(cls, line):
        line_lstrip = line.lstrip()
        for marker in cls.list_markers:
            if line_lstrip.startswith(marker) and len(line_lstrip) > len(marker):
                return True
        else:
            return False

    @classmethod
    def _get_list_marker(cls, line):
        return line.lstrip()[0]

    @classmethod
    def _is_same_level(cls, level1, level2):
        return level1 == level2

    @classmethod
    def _is_empty_line(cls, line):
        return len(line.strip()) == 0

    @classmethod
    def _append_li(cls, html_content_lines, line):
        html_content_lines.append("<li>" + line.lstrip(cls.all_list_markers) + "</li>")

    @classmethod
    def _start_ul(cls, md_content_lines, html_content_lines, prev_list_levels, prev_list_marker, line):
        """
        Start new list/sublist cycle

        :param md_content_lines: list with md content lines
        :param html_content_lines: list with html content lines
        :param prev_list_levels: previous levels sublists
        :param prev_list_marker: previous list marker
        :param line: current line of md content
        """
        html_content_lines.append("<ul>")
        prev_line_is_empty = False

        while line is not None:
            if cls._is_start_li(line):
                cur_list_level = len(line) - len(line.lstrip())
                cur_list_marker = cls._get_list_marker(line)

                if cur_list_marker != prev_list_marker:
                    # Other marker = end all lists
                    for _ in prev_list_levels:
                        html_content_lines.append("</ul>")

                    # and start new list
                    cls._start_ul(md_content_lines, html_content_lines, [cur_list_level],
                                  cur_list_marker, line)  # Recursion
                    return

                if cls._is_same_level(cur_list_level, prev_list_levels[-1]):
                    # Next element of the list
                    cls._append_li(html_content_lines, line)
                else:
                    if cur_list_level in prev_list_levels:
                        # This is the end of current sublist so stop it
                        html_content_lines.append("</ul>")
                        cls._append_li(html_content_lines, line)
                        prev_list_levels.pop()

                        # and continue previous lists
                        return

                    else:
                        # This is new sublist so remember current level
                        prev_list_levels.append(cur_list_level)

                        # And start other inner list
                        cls._start_ul(md_content_lines, html_content_lines, prev_list_levels,
                                      cur_list_marker, line)  # Recursion
            else:
                if cls._is_empty_line(line):
                    # Remember empty line to stop list if there is no elements
                    prev_line_is_empty = True
                    html_content_lines.append(line)
                else:
                    if prev_line_is_empty:
                        # Stop list with all sublists
                        for _ in prev_list_levels:
                            html_content_lines.append("</ul>")

                    # And start new paragraph
                    html_content_lines.append(line)
                    prev_line_is_empty = False

            line = next(md_content_lines, None)

        html_content_lines.append("</ul>")

    @classmethod
    def set_html_ul(cls, content):
        """
        Transform .md unordered lists to .html unordered lists
        Using iterator and remember previous states of list marker/list levels

        :param content: string
        :return: string
        """
        content_lines = content.splitlines()
        html_content_lines = []

        md_content_lines = iter(content_lines)
        line = ""
        while line is not None:
            line = next(md_content_lines, None)
            if line:
                if cls._is_start_li(line):
                    cur_list_level = len(line) - len(line.lstrip())
                    line_marker = cls._get_list_marker(line)
                    cls._start_ul(md_content_lines, html_content_lines, [cur_list_level], line_marker, line)
                else:
                    html_content_lines.append(line)
                    html_content_lines.append("<br>")

        return os.linesep.join(html_content_lines)
