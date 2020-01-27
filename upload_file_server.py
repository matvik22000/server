import os
from flask import Flask, render_template, request, send_from_directory
import glob

app = Flask(__name__)
UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/upload', methods = ['POST'])
def upload():
    print('uploading')
    file = request.files['file']
    print('2')
    if file:
        print('3')
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        
    return "success"
        
        
@app.route('/up')
def up():
    return render_template('upload.html')
        
@app.route('/get/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def root():
    path= 'files'
    files = [f for f in glob.glob(path + "**/*", recursive=True)]
    for i in range(len(files)):
        files[i] = 'get/' + files[i][files[i].find('/') + 1:]
        
    return render_template('files.html', files=files)
        


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
        
