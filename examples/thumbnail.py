import io
import flask
import requests
from PIL import Image
from bismuth import API, BlobStorage

class ThumbnailerAPI(API):
    def __init__(self):
        super().__init__()
        self.add_route('/thumbnail', {"POST": self.thumbnail})
        self.storage = BlobStorage()

    def thumbnail(self, request: flask.Request, url: str):
        cached = self.storage.retrieve(url)
        if cached:
            return flask.send_file(io.BytesIO(cached), mimetype='image/png')

        image_file = requests.get(url).content
        img = Image.open(image_file)
        img.thumbnail((100, 100))
        thumb_io = io.BytesIO()
        img.save(thumb_io, format='PNG')
        thumb_io.seek(0)
        self.storage.create(url, thumb_io.getvalue())

        return flask.send_file(thumb_io, mimetype='image/png')

app = ThumbnailerAPI()
