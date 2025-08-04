# Scout 👋

Scout AI is feature-rich, and user-friendly self-hosted WebUI designed to operate entirely offline. It supports various LLM runners, including Ollama and OpenAI-compatible APIs. 
This has been customized using Open WebUI Open source user interface.
For more information, be sure to check out OpenwebUI documentation [Open WebUI Documentation](https://docs.openwebui.com/).

![AmeritasAI Demo](./demo.gif)

## Key Features of Scout ⭐

- 🤝 **Ollama/OpenAI API Integration**: Effortlessly integrate OpenAI-compatible APIs for versatile conversations alongside Ollama models. Customize the OpenAI API URL to link with **LMStudio, GroqCloud, Mistral, OpenRouter, and more**.
- 🧩 **Pipelines, Plugin Support**: Seamlessly integrate custom logic and Python libraries using Pipeline Framework
- 📱 **Responsive Design**: Enjoy a seamless experience across Desktop PC, Laptop, and Mobile devices.
- 📱 **Progressive Web App (PWA) for Mobile**: Enjoy a native app-like experience on your mobile device with our PWA, providing offline access on localhost and a seamless user interface.
- ✒️🔢 **Full Markdown and LaTeX Support**: Elevate your LLM experience with comprehensive Markdown and LaTeX capabilities for enriched interaction.
- 🎤📹 **Hands-Free Voice/Video Call**: Experience seamless communication with integrated hands-free voice and video call features, allowing for a more dynamic and interactive chat environment.
- 🛠️ **Model Builder**: Easily create Ollama models via the Web UI. Create and add custom characters/agents, customize chat elements, and import models effortlessly through [Open WebUI Community](https://openwebui.com/) integration.
- 🐍 **Native Python Function Calling Tool**: Enhance your LLMs with built-in code editor support in the tools workspace. Bring Your Own Function (BYOF) by simply adding your pure Python functions, enabling seamless integration with LLMs.
- 📚 **Local RAG Integration**: Dive into the future of chat interactions with groundbreaking Retrieval Augmented Generation (RAG) support. This feature seamlessly integrates document interactions into your chat experience. You can load documents directly into the chat or add files to your document library, effortlessly accessing them using the `#` command before a query.
- 🔍 **Web Search for RAG**: Perform web searches using providers like `SearXNG`, `Google PSE`, `Brave Search`, `serpstack`, `serper`, `Serply`, `DuckDuckGo` and `TavilySearch` and inject the results directly into your chat experience.
- 🌐 **Web Browsing Capability**: Seamlessly integrate websites into your chat experience using the `#` command followed by a URL. This feature allows you to incorporate web content directly into your conversations, enhancing the richness and depth of your interactions.
- 🎨 **Image Generation Integration**: Seamlessly incorporate image generation capabilities using options such as AUTOMATIC1111 API or ComfyUI (local), and OpenAI's DALL-E (external), enriching your chat experience with dynamic visual content.
- ⚙️ **Many Models Conversations**: Effortlessly engage with various models simultaneously, harnessing their unique strengths for optimal responses. Enhance your experience by leveraging a diverse set of models in parallel.
- 🔐 **Role-Based Access Control (RBAC)**: Ensure secure access with restricted permissions; only authorized individuals can access your Ollama, and exclusive model creation/pulling rights are reserved for administrators.
- 🌐🌍 **Multilingual Support**: Experience Open WebUI in your preferred language with our internationalization (i18n) support. Join us in expanding our supported languages! We're actively seeking contributors!

  
  
## Deployment Configuration

- `GUNICORN_TIMEOUT` – Gunicorn worker timeout in seconds (default: `120`).
 
### Audio/TTS

- `AUDIO_TTS_MODEL` – Text-to-speech model (default: `tts-1`, or `collabora/whisperspeech:s2a-q4-base-en+pl.model` when `AUDIO_TTS_ENGINE` is `whisperspeech`). Set this environment variable to override the default.
- `TTS_ENGINE` – Text-to-speech engine. Set `TTS_ENGINE=whisperspeech` to enable the WhisperSpeech backend.
  - Requires extra packages: `webdataset`, `fastcore`, `fastprogress`, `torchaudio`, `speechbrain`, `vocos`, `huggingface-hub`.
  - Install them along with backend dependencies:

    ```bash
    pip install -r backend/requirements.txt webdataset fastcore fastprogress torchaudio speechbrain vocos huggingface-hub
    ```

- `AUDIO_TTS_OUTPUT_FORMAT` – Desired audio format for synthesized speech (`mp3`, `wav`, or `flac`). Scout checks if the selected engine supports the requested format and falls back to a supported option when necessary.
