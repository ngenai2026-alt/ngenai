import http.server
import socketserver
import json
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse

PORT = 8000

# Load .env file manually so we don't need third-party libraries
try:
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                value = value.strip('"\'')
                os.environ[key] = value
except FileNotFoundError:
    print("Warning: No .env file found. Please create one with GROQ_API_KEY=your_key")

class LocalHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                req_body = json.loads(post_data)
                
                groq_key = os.environ.get("GROQ_API_KEY")
                if not groq_key:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Missing GROQ_API_KEY in .env file"}).encode('utf-8'))
                    return

                messages = req_body.get('messages', [])
                context = req_body.get('context', '')
                
                prompt_path = os.path.join(os.path.dirname(__file__), "api", "prompt.txt")
                with open(prompt_path, "r", encoding="utf-8") as f:
                    system_prompt = f.read()
                    
                if context:
                    system_prompt += f"\n\nCURRENT CONTEXT: The user is currently viewing the page: '{context}'. If appropriate, tailor your greeting or pitch to this context."
                
                full_messages = [{"role": "system", "content": system_prompt}] + messages
                
                tools = [{
                    "type": "function",
                    "function": {
                        "name": "book_appointment",
                        "description": "DO NOT call this tool until the user has explicitly provided their name, email, phone number, and project description, and agreed to book.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "phone": {"type": "string"},
                                "preferred_time": {"type": "string"},
                                "message": {"type": "string"}
                            },
                            "required": ["name", "email", "phone", "preferred_time", "message"]
                        }
                    }
                }]
                
                payload = {
                    "model": "openai/gpt-oss-20b",
                    "messages": full_messages,
                    "tools": tools,
                    "tool_choice": "auto"
                }
                
                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    },
                    method="POST"
                )
                
                response = urllib.request.urlopen(req)
                data = json.loads(response.read().decode('utf-8'))
                
                message = data['choices'][0]['message']
                tool_calls = message.get('tool_calls', [])
                
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    if tool_call['function']['name'] == 'book_appointment':
                        args = json.loads(tool_call['function']['arguments'])
                        
                        email_address = args.get("email", "")
                        import re
                        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
                        if not re.match(email_pattern, email_address):
                            res_message = {
                                "role": "assistant",
                                "content": f"The email address '{email_address}' looks invalid. Could you please double-check and provide a valid email?"
                            }
                            self.send_response(200)
                            self.send_header('Content-Type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({"message": res_message}).encode('utf-8'))
                            return
                            
                        sheet_data = {
                            "name": args.get("name", ""),
                            "enquiry_type": "Company",
                            "company": "N/A",
                            "email": email_address,
                            "phone": args.get("phone", ""),
                            "service": "AI Chatbot Booking",
                            "message": f"[{args.get('preferred_time', 'Anytime')}] " + args.get("message", "")
                        }
                        
                        try:
                            sheet_req = urllib.request.Request(
                                "https://script.google.com/macros/s/AKfycbzvc_1YXuMxoTo-u93aZJuZYdbR1V2EdAlG5wGi5aOKQouSkqevGpXTBd1lkqNtCoopGA/exec",
                                data=json.dumps(sheet_data).encode('utf-8'),
                                headers={"Content-Type": "application/json"},
                                method="POST"
                            )
                            urllib.request.urlopen(sheet_req)
                        except Exception as e:
                            print("Error calling sheet:", str(e))
                            
                        res_message = {
                            "role": "assistant",
                            "content": f"Thank you, {args.get('name', 'there')}! I have successfully booked your appointment and our team will contact you shortly."
                        }
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"message": res_message}).encode('utf-8'))
                        return
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"message": message}).encode('utf-8'))
                
            except urllib.error.HTTPError as e:
                err_msg = e.read().decode('utf-8')
                print("Groq API Error:", err_msg)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Groq Error: {err_msg}"}).encode('utf-8'))
            except Exception as e:
                print("General Error:", str(e))
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Internal Server Error: {str(e)}"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(("", PORT), LocalHandler) as httpd:
    print(f"Serving locally at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    httpd.serve_forever()
