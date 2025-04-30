from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from PIL import Image, ImageEnhance
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def clear_upload_folder(exclude=None):
    """Xoá tất cả ảnh trong thư mục upload trừ ảnh được chỉ định."""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path) and file_path != exclude:
                os.unlink(file_path)
        except Exception as e:
            print(f'Error deleting file {file_path}: {e}')

current_image_path = ''
original_image_path = ''

@app.route('/', methods=['GET', 'POST'])
def index():
    global current_image_path, original_image_path

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'upload':
            clear_upload_folder()  # Xóa tất cả ảnh cũ
            file = request.files['image']
            if file:
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                original_image_path = filepath
                current_image_path = filepath
                return jsonify({
                    'original': url_for('static', filename=f'uploads/{filename}'),
                    'processed': url_for('static', filename=f'uploads/{filename}')
                })

        elif action == 'update':
            return update_image()

    if request.args.get('action') == 'reset':
        clear_upload_folder()  # Xoá toàn bộ ảnh khi reset
        current_image_path = ''
        original_image_path = ''
        return redirect(url_for('index'))

    return render_template('index.html')

def update_image():
    global current_image_path, original_image_path

    mode = request.form.get('mode')
    sharpness = float(request.form.get('sharpness', 1))
    brightness = float(request.form.get('brightness', 100)) / 100
    saturation = float(request.form.get('saturation', 100)) / 100
    contrast = float(request.form.get('contrast', 100)) / 100
    red = float(request.form.get('red', 100)) / 100
    green = float(request.form.get('green', 100)) / 100
    blue = float(request.form.get('blue', 100)) / 100

    image = Image.open(original_image_path).convert('RGB')

    # Apply color channel adjustments
    r, g, b = image.split()
    r = r.point(lambda i: i * red)
    g = g.point(lambda i: i * green)
    b = b.point(lambda i: i * blue)
    image = Image.merge('RGB', (r, g, b))

    # Apply enhancements
    image = ImageEnhance.Sharpness(image).enhance(sharpness)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    image = ImageEnhance.Color(image).enhance(saturation)
    image = ImageEnhance.Contrast(image).enhance(contrast)

    # Apply display mode
    if mode == 'red':
        image = image.split()[0].convert('L')
    elif mode == 'green':
        image = image.split()[1].convert('L')
    elif mode == 'blue':
        image = image.split()[2].convert('L')
    elif mode == 'gray':
        image = image.convert('L')

    # Xoá ảnh đã xử lý trước đó (không xoá ảnh gốc)
    clear_upload_folder(exclude=original_image_path)

    # Lưu ảnh mới
    image = image.convert('RGB')
    new_filename = str(uuid.uuid4()) + '.png'
    new_filepath = os.path.join(UPLOAD_FOLDER, new_filename)
    image.save(new_filepath)
    current_image_path = new_filepath

    return jsonify({
        'processed': url_for('static', filename='uploads/' + new_filename)
    })

@app.route('/download')
def download():
    return send_file(current_image_path, as_attachment=True)

if __name__ == '__main__':
    clear_upload_folder()  # Xoá ảnh khi khởi động server
    app.run(debug=True)
