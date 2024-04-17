import gradio as gr
import os
import json
from urllib.parse import quote
from azure.storage.blob import BlobClient
from PIL import Image
import io
import fitz
from utils import blob_base_url, sas_token


def update_seen(file_path, seen=None):
    seen = {} if not seen else seen
    if os.path.exists(file_path):
        labelled = open(file_path, 'r').read().strip()
        if labelled:
            labelled = labelled.split('\n')
            labelled = [json.loads(row) for row in labelled]
            doc_names = set([row['doc_name'] for row in labelled])
            for doc_name in doc_names:
                seen[doc_name] = [row['page'] for row in labelled if row['doc_name'] == doc_name]
    return seen


class ImageOutputter:
    def __init__(self, files_path, labels_path, errors_path, skipped_path, show_skipped=False):
        self.seen = update_seen(labels_path)
        self.seen = update_seen(errors_path, self.seen)
        if not show_skipped:
            self.seen = update_seen(skipped_path, self.seen)

        self.file_names = open(files_path).read().strip().split('\n')
        self.labels_file = open(labels_path, 'a')
        self.errors_file = open(errors_path, 'a')
        self.skipped_file = open(skipped_path, 'a')

        self.idx = -1
        self.load_next_pdf()

    def load_next_pdf(self):
        if self.idx == len(self.file_names):
            self.idx = -1

        self.idx += 1
        self.doc_name = self.file_names[self.idx]
        self.get_doc()
        if self.doc_name not in self.seen or len(self.seen[self.doc_name]) < self.doc_length:
            self.page = 0
            if self.doc_name in self.seen:
                for page in range(self.doc_length):
                    if page not in self.seen[self.doc_name]:
                        self.page = page
                        break
        else:
            return self.load_next_pdf()

    def get_doc(self):
        doc_name = quote(self.doc_name)
        blob_url = f"{blob_base_url}{doc_name}"
        url = f"{blob_url}?{sas_token}"
        blob_client = BlobClient.from_blob_url(url)
        pdf_stream = io.BytesIO(blob_client.download_blob().readall())
        self.doc = fitz.open(stream=pdf_stream, filetype="pdf")
        self.doc_length = len(self.doc)

    def get_page_image(self):
        page = self.doc.load_page(self.page)
        pix = page.get_pixmap()
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def get_next_image(self, record_in_seen=True):
        page = None

        if self.doc_name in self.seen:
            for page in range(max(0, self.page), self.doc_length):
                if page not in self.seen[self.doc_name]:
                    break
        else:
            page = 0
            self.seen[self.doc_name] = []

        if page == None or self.page == self.doc_length-1:
            self.load_next_pdf()

        else:
            self.page = page
            self.seen[self.doc_name].append(page)

        return self.get_page_image()

    def get_next(self):
        img = self.get_next_image()
        doc_image = gr.Image(img, type="pil")
        idx = gr.Slider(value=self.idx, label="idx")
        doc = gr.Textbox(f'Name: {self.doc_name}')
        page = gr.Textbox(f'Page: {self.page}')
        return idx, doc, page, doc_image

    def record_label(self, doc_class):
        jsn = {'doc_name': self.doc_name, 'page': self.page, 'doc_class': doc_class}
        self.labels_file.write(json.dumps(jsn) + '\n')
        return self.get_next()

    def record_error(self, error_type):
        jsn = {'doc_name': self.doc_name, 'page': self.page, 'error': error_type}
        self.errors_file.write(json.dumps(jsn) + '\n')
        return self.get_next()

    def record_skipped_page(self):
        jsn = {'doc_name': self.doc_name, 'page': self.page}
        self.skipped_file.write(json.dumps(jsn) + '\n')

    def skip_page(self):
        self.record_skipped_page()
        return self.get_next()

    def skip_file(self):
        if self.doc_name not in self.seen:
            self.seen[self.doc_name] = []
        self.seen[self.doc_name] += list(range(self.page, self.doc_length))

        for page in range(self.doc_length):
            self.page = page
            self.record_skipped_page()

        self.load_next_pdf()
        return self.get_next()

    def to_next_page(self):
        if self.page < self.doc_length-1:
            if self.doc_name in self.seen and self.page+1 in self.seen[self.doc_name]:
                self.seen[self.doc_name].remove(self.page+1)
        else:
            next_doc_name = self.file_names[self.idx+1]
            if next_doc_name in self.seen:
                self.seen[next_doc_name] = self.seen[next_doc_name][1:]

        return self.get_next()

    def to_prev_page(self):
        if self.page > 0:
            self.page -= 2
            if self.doc_name in self.seen:
                self.seen[self.doc_name].remove(self.page+1)
        else:
            prev_doc_name = self.file_names[self.idx-1]
            if prev_doc_name in self.seen:
                self.seen[prev_doc_name] = self.seen[prev_doc_name][:-1]

            self.idx -= 2
            self.load_next_pdf()
            self.page = self.doc_length - 2

        return self.get_next()

    def finish(self):
        self.labels_file.close()
        self.errors_file.close()
        self.skipped_file.close()
