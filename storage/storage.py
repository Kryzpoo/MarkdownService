import sqlite3

from storage.document import DocumentStatus

connection: sqlite3.Connection = None
cursor: sqlite3.Cursor = None


def init(storage_name):
    """
    Initializing DB: connecting, check if tables are created.

    :param storage_name: full name of .db file
    """
    global connection, cursor
    connection = sqlite3.connect(storage_name, check_same_thread=False, timeout=10)
    cursor = connection.cursor()
    try:
        # Check table 'documents' is created
        cursor.execute("SELECT 1 FROM documents").fetchall()
    except sqlite3.OperationalError:
        _create_db()


def close():
    """
    Close connection
    """
    cursor.close()
    connection.close()


def _create_db():
    cursor.execute(
        """
        CREATE TABLE documents
        (
            name TEXT UNIQUE,
            file_content TEXT,
            doc_type TEXT,
            encoding TEXT,
            status TEXT
        )
        """
    )
    connection.commit()


def save_document(content, name, doc_type, encoding):
    try:
        cursor.execute(
            """
            INSERT INTO documents
            (name, file_content, doc_type, encoding, status)
            VALUES
            ("{name}", "{file_content}", "{doc_type}", "{encoding}", "{status}")
            """.format(
                name=name,
                file_content=content,
                doc_type=doc_type,
                encoding=encoding,
                status=DocumentStatus.PROCESSING.name
            )
        )
        connection.commit()
    except sqlite3.IntegrityError as e:
        return e
    return None


def get_document_status(name):
    status = cursor.execute(
        """
        SELECT status FROM documents
        WHERE name = "{name}"
        """.format(name=name)
    ).fetchone()
    if status:
        return DocumentStatus[status[0]]
    else:
        return None


def set_document_status(name, status: DocumentStatus):
    cursor.execute(
        """
        UPDATE documents
        SET status = "{status}"
        WHERE name = "{name}"
        """.format(status=status.name,
                   name=name)
    )
    connection.commit()


def get_processing_documents():
    return cursor.execute(
        """
        SELECT name, doc_type, file_content FROM documents
        WHERE status = "{status}"
        """.format(status=DocumentStatus.PROCESSING.name)
    ).fetchall()


def get_documents_statuses():
    return cursor.execute(
        """
        SELECT name, status FROM documents
        """
    ).fetchall()
