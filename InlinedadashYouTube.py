import asyncio
import logging
import requests

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class Groq(loader.Module):
    """Interact with Groq AI"""

    strings = {
        "name": "Groq",
        "no_args": "<emoji document_id=5854929766146118183>❌</emoji> <b>Usage:</b> <code>{}{} {}</code>",
        "no_token": "<emoji document_id=5854929766146118183>❌</emoji> <b>API token missing! Set it in </b><code>{}cfg groq</code>",
        "asking_groq": "<emoji document_id=5332518162195816960>🔄</emoji> <b>Querying Groq...</b>",
    }

    def __init__(self):
        self.api_key = "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"  # Directly using your provided API key

    async def client_ready(self, client, db):
        self.db = db
        self._client = client

    @loader.command()
    async def groq(self, message):
        """Ask a question to Groq or reply to a message"""
        # Get the text from the current message or replied message
        q = utils.get_args_raw(message)
        if not q:
            if message.is_reply:
                q = (await message.get_reply_message()).text
            if not q:
                return await utils.answer(
                    message, self.strings["no_args"].format(self.get_prefix(), "groq", "[question]")
                )

        m = await utils.answer(message, self.strings["asking_groq"])

        # Groq API endpoint and headers
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3.3-70b-versatile",
            "messages": [{"role": "user", "content": q}],
            "temperature": 0.7,
            "max_tokens": 32000
        }

        # Make the API request
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                answer = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No answer found.")
            elif response.status_code == 404:
                answer = "Error: Endpoint not found. Please check the API URL."
            else:
                answer = f"Error: Unable to get a response from Groq. Status code: {response.status_code}."
        except requests.exceptions.RequestException as e:
            answer = f"Error: {e}"

        # Edit the response in the chat
        return await m.edit(f"[👤](tg://emoji?id=5879770735999717115) **Question:** {q}\n\n"
                            f"[🤖](tg://emoji?id=5372981976804366741) **Answer:** {answer}", parse_mode="markdown")