import json
import logging
import multiprocessing
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# MongoDB connection
def get_db():
    client = MongoClient("mongodb://mongo_db:27017/")  # Назва контейнера з Mongo
    return client["chat_db"]

def save_to_db(message):
    try:
        db = get_db()
        db.messages.insert_one(message)
    except Exception as e:
        logging.error(f"Failed to save message to MongoDB: {e}")

# HTTP Server
class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/":
            self.send_html_file("index.html")
        elif parsed_url.path == "/message.html":
            self.send_html_file("message.html")
        elif parsed_url.path == "/error.html":
            self.send_html_file("error.html")
        elif parsed_url.path == "/style.css":
            self.send_static_file("style.css")
        elif parsed_url.path == "/logo.png":
            self.send_static_file("logo.png")
        else:
            self.send_html_file("error.html", 404)

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            parsed_data = parse_qs(post_data)
            username = parsed_data.get("username", [""])[0]
            message = parsed_data.get("message", [""])[0]
            
            message_data = json.dumps({"username": username, "message": message})
            
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(message_data.encode('utf-8'), ("localhost", 5000))
            
            # self.send_response(200)
            # self.send_header("Content-type", "text/html")
            # self.end_headers()
            # self.wfile.write(b"Message received")
            
            self.send_response(303)  # HTTP 303 See Other
            self.send_header("Location", "/message.html")
            self.end_headers()

    def send_html_file(self, filename, status=200):
        try:
            with open(filename, "rb") as file:
                self.send_response(status)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Error: File not found")
    
    def send_static_file(self, filename, status=200):
        try:
            with open(filename, "rb") as file:
                self.send_response(status)
                if filename.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                elif filename.endswith(".png"):
                    self.send_header("Content-type", "image/png")
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Error: File not found")

# Socket Server
def socket_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 5000))
    logging.info("Socket server running on port 5000")
    
    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode('utf-8'))
        message["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        save_to_db(message)
        logging.info(f"Received and saved message: {message}")

# Run HTTP Server
def http_server():
    server_address = ("", 3000)
    httpd = HTTPServer(server_address, HttpHandler)
    logging.info("HTTP server running on port 3000")
    httpd.serve_forever()

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=http_server)
    p2 = multiprocessing.Process(target=socket_server)
    
    p1.start()
    p2.start()
    
    p1.join()
    p2.join()