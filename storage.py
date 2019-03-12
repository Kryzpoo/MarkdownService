import sqlite3

from document import DocumentStatus


storage_name = ""
connection: sqlite3.Connection = None
cursor: sqlite3.Cursor = None


def init():
    global connection, cursor
    connection = sqlite3.connect(storage_name, check_same_thread=False, timeout=10)
    cursor = connection.cursor()
    table_list = cursor.execute("SELECT * FROM sqlite_master").fetchall()
    if not table_list:
        _create_db()


def close():
    cursor.close()
    connection.close()


def _create_db():
    cursor.execute(
        """
        CREATE TABLE documents
        (
            name TEXT UNIQUE,
            file_content TEXT,
            encoding TEXT,
            status TEXT
        )
        """
    )
    connection.commit()


def save_document(content, name, encoding):
    try:
        cursor.execute(
            """
            INSERT INTO documents
            (name, file_content, encoding, status)
            VALUES
            ("{name}", "{file_content}", "{encoding}", "{status}")
            """.format(
                name=name,
                file_content=content,
                encoding=encoding,
                status=DocumentStatus.PROCESSING.name
            )
        )
        connection.commit()
    except sqlite3.IntegrityError as e:
        print(e)  # todo log
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


def get_document(name):
    return cursor.execute(
        """
        SELECT * FROM documents
        WHERE name = "{name}"
        """.format(name=name)
    ).fetchone()


def get_processed_documents():
    return cursor.execute(
        """
        SELECT name FROM documents
        WHERE status = "{status}"
        """.format(status=DocumentStatus.PROCESSED.name)
    ).fetchall()


def get_processing_documents():
    return cursor.execute(
        """
        SELECT name, file_content FROM documents
        WHERE status = "{status}"
        """.format(status=DocumentStatus.PROCESSING.name)
    ).fetchall()


def get_documents_statuses():
    return cursor.execute(
        """
        SELECT name, status FROM documents
        """
    ).fetchall()
