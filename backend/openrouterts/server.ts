import express, { Request, Response } from 'express';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(express.json()); 

const orToken = process.env.OPENROUTER;
if (!orToken) {
  console.error("CRITICAL: Missing OPENROUTER token in environment variables.");
  process.exit(1);
}

// POST endpoint that Python will hit
app.post('/api/completions', async (req: Request, res: Response) => {
  try {
    // API Call, currently in testing phase
    let response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${orToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        "model": "cohere/north-mini-code:free",
        "messages": [
          {
            "role": "user",
            "content": "How many r's are in the word 'strawberry'?"
          }
        ],
        "reasoning": {"enabled": true}
      })
    });

    const result = await response.json();
    
    // Return the response back to Python
    res.json(result);
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`TypeScript microservice running on http://localhost:${PORT}`);
});