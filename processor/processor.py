import time
from multiprocessing import Process

from processor.md_processor import MDProcessor
from storage.document import DocumentStatus, DocumentType
from storage import storage


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
