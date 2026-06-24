import * as dotenv from 'dotenv';
dotenv.config();

const orToken = process.env.OPENROUTER;
if (!orToken) {
  throw new Error("Missing OPENROUTER in environment variables");
}

// First API call with reasoning
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
