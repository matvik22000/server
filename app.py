from flask import Flask, render_template, request, send_from_directory
from flask_sockets import Sockets
import gevent
import psycopg2
import json
from gpiozero import CPUTemperature
import datetime
import glob
import os

app = Flask(__name__)
sockets = Sockets(app)
cpu = CPUTemperature()

def get_time():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
def parse_msg(msg):
    m = json.loads(msg)
    name = m["name"]
    text = m["text"]
    return name, text

def parse_system(msg, ws):
    msg = json.loads(msg)
    try:
        system = msg["system"]
    except Exception as e:
        return False
    try:
        limit = msg["limit"]
        chat.send_old_msgs(ws, limit)
    except Exception as e:
        pass
    return True


class DatabaseWork:
    def __init__(self, database, user, password, host, port="5432"):
        self.port = port
        self.host = host
        self.password = password
        self.user = user
        self.database = database
        self.cur = None
        self.conn = None

    def connect(self):
        conn = psycopg2.connect(
            database=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
        self.conn = conn
        self.cur = conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_msgs(self, lim):
        # get all msgs from table
        self.cur.execute("select count(*) from msgs")
        l = self.cur.fetchall()[0][0]
        start = l - lim
        self.cur.execute("""SELECT * FROM msgs offset %s limit %s""", (
            start, lim
            ))
        msgs = self.cur.fetchall()
        res = []
        for msg in msgs:
            res.append({"name": msg[0], "text": msg[1], "time": str(msg[2])})
        return res

    def put_msg(self, usr, msg, time):
        # inserts msg into table
        self.cur.execute("""INSERT INTO msgs (usr, msg, time) VALUES(%s, %s, %s)""", (
            usr, msg, time
        ))
        # don't forget about commit


class Chat:
    def __init__(self):
        self.clients = []

    def register(self, user):
        self.clients.append(user)

    def broadcast(self, data):
        name, text = parse_msg(data)#
        # timedelta = datetime.timedelta()
        time = get_time()
        data = json.dumps({"name": name, "text": text, "time": time})
        db.connect()
        db.put_msg(name, text, time)
        db.commit()
        db.close()
        users_for_remove = []
        for client in self.clients:
            if not self.send(client, data):
                users_for_remove.append(client)
        for user in users_for_remove:
            self.clients.remove(user)
            print("disconnect")

    def send(self, client, data):
        try:
            client.send(data)
            return True
        except Exception:
            return False

    def send_old_msgs(self, ws, limit=100):
        db.connect()
        msgs = db.get_msgs(limit)
        db.close()
        for msg in msgs:
            m = json.dumps(msg)
            if not self.send(ws, m):
                self.clients.remove(ws)
                print("disconnect")
                


chat = Chat()
db = DatabaseWork("chat", "postgres", "test", "127.0.0.1")


@sockets.route('/test')
def echo_socket(ws):
    print("connect")
    chat.register(ws)
    chat.send_old_msgs(ws)
    while not ws.closed:
        msg = ws.receive()
        if msg:
            if parse_system(msg, ws):
                print("new system msg:%s" % msg)
                continue
            print("new msg:%s" % msg)
            print(chat.clients)
            chat.broadcast(msg)

        gevent.sleep(0.1)
        
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
    print("success")
    return "success"
        
        
@app.route('/up')
def up():
    return render_template('upload.html')
        
@app.route('/get/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/files')
def root():
    path= 'files'
    files = [f for f in glob.glob(path + "**/*", recursive=True)]
    for i in range(len(files)):
        files[i] = 'get/' + files[i][files[i].find('/') + 1:]
        
    return render_template('files.html', files=files)


@app.route('/')
def hello():
    return render_template('nav.html')

@app.route('/chat_render')
def chat_render():
    return render_template('index.html')



@app.route('/clients')
def clients():
    return str(len(chat.clients))



@app.route('/temp')
def temp():
    return str(cpu.temperature) + "/" + str(get_time())


if __name__ == "__main__":
    app.run(host='0.0.0.0')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('0.0.0.0', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()

# gunicorn -k flask_sockets.worker --bind 0.0.0.0 app:app
