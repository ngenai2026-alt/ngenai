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
            company_name = req_body.get('company_name', '').strip()
            domain = req_body.get('domain', '').strip()
            about = req_body.get('about', '').strip()
            
            if company_name or domain or about:
                system_prompt = f"""You are an expert AI business consultant representing NgenAI. 
Your goal is to demonstrate the power of AI to a potential client by answering their questions specifically tailored to their business.

BUSINESS CONTEXT:
Company Name: {company_name or 'Not provided'}
Industry/Domain: {domain or 'Not provided'}
About the Company: {about or 'Not provided'}

INSTRUCTIONS:
1. Provide highly customized, actionable advice and answers based ONLY on the provided business context.
2. DO NOT give generic ChatGPT-style answers. Relate everything back to their specific industry, company, and goals.
3. If they ask for ideas, provide creative and concrete examples relevant to their domain.
4. KEEP YOUR ANSWERS EXTREMELY SHORT AND CONCISE. Maximum 3-4 sentences or a few brief bullet points.
5. You represent NgenAI. Subtly highlight how custom AI solutions can implement your suggestions.
"""
            else:
                system_prompt = f"""You are an expert AI business consultant representing NgenAI.
The user skipped providing specific business information. 

INSTRUCTIONS:
1. You must restrict your answers to domain-related topics, AI automation, general business scaling, marketing, and sales.
2. If they ask for specific ideas, provide general but highly impactful AI use cases for businesses.
3. KEEP YOUR ANSWERS EXTREMELY SHORT AND CONCISE. Maximum 3-4 sentences or a few brief bullet points.
4. You represent NgenAI. Subtly highlight how custom AI solutions can implement your suggestions.
"""
            
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            payload = {
                "model": "openai/gpt-oss-20b",
                "messages": full_messages,
                "temperature": 0.7
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
