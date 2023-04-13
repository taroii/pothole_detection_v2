from flask import send_from_directory
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask import render_template
from url_utils import get_base_url
from io import BytesIO
from PIL import Image
import os, requests, base64

# setup the webserver
# port may need to be changed if there are multiple flask servers running on same server
port = 12345
base_url = get_base_url(port)

# if the base url is not empty, then the server is running in development, and we need to specify the static folder so that the static files are served
if base_url == '/':
    app = Flask(__name__)
else:
    app = Flask(__name__, static_url_path=base_url+'static')

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

API_URL = "https://api-inference.huggingface.co/models/taroii/pothole-detection-model"
headers = {"Authorization": "Bearer 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"}

def query(img):
  response = requests.post(API_URL, headers=headers, data=img)
  return response.json()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route(f'{base_url}', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))

    return render_template('home.html')


@app.route(f'{base_url}/uploads/<filename>', methods=['GET'])
def uploaded_file(filename):
    file = request.files['file']
    img_bytes = file.read()
    img_bytes = BytesIO(img_bytes)
    result = query(img_bytes)
    print('--- check here ---')
    print(result)
    print('-----')
    img_base64 = base64.b64encode(img_bytes.getvalue()).decode()

    try: 
      if result[0]['label'] == 'pothole':
        label = 'We found a pothole!'
        confidence = 'With confidence ' + str(round(result[0]['score'], 2) * 100) + '%'
      else:
        label = "We didn't find a pothole :("
        confidence = 'With confidence ' + str(round(result[1]['score'], 2) * 100) + '%'
    except:
      print('--- check here ---')
      print(result['error'][0])
      print('-----')
      if result['error'][0].find('Invalid') != -1:
        label = 'An error occured with the image, please try another image.'
        confidence = ''
      else:
        label = 'Sorry! The model is still loading...'
        confidence = 'Please try again in ' + str(result['estimated_time']) + ' seconds :)'
    return render_template('results.html', confidences=confidence, labels=label, image=img_base64)


@app.route(f'{base_url}/uploads/<path:filename>')
def files(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# define additional routes here
# for example:
# @app.route(f'{base_url}/team_members')
# def team_members():
#     return render_template('team_members.html') # would need to actually make this page

if __name__ == '__main__':
    # IMPORTANT: change url to the site where you are editing this file.
    website_url = 'url'
    
    print(f'Try to open\n\n    https://{website_url}' + base_url + '\n\n')
    app.run(host = '0.0.0.0', port=port, debug=True)
