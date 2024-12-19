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
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "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",
                lambda: "Groq AI API token. Obtain it from: https://console.groq.com/keys",
                validator=loader.validators.Hidden(loader.validators.String())
            ),
            loader.ConfigValue(
                "answer_text",
                """[👤](tg://emoji?id=5879770735999717115) **Question:** {question}

[🤖](tg://emoji?id=5372981976804366741) **Answer:** {answer}""",
                lambda: "Output text format",
            ),
        )

    async def client_ready(self, client, db):
        self.db = db
        self._client = client

    @loader.command()
    async def groq(self, message):
        """Ask a question to Groq"""
        q = utils.get_args_raw(message)
        if not q:
            return await utils.answer(message, self.strings["no_args"].format(self.get_prefix(), "groq", "[question]"))

        if not self.config['api_key']:
            return await utils.answer(message, self.strings["no_token"].format(self.get_prefix()))

        m = await utils.answer(message, self.strings['asking_groq'])

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3.3-70b-versatile",
            "messages": [
                {
                    "role": "user",
                    "content": q,
                }
            ],
            "temperature": 0.7,
            "max_tokens": 32000
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            answer = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No answer found.")
        else:
            answer = f"Error: Unable to get a response from Groq. Status code: {response.status_code}."

        return await m.edit(self.config['answer_text'].format(question=q, answer=answer), parse_mode="markdown")