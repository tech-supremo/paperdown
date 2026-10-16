import base64
import importlib
import sys
import types
import zipfile
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient

from app import converter
from app.converter import convert_document
from app.main import app


def picture():
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 80, 60), False)
    pix.clear_with(120)
    return pix.tobytes('png')


def test_embedded_image_order_and_real_png():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((30, 30), 'Before picture.')
    page.insert_image(fitz.Rect(30, 60, 150, 150), stream=picture())
    page.insert_text((30, 200), 'After picture.')
    result = convert_document(doc)
    assert len(result.images) == 1
    asset = result.images[0]
    assert result.markdown.index('Before picture.') < result.markdown.index(asset.path)
    assert result.markdown.index(asset.path) < result.markdown.index('After picture.')
    png = fitz.Pixmap(base64.b64decode(asset.content))
    assert (png.width, png.height) == (240, 180)


def test_vector_page_gets_one_snapshot_including_images():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((30, 30), 'Sales chart')
    page.draw_rect(fitz.Rect(30, 80, 80, 140), fill=(0, 0.5, 1))
    page.insert_image(fitz.Rect(120, 80, 200, 140), stream=picture())
    result = convert_document(doc)
    assert len(result.images) == 1
    assert 'visual reference' in result.markdown
    assert result.markdown.index('Sales chart') < result.markdown.index('![')
    png = fitz.Pixmap(base64.b64decode(result.images[0].content))
    assert max(png.width, png.height) <= 1601


@pytest.mark.parametrize('rotation', [0, 90, 180, 270])
def test_image_only_and_rotated_pages(rotation):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(30, 60, 150, 150), stream=picture())
    page.set_rotation(rotation)
    result = convert_document(doc)
    assert len(result.images) == 1
    png = fitz.Pixmap(base64.b64decode(result.images[0].content))
    assert png.width > 0 and png.height > 0
    assert min(png.samples) == 120  # Actual picture, not an empty crop.


def test_api_returns_local_asset_and_text_only_has_no_assets():
    client = TestClient(app)
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((30, 30), 'Readable text.')
    response = client.post('/convert', files={'file': ('report.pdf', doc.tobytes(), 'application/pdf')})
    assert response.status_code == 200
    assert response.json()['images'] == []
    page.insert_image(fitz.Rect(30, 60, 150, 150), stream=picture())
    response = client.post('/convert', files={'file': ('report.pdf', doc.tobytes(), 'application/pdf')})
    result = response.json()
    assert response.status_code == 200
    assert result['filename'] == 'report.md'
    assert result['images'][0]['path'] in result['markdown']
    assert base64.b64decode(result['images'][0]['content']).startswith(b'\x89PNG')


def test_graphics_limit_has_actionable_error(monkeypatch):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(30, 60, 150, 150), stream=picture())
    monkeypatch.setattr(converter, 'MAX_IMAGE_BYTES', 1)
    response = TestClient(app).post('/convert', files={'file': ('report.pdf', doc.tobytes(), 'application/pdf')})
    assert response.status_code == 413
    assert 'Split' in response.json()['detail']


def test_native_zip_writes_binary_assets_and_relative_links(tmp_path, monkeypatch):
    # The bridge is independent of the platform-specific native window.
    monkeypatch.setitem(sys.modules, 'webview', types.SimpleNamespace())
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    desktop = importlib.import_module('desktop')
    api = desktop.DesktopApi()
    destination = tmp_path / 'result.zip'
    monkeypatch.setattr(api, '_save_path', lambda name: destination)
    png = picture()
    assert api.save_zip([
        {'path': 'report.md', 'content': '![Picture](images/picture.png)'},
        {'path': 'images/picture.png', 'content': base64.b64encode(png).decode(), 'encoding': 'base64'},
    ])
    with zipfile.ZipFile(destination) as archive:
        assert archive.read('images/picture.png') == png
        assert b'(images/picture.png)' in archive.read('report.md')
