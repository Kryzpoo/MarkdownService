import os

from flask import Flask, request, Response, render_template, send_from_directory

import storage
from document import DocumentStatus, DocumentType

app = Flask(__name__)
posts_dir = os.path.join(os.getcwd(), 'posts')


@app.route("/upload", methods=["POST"])
def upload():
    """
    Method: POST
    Content-Type: form-data
    Required fields: document (file)
    Other fields: doc_type (MD), encoding, name

    :return: Response(200, 422, 500)
    """
    document = request.files.get("document")
    if not document:
        return Response("Document not found", 422)

    doc_type = request.form.get("doc_type", DocumentType.MD.name)
    if doc_type not in [t.name for t in DocumentType]:
        return Response("Incorrect doc_type", 422)

    encoding = request.form.get("encoding", "UTF-8")
    try:
        content = document.stream.read().decode(encoding)
    except LookupError:
        return Response("Incorrect encoding", 422)

    name = request.form.get("name", document.filename)
    if not name:
        return Response("Incorrect name", 422)
    else:
        # Check filename is correct
        try:
            with open("posts/{}.html".format(name), "w+"):
                pass
        except (FileNotFoundError, OSError):
            return Response("Incorrect name", 422)

    save_error = storage.save_document(content, name, doc_type, encoding)
    if save_error:
        return Response(str(save_error), 500)

    return Response("Document uploaded", 200)


@app.route("/posts/<path:name>")
def get_post(name):
    """
    Method: GET
    Required fields: name

    :param name: name of uploaded post
    :return: Response(200, 404)
    """
    post_status = storage.get_document_status(name)
    if not post_status:
        return Response("Document not found", 404)
    elif post_status is DocumentStatus.PROCESSING:
        return Response("Still processing document")
    elif post_status is DocumentStatus.PROCESSED:
        return send_from_directory(posts_dir, "{}.html".format(name))


@app.route("/")
def get_posts():
    """
    Method: GET

    :return: Response(200)
    """
    documents = storage.get_documents_statuses()
    processed = [d[0] for d in documents if d[1] == DocumentStatus.PROCESSED.name]
    processing = [d[0] for d in documents if d[1] == DocumentStatus.PROCESSING.name]
    return render_template("index.html",
                           processed=processed,
                           processing=processing)
