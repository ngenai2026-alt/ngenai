from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            req_body = json.loads(post_data)
            
            groq_key = os.environ.get("GROQ_API_KEY")
            if not groq_key:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing GROQ_API_KEY"}).encode('utf-8'))
                return

            messages = req_body.get('messages', [])
            
            system_prompt = """You are Kani, the intelligent AI assistant for NgenAI (Next GenerationAI), based in Pune, India. 
NgenAI specializes in custom Generative AI solutions, Agentic AI Automation, Multi-Agent Workflows, RAG Pipelines, and Enterprise API integrations. 
We also provide hands-on workshops, corporate training, and help with PhD/M.Tech research implementations.
Your goal is to answer user questions politely and concisely. 
If the user shows interest in hiring us, starting a project, or getting more details, you should ask if they would like to book a free AI consultation.
If they agree, ask for their name, email, phone number, and a brief description of what they need.
Once you have all the required information (name, email, phone, and project description), you MUST call the 'book_appointment' tool to save their details.
Do NOT call the tool if you are missing their name, email, or phone. Ask them for the missing details first."""
            
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            tools = [{
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book a consultation appointment by submitting the user contact details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "The user full name"},
                            "email": {"type": "string", "description": "The user email address"},
                            "phone": {"type": "string", "description": "The user phone number"},
                            "message": {"type": "string", "description": "A brief description of their project or requirement"}
                        },
                        "required": ["name", "email", "phone", "message"]
                    }
                }
            }]
            
            # Using mixtral-8x7b-32768 to ensure absolute stability and speed on Groq
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": full_messages,
                "tools": tools,
                "tool_choice": "auto"
            }
            
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
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

