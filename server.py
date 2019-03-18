import os

from flask import Flask, request, Response, render_template, send_from_directory

import storage
from document import DocumentStatus, DocumentType

app = Flask(__name__)
posts_dir = os.path.join(os.getcwd(), 'posts')


@app.route("/upload", methods=["POST"])
def upload():
    document = request.files.get("document")
    if not document:
        error = "Document not found"
        print(error)  # todo log
        return Response(error, 500)
    encoding = request.form.get("encoding", "UTF-8")
    name = request.form.get("name", document.filename)
    doc_type = request.form.get("doc_type", DocumentType.MD.name)
    content = document.stream.read().decode(encoding)
    save_error = storage.save_document(content, name, doc_type, encoding)
    if save_error:
        return Response(str(save_error), 500)

    return Response("Document uploaded", 200)


@app.route("/posts/<path:name>")
def get_post(name):
    post_status = storage.get_document_status(name)
    if not post_status:
        return Response("No such document", 404)
    if post_status is DocumentStatus.PROCESSING:
        return Response("Still processing document")
    if post_status is DocumentStatus.PROCESSED:
        return send_from_directory(posts_dir, "{}.html".format(name))


@app.route("/")
def get_posts():
    documents = storage.get_documents_statuses()
    processed = [d[0] for d in documents if d[1] == DocumentStatus.PROCESSED.name]
    processing = [d[0] for d in documents if d[1] == DocumentStatus.PROCESSING.name]
    return render_template("index.html",
                           processed=processed,
                           processing=processing)
