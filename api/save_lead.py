from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            req_body = json.loads(post_data)
            
            user_name = req_body.get('user_name', 'Unknown User')
            contact = req_body.get('contact', 'Unknown Contact')
            
            is_email = "@" in contact
            email_field = contact if is_email else "N/A"
            phone_field = contact if not is_email else "N/A"
            
            sheet_data = {
                "name": user_name,
                "enquiry_type": "AI Demo Lead",
                "company": "N/A",
                "email": email_field,
                "phone": phone_field,
                "service": "N/A",
                "message": "[Demo Session Started] No business info collected."
            }
            
            # The same google script URL used in chat.py
            sheet_req = urllib.request.Request(
                "https://script.google.com/macros/s/AKfycbzvc_1YXuMxoTo-u93aZJuZYdbR1V2EdAlG5wGi5aOKQouSkqevGpXTBd1lkqNtCoopGA/exec",
                data=json.dumps(sheet_data).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(sheet_req)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            
        except Exception as e:
            print("General Error saving lead:", str(e))
            # Even if it fails, we shouldn't block the demo from running
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
