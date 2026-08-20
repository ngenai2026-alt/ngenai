export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const GROQ_API_KEY = process.env.GROQ_API_KEY;
  if (!GROQ_API_KEY) {
    return res.status(500).json({ error: 'Missing GROQ_API_KEY environment variable' });
  }

  const { messages } = req.body;
  if (!messages || !Array.isArray(messages)) {
    return res.status(400).json({ error: 'Messages array is required' });
  }

  const systemPrompt = `You are Kani, the intelligent AI assistant for NgenAI (Next GenerationAI), based in Pune, India. 
NgenAI specializes in custom Generative AI solutions, Agentic AI Automation, Multi-Agent Workflows, RAG Pipelines, and Enterprise API integrations. 
We also provide hands-on workshops, corporate training, and help with PhD/M.Tech research implementations.
Your goal is to answer user questions politely and concisely. 
If the user shows interest in hiring us, starting a project, or getting more details, you should ask if they would like to book a free AI consultation.
If they agree, ask for their name, email, phone number, and a brief description of what they need.
Once you have all the required information (name, email, phone, and project description), you MUST call the 'book_appointment' tool to save their details.
Do NOT call the tool if you are missing their name, email, or phone. Ask them for the missing details first.`;

  // Prepend system prompt
  const fullMessages = [
    { role: 'system', content: systemPrompt },
    ...messages
  ];

  const tools = [
    {
      type: 'function',
      function: {
        name: 'book_appointment',
        description: 'Book a consultation appointment by submitting the user contact details.',
        parameters: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'The user full name' },
            email: { type: 'string', description: 'The user email address' },
            phone: { type: 'string', description: 'The user phone number' },
            message: { type: 'string', description: 'A brief description of their project or requirement' }
          },
          required: ['name', 'email', 'phone', 'message']
        }
      }
    }
  ];

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-oss-120b',
        messages: fullMessages,
        tools: tools,
        tool_choice: 'auto'
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error('Groq API Error:', errText);
      return res.status(500).json({ error: 'Failed to fetch from Groq API' });
    }

    const data = await response.json();
    const responseMessage = data.choices[0].message;
    const toolCalls = responseMessage.tool_calls;

    // Check if the LLM decided to call our tool
    if (toolCalls && toolCalls.length > 0) {
      const toolCall = toolCalls[0];
      if (toolCall.function.name === 'book_appointment') {
        const args = JSON.parse(toolCall.function.arguments);
        
        // Push data to Google Sheets Webhook
        const SHEET_URL = 'https://script.google.com/macros/s/AKfycbzvc_1YXuMxoTo-u93aZJuZYdbR1V2EdAlG5wGi5aOKQouSkqevGpXTBd1lkqNtCoopGA/exec';
        
        const sheetData = {
          name: args.name,
          enquiry_type: 'Company',
          company: 'N/A', // Using N/A as it's from chat
          email: args.email,
          phone: args.phone,
          service: 'AI Chatbot Booking',
          message: args.message
        };

        // We use fetch in no-cors mode in frontend, but backend can just do standard POST.
        // Google Apps Script usually expects form-encoded or JSON with following redirects, but let's try direct JSON.
        // Wait, the Google Apps Script in contact.html works with direct POSTing JSON, but we have to handle CORS/Redirects. 
        // In Node fetch, it handles redirects automatically.
        try {
          await fetch(SHEET_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(sheetData)
          });
        } catch (e) {
          console.error("Failed to push to Google Sheet:", e);
        }

        // Return a response to the frontend saying it was booked successfully, 
        // without making a second trip to the LLM (for speed and simplicity).
        return res.status(200).json({ 
          message: {
            role: 'assistant', 
            content: `Thank you, ${args.name}! I have successfully booked your appointment and our team will contact you shortly at ${args.email} or ${args.phone}.`
          } 
        });
      }
    }

    // Normal response
    return res.status(200).json({ message: responseMessage });

  } catch (error) {
    console.error('API Route Error:', error);
    return res.status(500).json({ error: 'Internal Server Error' });
  }
}
