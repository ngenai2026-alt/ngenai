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
                
                system_prompt = """You are Kani, the intelligent AI assistant for NgenAI (Next GenerationAI), based in Pune, India. 
NgenAI specializes in custom Generative AI solutions, Agentic AI Automation, Multi-Agent Workflows, RAG Pipelines, and Enterprise API integrations. 
We also provide hands-on workshops, corporate training, and help with PhD/M.Tech research implementations.
Your goal is to answer user questions politely and concisely. 
If the user shows interest in hiring us, starting a project, or getting more details, you should guide them towards booking a free AI consultation.
CRITICAL RULES FOR BOOKING:
1. NEVER hallucinate or guess the user's name, email, or phone number. If they don't provide it, you must ask for it.
2. If the user is missing ANY of the required details (name, email, phone, or project description), you MUST ask them follow-up questions to gather the missing information.
3. Once you have collected ALL the information, you MUST explicitly ask the user: "Should I go ahead and book an appointment/inquiry for you?"
4. ONLY call the 'book_appointment' tool AFTER the user explicitly agrees to book AND you have all their details."""
                
                full_messages = [{"role": "system", "content": system_prompt}] + messages
                
                tools = [{
                    "type": "function",
                    "function": {
                        "name": "book_appointment",
                        "description": "Book a consultation appointment by submitting the user contact details.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "phone": {"type": "string"},
                                "message": {"type": "string"}
                            },
                            "required": ["name", "email", "phone", "message"]
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
                        
                        sheet_data = {
                            "name": args.get("name", ""),
                            "enquiry_type": "Company",
                            "company": "N/A",
                            "email": args.get("email", ""),
                            "phone": args.get("phone", ""),
                            "service": "AI Chatbot Booking",
                            "message": args.get("message", "")
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
