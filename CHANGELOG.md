# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [1.2.0] - 2025-04-06

### Fixed Ameritas Custom Changes - 2025-04-06
- 📝**Chunk base Page Number**: Chunk Based Page Number allocation to all documents.
- 🧾**OCR RAG Markdown**: Allocated clearer RAG data retrieval for PDF OCR.

### Added OpenWebUI [0.6.0] - 2025-03-31

- 🧩 **External Tool Server Support via OpenAPI**: Connect Open WebUI to any OpenAPI-compatible REST server instantly—offering immediate integration with thousands of developer tools, SDKs, and SaaS systems for powerful extensibility. Learn more: https://github.com/open-webui/openapi-servers
- 🛠️ **MCP Server Support via MCPO**: You can now convert and expose your internal MCP tools as interoperable OpenAPI HTTP servers within Open WebUI for seamless, plug-n-play AI toolchain creation. Learn more: https://github.com/open-webui/mcpo
- 📨 **/messages Chat API Endpoint Support**: For power users building external AI systems, new endpoints allow precise control of messages asynchronously—feed long-running external responses into Open WebUI chats without coupling with the frontend.
- 📝 **Client-Side PDF Generation**: PDF exports are now generated fully client-side for drastically improved output quality—perfect for saving conversations or documents.
- 💼 **Enforced Temporary Chats Mode**: Admins can now enforce temporary chat sessions by default to align with stringent data retention and compliance requirements.
- 🌍 **Public Resource Sharing Permission Controls**: Fine-grained user group permissions now allow enabling/disabling public sharing for models, knowledge, prompts, and tools—ideal for privacy, team control, and internal deployments.
- 📦 **Custom pip Options for Tools/Functions**: You can now specify custom pip installation options with "PIP_OPTIONS", "PIP_PACKAGE_INDEX_OPTIONS" environment variables—improving compatibility, support for private indexes, and better control over Python environments.
- 🔢 **Editable Message Counter**: You can now double-click the message count number and jump straight to editing the index—quickly navigate complex chats or regenerate specific messages precisely.
- 🧠 **Embedding Prefix Support Added**: Add custom prefixes to your embeddings for instruct-style tokens, enabling stronger model alignment and more consistent RAG performance.
- 🙈 **Ability to Hide Base Models**: Optionally hide base models from the UI, helping users streamline model visibility and limit access to only usable endpoints..
- 📚 **Docling Content Extraction Support**: Open WebUI now supports Docling as a content extraction engine, enabling smarter and more accurate parsing of complex file formats—ideal for advanced document understanding and Retrieval-Augmented Generation (RAG) workflows.
- 🗃️ **Redis Sentinel Support Added**: Enhance deployment redundancy with support for Redis Sentinel for highly available, failover-safe Redis-based caching or pub/sub.
- 📚 **JSON Schema Format for Ollama**: Added support for defining the format using JSON schema in Ollama-compatible models, improving flexibility and validation of model outputs.
- 🔍 **Chat Sidebar Search "Clear” Button**: Quickly clear search filters in chat sidebar using the new ✖️ button—streamline your chat navigation with one click.
- 🗂️ **Auto-Focus + Enter Submit for Folder Name**: When creating a new folder, the system automatically enters rename mode with name preselected—simplifying your org workflow.
- 🧱 **Markdown Alerts Rendering**: Blockquotes with syntax hinting (e.g. ⚠️, ℹ️, ✅) now render styled Markdown alert banners, making messages and documentation more visually structured.
- 🔁 **Hybrid Search Runs in Parallel Now**: Hybrid (BM25 + embedding) search components now run in parallel—dramatically reducing response times and speeding up document retrieval.
- 📋 **Cleaner UI for Tool Call Display**: Optimized the visual layout of called tools inside chat messages for better clarity and reduced visual clutter.
- 🧪 **Playwright Timeout Now Configurable**: Default timeout for Playwright processes is now shorter and adjustable via environment variables—making web scraping more robust and tunable to environments.
- 📈 **OpenTelemetry Support for Observability**: Open WebUI now integrates with OpenTelemetry, allowing you to connect with tools like Grafana, Jaeger, or Prometheus for detailed performance insights and real-time visibility—entirely opt-in and fully self-hosted. Even if enabled, no data is ever sent to us, ensuring your privacy and ownership over all telemetry data.
- 🛠 **General UI Enhancements & UX Polish**: Numerous refinements across sidebar, code blocks, modal interactions, button alignment, scrollbar visibility, and folder behavior improve overall fluidity and usability of the interface.
- 🧱 **General Backend Refactoring**: Numerous backend components have been refactored to improve stability, maintainability, and performance—ensuring a more consistent and reliable system across all features.
- 🌍 **Internationalization Language Support Updates**: Added Estonian and Galician languages, improved Spanish (fully revised), Traditional Chinese, Simplified Chinese, Turkish, Catalan, Ukrainian, and German for a more localized and inclusive interface.

### Fixed OpenWebUI [0.6.0] - 2025-03-31

- 🧑‍💻 **Firefox Input Height Bug**: Text input in Firefox now maintains proper height, ensuring message boxes look consistent and behave predictably.
- 🧾 **Tika Blank Line Bug**: PDFs processed with Apache Tika 3.1.0.0 no longer introduce excessive blank lines—improving RAG output quality and visual cleanliness.
- 🧪 **CSV Loader Encoding Issues**: CSV files with unknown encodings now automatically detect character sets, resolving import errors in non-UTF-8 datasets.
- ✅ **LDAP Auth Config Fix**: Path to certificate file is now optional for LDAP setups, fixing authentication trouble for users without preconfigured cert paths.
- 📥 **File Deletion in Bypass Mode**: Resolved issue where files couldn’t be deleted from knowledge when “bypass embedding” mode was enabled.
- 🧩 **Hybrid Search Result Sorting & Deduplication Fixed**: Fixed citation and sorting issues in RAG hybrid and reranker modes, ensuring retrieved documents are shown in correct order per score.
- 🧷 **Model Export/Import Broken for a Single Model**: Fixed bug where individual models couldn’t be exported or re-imported, restoring full portability.
- 📫 **Auth Redirect Fix**: Logged-in users are now routed properly without unnecessary login prompts when already authenticated.

### Changed OpenWebUI [0.6.0] - 2025-03-31

- 🧠 **Prompt Autocompletion Disabled By Default**: Autocomplete suggestions while typing are now disabled unless explicitly re-enabled in user preferences—reduces distractions while composing prompts for advanced users.
- 🧾 **Normalize Citation Numbering**: Source citations now properly begin from "1" instead of "0"—improving consistency and professional presentation in AI outputs.
- 📚 **Improved Error Handling from Pipelines**: Pipelines now show the actual returned error message from failed tasks rather than generic "Connection closed"—making debugging far more user-friendly.

### Removed OpenWebUI [0.6.0] - 2025-03-31

- 🧾 **ENABLE_AUDIT_LOGS Setting Removed**: Deprecated setting “ENABLE_AUDIT_LOGS” has been fully removed—now controlled via “AUDIT_LOG_LEVEL” instead.

### Added OpenWebUI [0.5.20] - 2025-03-05

- **⚡ Toggle Code Execution On/Off**: You can now enable or disable code execution, providing more control over security, ensuring a safer and more customizable experience.

### Fixed OpenWebUI [0.5.20] - 2025-03-05

- **📜 Pinyin Keyboard Enter Key Now Works Properly**: Resolved an issue where the Enter key for Pinyin keyboards was not functioning as expected, ensuring seamless input for Chinese users.
- **🖼️ Web Manifest Loading Issue Fixed**: Addressed inconsistencies with 'site.webmanifest', guaranteeing proper loading and representation of the app across different browsers and devices.
- **📦 Non-Root Container Issue Resolved**: Fixed a critical issue where the UI failed to load correctly in non-root containers, ensuring reliable deployment in various environments.

### Added OpenWebUI [0.5.19] - 2025-03-04

- **📊 Logit Bias Parameter Support**: Fine-tune conversation dynamics by adjusting the Logit Bias parameter directly in chat settings, giving you more control over model responses.
- **⌨️ Customizable Enter Behavior**: You can now configure Enter to send messages only when combined with Ctrl (Ctrl+Enter) via Settings > Interface, preventing accidental message sends.
- **📝 Collapsible Code Blocks**: Easily collapse long code blocks to declutter your chat, making it easier to focus on important details.
- **🏷️ Tag Selector in Model Selector**: Quickly find and categorize models with the new tag filtering system in the Model Selector, streamlining model discovery.
- **📈 Experimental Elasticsearch Vector DB Support**: Now supports Elasticsearch as a vector database, offering more flexibility for data retrieval in Retrieval-Augmented Generation (RAG) workflows.
- **⚙️ General Reliability Enhancements**: Various stability improvements across the WebUI, ensuring a smoother, more consistent experience.
- **🌍 Updated Translations**: Refined multilingual support for better localization and accuracy across various languages.

### Fixed OpenWebUI [0.5.19] - 2025-03-04

- **🔄 "Stream" Hook Activation**: Fixed an issue where the "Stream" hook only worked when globally enabled, ensuring reliable real-time filtering.
- **📧 LDAP Email Case Sensitivity**: Resolved an issue where LDAP login failed due to email case sensitivity mismatches, improving authentication reliability.
- **💬 WebSocket Chat Event Registration**: Fixed a bug preventing chat event listeners from being registered upon sign-in, ensuring real-time updates work properly.


### Fixed OpenWebUI [0.5.18] - 2025-02-27

- **🌐 Open WebUI Now Works Over LAN in Insecure Context**: Resolved an issue preventing Open WebUI from functioning when accessed over a local network in an insecure context, ensuring seamless connectivity.
- **🔄 UI Now Reflects Deleted Connections Instantly**: Fixed an issue where deleting a connection did not update the UI in real time, ensuring accurate system state visibility.
- **🛠️ Models Now Display Correctly with ENABLE_FORWARD_USER_INFO_HEADERS**: Addressed a bug where models were not visible when ENABLE_FORWARD_USER_INFO_HEADERS was set, restoring proper model listing.

### Added OpenWebUI [0.5.17] - 2025-02-27

- **🚀 Instant Document Upload with Bypass Embedding & Retrieval**: Admins can now enable "Bypass Embedding & Retrieval" in Admin Settings > Documents, significantly speeding up document uploads and ensuring full document context is retained without chunking.
- **🔎 "Stream" Hook for Real-Time Filtering**: The new "stream" hook allows dynamic real-time message filtering. Learn more in our documentation (https://docs.openwebui.com/features/plugin/functions/filter).
- **☁️ OneDrive Integration**: Early support for OneDrive storage integration has been introduced, expanding file import options.
- **📈 Enhanced Logging with Loguru**: Backend logging has been improved with Loguru, making debugging and issue tracking far more efficient.
- **⚙️ General Stability Enhancements**: Backend and frontend refactoring improves performance, ensuring a smoother and more reliable user experience.
- **🌍 Updated Translations**: Refined multilingual support for better localization and accuracy across various languages.

### Fixed OpenWebUI  [0.5.17] - 2025-02-27

- **🔄 Reliable Model Imports from the Community Platform**: Resolved import failures, allowing seamless integration of community-shared models without errors.
- **📊 OpenAI Usage Statistics Restored**: Fixed an issue where OpenAI usage metrics were not displaying correctly, ensuring accurate tracking of usage data.
- **🗂️ Deduplication for Retrieved Documents**: Documents retrieved during searches are now intelligently deduplicated, meaning no more redundant results—helping to keep information concise and relevant.

### Changed OpenWebUI  [0.5.17] - 2025-02-27

- **📝 "Full Context Mode" Renamed for Clarity**: The "Full Context Mode" toggle in Web Search settings is now labeled "Bypass Embedding & Retrieval" for consistency across the UI.

### Fixed OpenWebUI [0.5.16] - 2025-02-20

- **🔍 Web Search Retrieval Restored**: Resolved a critical issue that broke web search retrieval by reverting deduplication changes, ensuring complete and accurate search results once again.

### Added OpenWebUI [0.5.15] - 2025-02-20

- **📄 Full Context Mode for Local Document Search (RAG)**: Toggle full context mode from Admin Settings > Documents to inject entire document content into context, improving accuracy for models with large context windows—ideal for deep context understanding.
- **🌍 Smarter Web Search with Agentic Workflows**: Web searches now intelligently gather and refine multiple relevant terms, similar to RAG handling, delivering significantly better search results for more accurate information retrieval.
- **🔎 Experimental Playwright Support for Web Loader**: Web content retrieval is taken to the next level with Playwright-powered scraping for enhanced accuracy in extracted web data.
- **☁️ Experimental Azure Storage Provider**: Early-stage support for Azure Storage allows more cloud storage flexibility directly within Open WebUI.
- **📊 Improved Jupyter Code Execution with Plots**: Interactive coding now properly displays inline plots, making data visualization more seamless inside chat interactions.
- **⏳ Adjustable Execution Timeout for Jupyter Interpreter**: Customize execution timeout (default: 60s) for Jupyter-based code execution, allowing longer or more constrained execution based on your needs.
- **▶️ "Running..." Indicator for Jupyter Code Execution**: A visual indicator now appears while code execution is in progress, providing real-time status updates on ongoing computations.
- **⚙️ General Backend & Frontend Stability Enhancements**: Extensive refactoring improves reliability, performance, and overall user experience for a more seamless Open WebUI.
- **🌍 Translation Updates**: Various international translation refinements ensure better localization and a more natural user interface experience.

### Fixed OpenWebUI [0.5.15] - 2025-02-20

- **📱 Mobile Hover Issue Resolved**: Users can now edit responses smoothly on mobile without interference, fixing a longstanding hover issue.
- **🔄 Temporary Chat Message Duplication Fixed**: Eliminated buggy behavior where messages were being unnecessarily repeated in temporary chat mode, ensuring a smooth and consistent conversation flow.
  
## [1.1.0] - 2025-04-02
### Fixes Ameritas Custom changes -2025-04-02
- **🛠️RAG Page number issue fixed**: Issue with non-OCR Page Number metadata fixed
- **🛠️Web Search Proxy Issue**: Web Search enabled for chat using Duckduckgo with Proxy setup in web util
  
### Modified Ameritas Custom changes -2025-03-24
- **📝RAG Updates** - New changes allocated for Page Number Append to Loaded content and Metadata to Vector DB
- **🔧Tool and Function Usage** - Updated logic for secure usage of Tools and Functions for used libraries to be registered before usage

### Vulnerability Fixes 2025-03-12
- **🛠️CWE-209**: Replaced direct exception messages with generic responses in user-facing outputs. 
- **🛠️CWE-1004**: Ensured all "set_cookie" calls use "httponly", "secure", and "samesite" attributes. outputs. 
- **🛠️CWE-1333**: Modified the RE to address the Inefficient Regular Expression Complexity 
- **🛠️CWE-73**: Validated the path to address External Control of File Name or Path
- **🛠️CWE-400**: Sanitized the tag details before passign to the regular expression
  
### Modified Ameritas Custom changes -2025-02-20
- **🛠️Custom Changes Merged**: OpenWebUI version 0.5.14 project structure retrofitted with Ameritas Custom changes from version 1.0 release
- **📝OCR logic updated**: Added page formatting and page Number for OCR processing. Segregated OCR Logic for Retrieval Logic.
- **🔧Config and Setting**: Updated version0.5.14 configs to match with Ameritas AWS config setup. Modified requirement.txt for new dependencies
- **🔍Topic Modeling**: Topic Modeling logic allocated for chat transcripts extraction and lda,Lsa and BertTopic

### Fixed  in OpenWebUI [0.5.14] - 2025-02-17

- **🔧 Critical Import Error Resolved**: Fixed a circular import issue preventing 'override_static' from being correctly imported in 'open_webui.config', ensuring smooth system initialization and stability.


### Added in  OpenWebUI [0.5.13] - 2025-02-17

- **🌐 Full Context Mode for Web Search**: Enable highly accurate web searches by utilizing full context mode—ideal for models with large context windows, ensuring more precise and insightful results.
- **⚡ Optimized Asynchronous Web Search**: Web searches now load significantly faster with optimized async support, providing users with quicker, more efficient information retrieval.
- **🔄 Auto Text Direction for RTL Languages**: Automatic text alignment based on language input, ensuring seamless conversation flow for Arabic, Hebrew, and other right-to-left scripts.
- **🚀 Jupyter Notebook Support for Code Execution**: The "Run" button in code blocks can now use Jupyter for execution, offering a powerful, dynamic coding experience directly in the chat.
- **🗑️ Message Delete Confirmation Dialog**: Prevent accidental deletions with a new confirmation prompt before removing messages, adding an additional layer of security to your chat history.
- **📥 Download Button for SVG Diagrams**: SVG diagrams generated within chat can now be downloaded instantly, making it easier to save and share complex visual data.
- **✨ General UI/UX Improvements and Backend Stability**: A refined interface with smoother interactions, improved layouts, and backend stability enhancements for a more reliable, polished experience.

### Fixed in OpenWebUI  [0.5.13] - 2025-02-17

- **🛠️ Temporary Chat Message Continue Button Fixed**: The "Continue Response" button for temporary chats now works as expected, ensuring an uninterrupted conversation flow.

### Changed in OpenWebUI  [0.5.13] - 2025-02-17

- **📝 Prompt Variable Update**: Deprecated square bracket '[]' indicators for prompt variables; now requires double curly brackets '{{}}' for consistency and clarity.
- **🔧 Stability Enhancements**: Error handling improved in chat history, ensuring smoother operations when reviewing previous messages.

### Added in OpenWebUI [0.5.12] - 2025-02-13

- **🛠️ Multiple Tool Calls Support for Native Function Mode**: Functions now can call multiple tools within a single response, unlocking better automation and workflow flexibility when using native function calling.

### Fixed in OpenWebUI [0.5.12] - 2025-02-13

- **📝 Playground Text Completion Restored**: Addressed an issue where text completion in the Playground was not functioning.
- **🔗 Direct Connections Now Work for Regular Users**: Fixed a bug where users with the 'user' role couldn't establish direct API connections, enabling seamless model usage for all user tiers.
- **⚡ Landing Page Input No Longer Lags with Long Text**: Improved input responsiveness on the landing page, ensuring fast and smooth typing experiences even when entering long messages.
- **🔧 Parameter in Functions Fixed**: Fixed an issue where the reserved parameters wasn’t recognized within functions, restoring full functionality for advanced task-based automation.


### Added in OpenWebUI [0.5.11] - 2025-02-13

- **🎤 Kokoro-JS TTS Support**: A new on-device, high-quality text-to-speech engine has been integrated, vastly improving voice generation quality—everything runs directly in your browser.
- **🐍 Jupyter Notebook Support in Code Interpreter**: Now, you can configure Code Interpreter to run Python code not only via Pyodide but also through Jupyter, offering a more robust coding environment for AI-driven computations and analysis.
- **🔗 Direct API Connections for Private & Local Inference**: You can now connect Open WebUI to your private or localhost API inference endpoints. CORS must be enabled, but this unlocks direct, on-device AI infrastructure support.
- **🔍 Advanced Domain Filtering for Web Search**: You can now specify which domains should be included or excluded from web searches, refining results for more relevant information retrieval.
- **🚀 Improved Image Generation Metadata Handling**: Generated images now retain metadata for better organization and future retrieval.
- **📂 S3 Key Prefix Support**: Fine-grained control over S3 storage file structuring with configurable key prefixes.
- **📸 Support for Image-Only Messages**: Send messages containing only images, facilitating more visual-centric interactions.
- **🌍 Updated Translations**: German, Spanish, Traditional Chinese, and Catalan translations updated for better multilingual support.

### Fixed in OpenWebUI [0.5.11] - 2025-02-13

- **🔧 OAuth Debug Logs & Username Claim Fixes**: Debug logs have been added for OAuth role and group management, with fixes ensuring proper OAuth username retrieval and claim handling.
- **📌 Citations Formatting & Toggle Fixes**: Inline citation toggles now function correctly, and citations with more than three sources are now fully visible when expanded.
- **📸 ComfyUI Maximum Seed Value Constraint Fixed**: The maximum allowed seed value for ComfyUI has been corrected, preventing unintended behavior.
- **🔑 Connection Settings Stability**: Addressed connection settings issues that were causing instability when saving configurations.
- **📂 GGUF Model Upload Stability**: Fixed upload inconsistencies for GGUF models, ensuring reliable local model handling.
- **🔧 Web Search Configuration Bug**: Fixed issues where web search filters and settings weren't correctly applied.
- **💾 User Settings Persistence Fix**: Ensured user-specific settings are correctly saved and applied across sessions.
- **🔄 OpenID Username Retrieval Enhancement**: Usernames are now correctly picked up and assigned for OpenID Connect (OIDC) logins.



### Fixed in OpenWebUI [0.5.10] - 2025-02-05

- **⚙️ System Prompts Now Properly Templated via API**: Resolved an issue where system prompts were not being correctly processed when used through the API, ensuring template variables now function as expected.
- **📝 '<thinking>' Tag Display Issue Fixed**: Fixed a bug where the 'thinking' tag was disrupting content rendering, ensuring clean and accurate text display.
- **💻 Code Interpreter Stability with Custom Functions**: Addressed failures when using the Code Interpreter with certain custom functions like Anthropic, ensuring smoother execution and better compatibility.


### Fixed in [0.5.9] - 2025-02-05

- **💡 "Think" Tag Display Issue**: Resolved a bug where the "Think" tag was not functioning correctly, ensuring proper visualization of the model's reasoning process before delivering responses.


### Added in OpenWebUI [0.5.8] - 2025-02-05

- **🖥️ Code Interpreter**: Models can now execute code in real time to refine their answers dynamically, running securely within a sandboxed browser environment using Pyodide. Perfect for calculations, data analysis, and AI-assisted coding tasks!
- **💬 Redesigned Chat Input UI**: Enjoy a sleeker and more intuitive message input with improved feature selection, making it easier than ever to toggle tools, enable search, and interact with AI seamlessly.
- **🛠️ Native Tool Calling Support (Experimental)**: Supported models can now call tools natively, reducing query latency and improving contextual responses. More enhancements coming soon!
- **🔗 Exa Search Engine Integration**: A new search provider has been added, allowing users to retrieve up-to-date and relevant information without leaving the chat interface.
- **🌍 Localized Dates & Times**: Date and time formats now match your system locale, ensuring a more natural, region-specific experience.
- **📎 User Headers for External Embedding APIs**: API calls to external embedding services now include user-related headers.
- **🌍 "Always On" Web Search Toggle**: A new option under Settings > Interface allows users to enable Web Search by default—transform Open WebUI into your go-to search engine, ensuring AI-powered results with every query.
- **🚀 General Performance & Stability**: Significant improvements across the platform for a faster, more reliable experience.
- **🖼️ UI/UX Enhancements**: Numerous design refinements improving readability, responsiveness, and accessibility.
- **🌍 Improved Translations**: Chinese, Korean, French, Ukrainian and Serbian translations have been updated with refined terminologies for better clarity.

### Fixed in OpenWebUI [0.5.8] - 2025-02-05

- **🔄 OAuth Name Field Fallback**: Resolves OAuth login failures by using the email field as a fallback when a name is missing.
- **🔑 Google Drive Credentials Restriction**: Ensures only authenticated users can access Google Drive credentials for enhanced security.
- **🌐 DuckDuckGo Search Rate Limit Handling**: Fixes issues where users would encounter 202 errors due to rate limits when using DuckDuckGo for web search.
- **📁 File Upload Permission Indicator**: Users are now notified when they lack permission to upload files, improving clarity on system restrictions.
- **🔧 Max Tokens Issue**: Fixes cases where 'max_tokens' were not applied correctly, ensuring proper model behavior.
- **🔍 Validation for RAG Web Search URLs**: Filters out invalid or unsupported URLs when using web-based retrieval augmentation.
- **🖋️ Title Generation Bug**: Fixes inconsistencies in title generation, ensuring proper chat organization.

### Removed in OpenWebUI [0.5.8] - 2025-02-05

- **⚡ Deprecated Non-Web Worker Pyodide Execution**: Moves entirely to browser sandboxing for better performance and security.


### Added in  OpenWebUI [0.5.7] - 2025-01-23

- **🌍 Enhanced Internationalization (i18n)**: Refined and expanded translations for greater global accessibility and a smoother experience for international users.

### Fixed in OpenWebUI [0.5.7] - 2025-01-23

- **🔗 Connection Model ID Resolution**: Resolved an issue preventing model IDs from registering in connections.
- **💡 Prefix ID for Ollama Connections**: Fixed a bug where prefix IDs in Ollama connections were non-functional.
- **🔧 Ollama Model Enable/Disable Functionality**: Addressed the issue of enable/disable toggles not working for Ollama base models.
- **🔒 RBAC Permissions for Tools and Models**: Corrected incorrect Role-Based Access Control (RBAC) permissions for tools and models, ensuring that users now only access features according to their assigned privileges, enhancing security and role clarity.


### Added in OpenWebUI [0.5.6] - 2025-01-22

- **🧠 Effortful Reasoning Control for OpenAI Models**: Introduced the reasoning_effort parameter in chat controls for supported OpenAI models, enabling users to fine-tune how much cognitive effort a model dedicates to its responses, offering greater customization for complex queries and reasoning tasks.

### Fixed in OpenWebUI  [0.5.6] - 2025-01-22

- **🔄 Chat Controls Loading UI Bug**: Resolved an issue where collapsible chat controls appeared as "loading," ensuring a smoother and more intuitive user experience for managing chat settings.

### Changed in OpenWebUI  [0.5.6] - 2025-01-22

- **🔧 Updated Ollama Model Creation**: Revamped the Ollama model creation method to align with their new JSON payload format, ensuring seamless compatibility and more efficient model setup workflows.


### Added in OpenWebUI [0.5.5] - 2025-01-22

- **🤔 Native 'Think' Tag Support**: Introduced the new 'think' tag support that visually displays how long the model is thinking, omitting the reasoning content itself until the next turn. Ideal for creating a more streamlined and focused interaction experience.
- **🖼️ Toggle Image Generation On/Off**: In the chat input menu, you can now easily toggle image generation before initiating chats, providing greater control and flexibility to suit your needs.
- **🔒 Chat Controls Permissions**: Admins can now disable chat controls access for users, offering tighter management and customization over user interactions.
- **🔍 Web Search & Image Generation Permissions**: Easily disable web search and image generation for specific users, improving workflow governance and security for certain environments.
- **🗂️ S3 and GCS Storage Provider Support**: Scaled deployments now benefit from expanded storage options with Amazon S3 and Google Cloud Storage seamlessly integrated as providers.
- **🎨 Enhanced Model Management**: Reintroduced the ability to download and delete models directly in the admin models settings page to minimize user confusion and aid efficient model management.
- **🔗 Improved Connection Handling**: Enhanced backend to smoothly handle multiple identical base URLs, allowing more flexible multi-instance configurations with fewer hiccups.
- **✨ General UI/UX Refinements**: Numerous tweaks across the WebUI make navigation and usability even more user-friendly and intuitive.
- **🌍 Translation Enhancements**: Various translation updates ensure smoother and more polished interactions for international users.

### Fixed in OpenWebUI [0.5.5] - 2025-01-22

- **⚡ MPS Functionality for Mac Users**: Fixed MPS support, ensuring smooth performance and compatibility for Mac users leveraging MPS.
- **📡 Ollama Connection Management**: Resolved the issue where deleting all Ollama connections prevented adding new ones.

### Changed in OpenWebUI [0.5.5] - 2025-01-22

- **⚙️ General Stability Refac**: Backend refactoring delivers a more stable, robust platform.
- **🖥️ Desktop App Preparations**: Ongoing work to support the upcoming Open WebUI desktop app. Follow our progress and updates here: https://github.com/open-webui/desktop


### Added in OpenWebUI [0.5.4] - 2025-01-05

- **🔄 Clone Shared Chats**: Effortlessly clone shared chats to save time and streamline collaboration, perfect for reusing insightful discussions or custom setups.
- **📣 Native Notifications for Channel Messages**: Stay informed with integrated desktop notifications for channel messages, ensuring you never miss important updates while multitasking.
- **🔥 Torch MPS Support**: MPS support for Mac users when Open WebUI is installed directly, offering better performance and compatibility for AI workloads.
- **🌍 Enhanced Translations**: Small improvements to various translations, ensuring a smoother global user experience.

### Fixed in OpenWebUI [0.5.4] - 2025-01-05

- **🖼️ Image-Only Messages in Channels**: You can now send images without accompanying text or content in channels.
- **❌ Proper Exception Handling**: Enhanced error feedback by ensuring exceptions are raised clearly, reducing confusion and promoting smoother debugging.
- **🔍 RAG Query Generation Restored**: Fixed query generation issues for Retrieval-Augmented Generation, improving retrieval accuracy and ensuring seamless functionality.
- **📩 MOA Response Functionality Fixed**: Addressed an error with the MOA response generation feature.
- **💬 Channel Thread Loading with 50+ Messages**: Resolved an issue where channel threads stalled when exceeding 50 messages, ensuring smooth navigation in active discussions.
- **🔑 API Endpoint Restrictions Resolution**: Fixed a critical bug where the 'API_KEY_ALLOWED_ENDPOINTS' setting was not functioning as intended, ensuring API access is limited to specified endpoints for enhanced security.
- **🛠️ Action Functions Restored**: Corrected an issue preventing action functions from working, restoring their utility for customized automations and workflows.
- **📂 Temporary Chat JSON Export Fix**: Resolved a bug blocking temporary chats from being exported in JSON format, ensuring seamless data portability.

### Changed in OpenWebUI [0.5.4] - 2025-01-05

- **🎛️ Sidebar UI Tweaks**: Chat folders, including pinned folders, now display below the Chats section for better organization; the "New Folder" button has been relocated to the Chats section for a more intuitive workflow.
- **🏗️ Real-Time Save Disabled by Default**: The 'ENABLE_REALTIME_CHAT_SAVE' setting is now off by default, boosting response speed for users who prioritize performance in high-paced workflows or less critical scenarios.
- **🎤 Audio Input Echo Cancellation**: Audio input now features echo cancellation enabled by default, reducing audio feedback for improved clarity during conversations or voice-based interactions.
- **🔧 General Reliability Improvements**: Numerous under-the-hood enhancements have been made to improve platform stability, boost overall performance, and ensure a more seamless, dependable experience across workflows.


### Added in [0.5.3] - 2024-12-31

- **💬 Channel Reactions with Built-In Emoji Picker**: Easily express yourself in channel threads and messages with reactions, featuring an intuitive built-in emoji picker for seamless selection.
- **🧵 Threads for Channels**: Organize discussions within channels by creating threads, improving clarity and fostering focused conversations.
- **🔄 Reset Button for SVG Pan/Zoom**: Added a handy reset button to SVG Pan/Zoom, allowing users to quickly return diagrams or visuals to their default state without hassle.
- **⚡ Realtime Chat Save Environment Variable**: Introduced the ENABLE_REALTIME_CHAT_SAVE environment variable. Choose between faster responses by disabling realtime chat saving or ensuring chunk-by-chunk data persistency for critical operations.
- **🌍 Translation Enhancements**: Updated and refined translations across multiple languages, providing a smoother experience for international users.
- **📚 Improved Documentation**: Expanded documentation on functions, including clearer guidance on function plugins and detailed instructions for migrating to v0.5. This ensures users can adapt and harness new updates more effectively. (https://docs.openwebui.com/features/plugin/)

### Fixed in OpenWebUI [0.5.3] - 2024-12-31

- **🛠️ Ollama Parameters Respected**: Resolved an issue where input parameters for Ollama were being ignored, ensuring precise and consistent model behavior.
- **🔧 Function Plugin Outlet Hook Reliability**: Fixed a bug causing issues with 'event_emitter' and outlet hooks in filter function plugins, guaranteeing smoother operation within custom extensions.
- **🖋️ Weird Custom Status Descriptions**: Adjusted the formatting and functionality for custom user statuses, ensuring they display correctly and intuitively.
- **🔗 Restored API Functionality**: Fixed a critical issue where APIs were not operational for certain configurations, ensuring uninterrupted access.
- **⏳ Custom Pipe Function Completion**: Resolved an issue where chats using specific custom pipe function plugins weren’t finishing properly, restoring consistent chat workflows.
- **✅ General Stability Enhancements**: Implemented various under-the-hood improvements to boost overall reliability, ensuring smoother and more consistent performance across the WebUI.

### Added in OpenWebUI [0.5.2] - 2024-12-26

- **🖊️ Typing Indicators in Channels**: Know exactly who’s typing in real-time within your channels, enhancing collaboration and keeping everyone engaged.
- **👤 User Status Indicators**: Quickly view a user’s status by clicking their profile image in channels for better coordination and availability insights.
- **🔒 Configurable API Key Authentication Restrictions**: Flexibly configure endpoint restrictions for API key authentication, now off by default for a smoother setup in trusted environments.

### Fixed in OpenWebUI [0.5.2] - 2024-12-26

- **🔧 Playground Functionality Restored**: Resolved a critical issue where the playground wasn’t working, ensuring seamless experimentation and troubleshooting workflows.
- **📊 Corrected Ollama Usage Statistics**: Fixed a calculation error in Ollama’s usage statistics, providing more accurate tracking and insights for better resource management.
- **🔗 Pipelines Outlet Hook Registration**: Addressed an issue where outlet hooks for pipelines weren’t registered, restoring functionality and consistency in pipeline workflows.
- **🎨 Image Generation Error**: Resolved a persistent issue causing errors with 'get_automatic1111_api_auth()' to ensure smooth image generation workflows.
- **🎙️ Text-to-Speech Error**: Fixed the missing argument in Eleven Labs’ 'get_available_voices()', restoring full text-to-speech capabilities for uninterrupted voice interactions.
- **🖋️ Title Generation Issue**: Fixed a bug where title generation was not working in certain cases, ensuring consistent and reliable chat organization.


### Added in OpenWebUI [0.5.1] - 2024-12-25

- **🔕 Notification Sound Toggle**: Added a new setting under Settings > Interface to disable notification sounds, giving you greater control over your workspace environment and focus.

### Fixed in OpenWebUI [0.5.1] - 2024-12-25

- **🔄 Non-Streaming Response Visibility**: Resolved an issue where non-streaming responses were not displayed, ensuring all responses are now reliably shown in your conversations.
- **🖋️ Title Generation with OpenAI APIs**: Fixed a bug preventing title generation when using OpenAI APIs, restoring the ability to automatically generate chat titles for smoother organization.
- **👥 Admin Panel User List**: Addressed the issue where only 50 users were visible in the admin panel. You can now manage and view all users without restrictions.
- **🖼️ Image Generation Error**: Fixed the issue causing 'get_automatic1111_api_auth()' errors in image generation, ensuring seamless creative workflows.
- **⚙️ Pipeline Settings Loading Issue**: Resolved a problem where pipeline settings were stuck at the loading screen, restoring full configurability in the admin panel.


### Added in OpenWebUI  [0.5.0] - 2024-12-25

- **💬 True Asynchronous Chat Support**: Create chats, navigate away, and return anytime with responses ready. Ideal for reasoning models and multi-agent workflows, enhancing multitasking like never before.
- **🔔 Chat Completion Notifications**: Never miss a completed response. Receive instant in-UI notifications when a chat finishes in a non-active tab, keeping you updated while you work elsewhere.
- **🌐 Notification Webhook Integration**: Get alerts via webhooks even when your tab is closed! Configure your webhook URL in Settings > Account and receive timely updates for long-running chats or external integration needs.
- **📚 Channels (Beta)**: Explore Discord/Slack-style chat rooms designed for real-time collaboration between users and AIs. Build bots for channels and unlock asynchronous communication for proactive multi-agent workflows. Opt-in via Admin Settings > General. A Comprehensive Bot SDK tutorial (https://github.com/open-webui/bot) is incoming, so stay tuned!
- **🖼️ Client-Side Image Compression**: Now compress images before upload (Settings > Interface), saving bandwidth and improving performance seamlessly.
- **🛠️ OAuth Management for User Groups**: Enable group-level management via OAuth integration for enhanced control and scalability in collaborative environments.
- **✅ Structured Output for Ollama**: Pass structured data output directly to Ollama, unlocking new possibilities for streamlined automation and precise data handling.
- **📜 Offline Swagger Documentation**: Developer-friendly Swagger API docs are now available offline, ensuring full accessibility wherever you are.
- **📸 Quick Screen Capture Button**: Effortlessly capture your screen with a single click from the message input menu.
- **🌍 i18n Updates**: Improved and refined translations across several languages, including Ukrainian, German, Brazilian Portuguese, Catalan, and more, ensuring a seamless global user experience.

### Fixed in OpenWebUI  [0.5.0] - 2024-12-25

- **📋 Table Export to CSV**: Resolved issues with CSV export where headers were missing or errors occurred due to values with commas, ensuring smooth and reliable data handling.
- **🔓 BYPASS_MODEL_ACCESS_CONTROL**: Fixed an issue where users could see models but couldn’t use them with 'BYPASS_MODEL_ACCESS_CONTROL=True', restoring proper functionality for environments leveraging this setting.

### Changed in OpenWebUI  [0.5.0] - 2024-12-25

- **💡 API Key Authentication Restriction**: Narrowed API key auth permissions to '/api/models' and '/api/chat/completions' for enhanced security and better API governance.
- **⚙️ Backend Overhaul for Performance**: Major backend restructuring; a heads-up that some "Functions" using internal variables may face compatibility issues. Moving forward, websocket support is mandatory to ensure Open WebUI operates seamlessly.

### Removed in OpenWebUI  [0.5.0] - 2024-12-25

- **⚠️ Legacy Functionality Clean-Up**: Deprecated outdated backend systems that were non-essential or overlapped with newer implementations, allowing for a leaner, more efficient platform.

### Added in OpenWebUI [0.4.8] - 2024-12-07

- **🔓 Bypass Model Access Control**: Introduced the 'BYPASS_MODEL_ACCESS_CONTROL' environment variable. Easily bypass model access controls for user roles when access control isn't required, simplifying workflows for trusted environments.
- **📝 Markdown in Banners**: Now supports markdown for banners, enabling richer, more visually engaging announcements.
- **🌐 Internationalization Updates**: Enhanced translations across multiple languages, further improving accessibility and global user experience.
- **🎨 Styling Enhancements**: General UI style refinements for a cleaner and more polished interface.
- **📋 Rich Text Reliability**: Improved the reliability and stability of rich text input across chats for smoother interactions.

### Fixed in OpenWebUI [0.4.8] - 2024-12-07

- **💡 Tailwind Build Issue**: Resolved a breaking bug caused by Tailwind, ensuring smoother builds and overall system reliability.
- **📚 Knowledge Collection Query Fix**: Addressed API endpoint issues with querying knowledge collections, ensuring accurate and reliable information retrieval.


### Added in OpenWebUI  [0.4.7] - 2024-12-01

- **✨ Prompt Input Auto-Completion**: Type a prompt and let AI intelligently suggest and complete your inputs. Simply press 'Tab' or swipe right on mobile to confirm. Available only with Rich Text Input (default setting). Disable via Admin Settings for full control.
- **🌍 Improved Translations**: Enhanced localization for multiple languages, ensuring a more polished and accessible experience for international users.

### Fixed in OpenWebUI  [0.4.7] - 2024-12-01

- **🛠️ Tools Export Issue**: Resolved a critical issue where exporting tools wasn’t functioning, restoring seamless export capabilities.
- **🔗 Model ID Registration**: Fixed an issue where model IDs weren’t registering correctly in the model editor, ensuring reliable model setup and tracking.
- **🖋️ Textarea Auto-Expansion**: Corrected a bug where textareas didn’t expand automatically on certain browsers, improving usability for multi-line inputs.
- **🔧 Ollama Embed Endpoint**: Addressed the /ollama/embed endpoint malfunction, ensuring consistent performance and functionality.

### Changed in OpenWebUI  [0.4.7] - 2024-12-01

- **🎨 Knowledge Base Styling**: Refined knowledge base visuals for a cleaner, more modern look, laying the groundwork for further enhancements in upcoming releases.

### Added in OpenWebUI  [0.4.6] - 2024-11-26

- **🌍 Enhanced Translations**: Various language translations improved to make the WebUI more accessible and user-friendly worldwide.

### Fixed in OpenWebUI  [0.4.6] - 2024-11-26

- **✏️ Textarea Shifting Bug**: Resolved the issue where the textarea shifted unexpectedly, ensuring a smoother typing experience.
- **⚙️ Model Configuration Modal**: Fixed the issue where the models configuration modal introduced in 0.4.5 wasn’t working for some users.
- **🔍 Legacy Query Support**: Restored functionality for custom query generation in RAG when using legacy prompts, ensuring both default and custom templates now work seamlessly.
- **⚡ Improved General Reliability**: Various minor fixes improve platform stability and ensure a smoother overall experience across workflows.

### Added in OpenWebUI [0.4.5] - 2024-11-26

- **🎨 Model Order/Defaults Reintroduced**: Brought back the ability to set model order and default models, now configurable via Admin Settings > Models > Configure (Gear Icon).

### Fixed in OpenWebUI [0.4.5] - 2024-11-26

- **🔍 Query Generation Issue**: Resolved an error in web search query generation, enhancing search accuracy and ensuring smoother search workflows.
- **📏 Textarea Auto Height Bug**: Fixed a layout issue where textarea input height was shifting unpredictably, particularly when editing system prompts.
- **🔑 Ollama Authentication**: Corrected an issue with Ollama’s authorization headers, guaranteeing reliable authentication across all endpoints.
- **⚙️ Missing Min_P Save**: Resolved an issue where the 'min_p' parameter was not being saved in configurations.
- **🛠️ Tools Description**: Fixed a key issue that omitted tool descriptions in tools payload.

### Added in  OpenWebUI [0.4.4] - 2024-11-22

- **🌐 Translation Updates**: Refreshed Catalan, Brazilian Portuguese, German, and Ukrainian translations, further enhancing the platform's accessibility and improving the experience for international users.

### Fixed in OpenWebUI  [0.4.4] - 2024-11-22

- **📱 Mobile Controls Visibility**: Resolved an issue where the controls button was not displaying on the new chats page for mobile users, ensuring smoother navigation and functionality on smaller screens.
- **📷 LDAP Profile Image Issue**: Fixed an LDAP integration bug related to profile images, ensuring seamless authentication and a reliable login experience for users.
- **⏳ RAG Query Generation Issue**: Addressed a significant problem where RAG query generation occurred unnecessarily without attached files, drastically improving speed and reducing delays during chat completions.

### Changed in OpenWebUI  [0.4.4] - 2024-11-22

- **⚙️ Legacy Event Emitter Support**: Reintroduced compatibility with legacy "citation" types for event emitters in tools and functions, providing smoother workflows and broader tool support for users.


### Added in OpenWebUI [0.4.3] - 2024-11-21

- **📚 Inline Citations for RAG Results**: Get seamless inline citations for Retrieval-Augmented Generation (RAG) responses using the default RAG prompt. Note: This feature only supports newly uploaded files, improving traceability and providing source clarity.
- **🎨 Better Rich Text Input Support**: Enjoy smoother and more reliable rich text formatting for chats, enhancing communication quality.
- **⚡ Faster Model Retrieval**: Implemented caching optimizations for faster model loading, providing a noticeable speed boost across workflows. Further improvements are on the way!

### Fixed in OpenWebUI [0.4.3] - 2024-11-21

- **🔗 Pipelines Feature Restored**: Resolved a critical issue that previously prevented Pipelines from functioning, ensuring seamless workflows.
- **✏️ Missing Suffix Field in Ollama Form**: Added the missing "suffix" field to the Ollama generate form, enhancing customization options.

### Changed

- **🗂️ Renamed "Citations" to "Sources"**: Improved clarity and consistency by renaming the "citations" field to "sources" in messages.

### Fixed in OpenWebUI [0.4.2] - 2024-11-20

- **📁 Knowledge Files Visibility Issue**: Resolved the bug preventing individual files in knowledge collections from displaying when referenced with '#'.
- **🔗 OpenAI Endpoint Prefix**: Fixed the issue where certain OpenAI connections that deviate from the official API spec weren’t working correctly with prefixes.
- **⚔️ Arena Model Access Control**: Corrected an issue where arena model access control settings were not being saved.
- **🔧 Usage Capability Selector**: Fixed the broken usage capabilities selector in the model editor.


### Added in OpenWebUI [0.4.1] - 2024-11-19

- **📊 Enhanced Feedback System**: Introduced a detailed 1-10 rating scale for feedback alongside thumbs up/down, preparing for more precise model fine-tuning and improving feedback quality.
- **ℹ️ Tool Descriptions on Hover**: Easily access tool descriptions by hovering over the message input, providing a smoother workflow with more context when utilizing tools.

### Fixed in OpenWebUI [0.4.1] - 2024-11-19

- **🗑️ Graceful Handling of Deleted Users**: Resolved an issue where deleted users caused workspace items (models, knowledge, prompts, tools) to fail, ensuring reliable workspace loading.
- **🔑 API Key Creation**: Fixed an issue preventing users from creating new API keys, restoring secure and seamless API management.
- **🔗 HTTPS Proxy Fix**: Corrected HTTPS proxy issues affecting the '/api/v1/models/' endpoint, ensuring smoother, uninterrupted model management.


### Added in OpenWebUI [0.4.0] - 2024-11-19

- **👥 User Groups**: You can now create and manage user groups, making user organization seamless.
- **🔐 Group-Based Access Control**: Set granular access to models, knowledge, prompts, and tools based on user groups, allowing for more controlled and secure environments.
- **🛠️ Group-Based User Permissions**: Easily manage workspace permissions. Grant users the ability to upload files, delete, edit, or create temporary chats, as well as define their ability to create models, knowledge, prompts, and tools.
- **🔑 LDAP Support**: Newly introduced LDAP authentication adds robust security and scalability to user management.
- **🌐 Enhanced OpenAI-Compatible Connections**: Added prefix ID support to avoid model ID clashes, with explicit model ID support for APIs lacking '/models' endpoint support, ensuring smooth operation with custom setups.
- **🔐 Ollama API Key Support**: Now manage credentials for Ollama when set behind proxies, including the option to utilize prefix ID for proper distinction across multiple Ollama instances.
- **🔄 Connection Enable/Disable Toggle**: Easily enable or disable individual OpenAI and Ollama connections as needed.
- **🎨 Redesigned Model Workspace**: Freshly redesigned to improve usability for managing models across users and groups.
- **🎨 Redesigned Prompt Workspace**: A fresh UI to conveniently organize and manage prompts.
- **🧩 Sorted Functions Workspace**: Functions are now automatically categorized by type (Action, Filter, Pipe), streamlining management.
- **💻 Redesigned Collaborative Workspace**: Enhanced support for multiple users contributing to models, knowledge, prompts, or tools, improving collaboration.
- **🔧 Auto-Selected Tools in Model Editor**: Tools enabled through the model editor are now automatically selected, whereas previously it only gave users the option to enable the tool, reducing manual steps and enhancing efficiency.
- **🔔 Web Search & Tools Indicator**: A clear indication now shows when web search or tools are active, reducing confusion.
- **🔑 Toggle API Key Auth**: Tighten security by easily enabling or disabling API key authentication option for Open WebUI.
- **🗂️ Agentic Retrieval**: Improve RAG accuracy via smart pre-processing of chat history to determine the best queries before retrieval.
- **📁 Large Text as File Option**: Optionally convert large pasted text into a file upload, keeping the chat interface cleaner.
- **🗂️ Toggle Citations for Models**: Ability to disable citations has been introduced in the model editor.
- **🔍 User Settings Search**: Quickly search for settings fields, improving ease of use and navigation.
- **🗣️ Experimental SpeechT5 TTS**: Local SpeechT5 support added for improved text-to-speech capabilities.
- **🔄 Unified Reset for Models**: A one-click option has been introduced to reset and remove all models from the Admin Settings.
- **🛠️ Initial Setup Wizard**: The setup process now explicitly informs users that they are creating an admin account during the first-time setup, ensuring clarity. Previously, users encountered the login page right away without this distinction.
- **🌐 Enhanced Translations**: Several language translations, including Ukrainian, Norwegian, and Brazilian Portuguese, were refined for better localization.

### Fixed in OpenWebUI [0.4.0] - 2024-11-19

- **🎥 YouTube Video Attachments**: Fixed issues preventing proper loading and attachment of YouTube videos as files.
- **🔄 Shared Chat Update**: Corrected issues where shared chats were not updating, improving collaboration consistency.
- **🔍 DuckDuckGo Rate Limit Fix**: Addressed issues with DuckDuckGo search integration, enhancing search stability and performance when operating within rate limits.
- **🧾 Citations Relevance Fix**: Adjusted the relevance percentage calculation for citations, so that Open WebUI properly reflect the accuracy of a retrieved document in RAG, ensuring users get clearer insights into sources.
- **🔑 Jina Search API Key Requirement**: Added the option to input an API key for Jina Search, ensuring smooth functionality as keys are now mandatory.

### Changed in OpenWebUI [0.4.0] - 2024-11-19

- **🛠️ Functions Moved to Admin Panel**: As Functions operate as advanced plugins, they are now accessible from the Admin Panel instead of the workspace.
- **🛠️ Manage Ollama Connections**: The "Models" section in Admin Settings has been relocated to Admin Settings > "Connections" > Ollama Connections. You can now manage Ollama instances via a dedicated "Manage Ollama" modal from "Connections", streamlining the setup and configuration of Ollama models.
- **📊 Base Models in Admin Settings**: Admins can now find all base models, both connections or functions, in the "Models" Admin setting. Global model accessibility can be enabled or disabled here. Models are private by default, requiring explicit permission assignment for user access.
- **📌 Sticky Model Selection for New Chats**: The model chosen from a previous chat now persists when creating a new chat. If you click "New Chat" again from the new chat page, it will revert to your default model.
- **🎨 Design Refactoring**: Overall design refinements across the platform have been made, providing a more cohesive and polished user experience.

### Removed in OpenWebUI [0.4.0] - 2024-11-19

- **📂 Model List Reordering**: Temporarily removed and will be reintroduced in upcoming user group settings improvements.
- **⚙️ Default Model Setting**: Removed the ability to set a default model for users, will be reintroduced with user group settings in the future.


### Added in OpenWebUI [0.3.35] - 2024-10-26

- **🌐 Translation Update**: Added translation labels in the SearchInput and CreateCollection components and updated Brazilian Portuguese translation (pt-BR)
- **📁 Robust File Handling**: Enhanced file input handling for chat. If the content extraction fails or is empty, users will now receive a clear warning, preventing silent failures and ensuring you always know what's happening with your uploads.
- **🌍 New Language Support**: Introduced Hungarian translations and updated French translations, expanding the platform's language accessibility for a more global user base.

### Fixed in OpenWebUI [0.3.35] - 2024-10-26

- **📚 Knowledge Base Loading Issue**: Resolved a critical bug where the Knowledge Base was not loading, ensuring smooth access to your stored documents and improving information retrieval in RAG-enhanced workflows.
- **🛠️ Tool Parameters Issue**: Fixed an error where tools were not functioning correctly when required parameters were missing, ensuring reliable tool performance and more efficient task completions.
- **🔗 Merged Response Loss in Multi-Model Chats**: Addressed an issue where responses in multi-model chat workflows were being deleted after follow-up queries, improving consistency and ensuring smoother interactions across models.

### Added changes for OpenWebUI [0.3.34] - 2024-10-26

- **🔧 Feedback Export Enhancements**: Feedback history data can now be exported to JSON, allowing for seamless integration in RLHF processing and further analysis.
- **🗂️ Embedding Model Lazy Loading**: Search functionality for leaderboard reranking is now more efficient, as embedding models are lazy-loaded only when needed, optimizing performance.
- **🎨 Rich Text Input Toggle**: Users can now switch back to legacy textarea input for chat if they prefer simpler text input, though rich text is still the default until deprecation.
- **🛠️ Improved Tool Calling Mechanism**: Enhanced method for parsing and calling tools, improving the reliability and robustness of tool function calls.
- **🌐 Globalization Enhancements**: Updates to internationalization (i18n) support, further refining multi-language compatibility and accuracy.

### Fixed in [0.3.34] - 2024-10-26

- **🖥️ Folder Rename Fix for Firefox**: Addressed a persistent issue where users could not rename folders by pressing enter in Firefox, now ensuring seamless folder management across browsers.
- **🔠 Tiktoken Model Text Splitter Issue**: Resolved an issue where the tiktoken text splitter wasn’t working in Docker installations, restoring full functionality for tokenized text editing.
- **💼 S3 File Upload Issue**: Fixed a problem affecting S3 file uploads, ensuring smooth operations for those who store files on cloud storage.
- **🔒 Strict-Transport-Security Crash**: Resolved a crash when setting the Strict-Transport-Security (HSTS) header, improving stability and security enhancements.
- **🚫 OIDC Boolean Access Fix**: Addressed an issue with boolean values not being accessed correctly during OIDC logins, ensuring login reliability.
- **⚙️ Rich Text Paste Behavior**: Refined paste behavior in rich text input to make it smoother and more intuitive when pasting various content types.
- **🔨 Model Exclusion for Arena Fix**: Corrected the filter function that was not properly excluding models from the arena, improving model management.
- **🏷️ "Tags Generation Prompt" Fix**: Addressed an issue preventing custom "tags generation prompts" from registering properly, ensuring custom prompt work seamlessly.
  
## [1.0.0] - 2024-11-08
### Added Changes

- **🛠️ Milvus DB connection allocation**: External Milvus DB allocated with authentication and role allocation for application
- **📁 OCR updates**: Changes fo performance enhancement and fix for GPU memory outage.
- **🔧 Pyodide Proxy Setup**: Updated script to work with Corporate Proxy Setup.
- **🧠 Embedding Model Download**: Enabled Local install of Embedding model.
  
### Fixed

- **🔍 Vulnerability Issues**: Github Advanced Vulnerability issues fixed.
  
### Added changes for OpenWebUI [0.3.33] Changes - 2024-11-07

- **🏆 Evaluation Leaderboard**: Easily track your performance through a new leaderboard system where your ratings contribute to a real-time ranking based on the Elo system. Sibling responses (regenerations, many model chats) are required for your ratings to count in the leaderboard. Additionally, you can opt-in to share your feedback history and be part of the community-wide leaderboard. Expect further improvements as we refine the algorithm—help us build the best community leaderboard!
- **⚔️ Arena Model Evaluation**: Enable blind A/B testing of models directly from Admin Settings > Evaluation for a true side-by-side comparison. Ideal for pinpointing the best model for your needs.
- **🎯 Topic-Based Leaderboard**: Discover more accurate rankings with experimental topic-based reranking, which adjusts leaderboard standings based on tag similarity in feedback. Get more relevant insights based on specific topics!
- **📁 Folders Support for Chats**: Organize your chats better by grouping them into folders. Drag and drop chats between folders and export them seamlessly for easy sharing or analysis.
- **📤 Easy Chat Import via Drag & Drop**: Save time by simply dragging and dropping chat exports (JSON) directly onto the sidebar to import them into your workspace—streamlined, efficient, and intuitive!
- **📚 Enhanced Knowledge Collection**: Now, you can reference individual files from a knowledge collection—ideal for more precise Retrieval-Augmented Generations (RAG) queries and document analysis.
- **🏷️ Enhanced Tagging System**: Tags now take up less space! Utilize the new 'tag:' query system to manage, search, and organize your conversations more effectively without cluttering the interface.
- **🧠 Auto-Tagging for Chats**: Your conversations are now automatically tagged for improved organization, mirroring the efficiency of auto-generated titles.
- **🔍 Backend Chat Query System**: Chat filtering has become more efficient, now handled through the backend\*\* instead of your browser, improving search performance and accuracy.
- **🎮 Revamped Playground**: Experience a refreshed and optimized Playground for smoother testing, tweaks, and experimentation of your models and tools.
- **🧩 Token-Based Text Splitter**: Introducing token-based text splitting (tiktoken), giving you more precise control over how text is processed. Previously, only character-based splitting was available.
- **🔢 Ollama Batch Embeddings**: Leverage new batch embedding support for improved efficiency and performance with Ollama embedding models.
- **🔍 Enhanced Add Text Content Modal**: Enjoy a cleaner, more intuitive workflow for adding and curating knowledge content with an upgraded input modal from our Knowledge workspace.
- **🖋️ Rich Text Input for Chats**: Make your chat inputs more dynamic with support for rich text formatting. Your conversations just got a lot more polished and professional.
- **⚡ Faster Whisper Model Configurability**: Customize your local faster whisper model directly from the WebUI.
- **☁️ Experimental S3 Support**: Enable stateless WebUI instances with S3 support, greatly enhancing scalability and balancing heavy workloads.
- **🔕 Disable Update Toast**: Now you can streamline your workspace even further—choose to disable update notifications for a more focused experience.
- **🌟 RAG Citation Relevance Percentage**: Easily assess citation accuracy with the addition of relevance percentages in RAG results.
- **⚙️ Mermaid Copy Button**: Mermaid diagrams now come with a handy copy button, simplifying the extraction and use of diagram contents directly in your workflow.
- **🎨 UI Redesign**: Major interface redesign that will make navigation smoother, keep your focus where it matters, and ensure a modern look.

### Fixed

- **🎙️ Voice Note Mic Stopping Issue**: Fixed the issue where the microphone stayed active after ending a voice note recording, ensuring your audio workflow runs smoothly.

### Removed

- **👋 Goodbye Sidebar Tags**: Sidebar tag clutter is gone. We’ve shifted tag buttons to more effective query-based tag filtering for a sleeker, more agile interface.


### Added changes for OpenWebUI [0.3.32] Changes

- **🔢 Workspace Enhancements**: Added a display count for models, prompts, tools, and functions in the workspace, providing a clear overview and easier management.

### Fixed

- **🖥️ Web and YouTube Attachment Fix**: Resolved an issue where attaching web links and YouTube videos was malfunctioning, ensuring seamless integration and display within chats.
- **📞 Call Mode Activation on Landing Page**: Fixed a bug where call mode was not operational from the landing page.

### Changed

- **🔄 URL Parameter Refinement**: Updated the 'tool_ids' URL parameter to 'tools' or 'tool-ids' for more intuitive and consistent user experience.
- **🎨 Floating Buttons Styling Update**: Refactored the styling of floating buttons to intelligently adjust to the left side when there isn't enough room on the right, improving interface usability and aesthetic.
- **🔧 Enhanced Accessibility for Floating Buttons**: Implemented the ability to close floating buttons with the 'Esc' key, making workflow smoother and more efficient for users navigating via keyboard.
- **🖇️ Updated Information URL**: Information URLs now direct users to a general release page rather than a version-specific URL, ensuring access to the latest and relevant details all in one place.
- **📦 Library Dependencies Update**: Upgraded dependencies to ensure compatibility and performance optimization for pip installs.


### Added OpenWebUI [0.3.31] Changes - 2024-10-06

- **📚 Knowledge Feature**: Reimagined documents feature, now more performant with a better UI for enhanced organization; includes streamlined API integration for Retrieval-Augmented Generation (RAG). Detailed documentation forthcoming: https://docs.openwebui.com/
- **🌐 New Landing Page**: Freshly designed landing page; toggle between the new UI and the classic chat UI from Settings > Interface for a personalized experience.
- **📁 Full Document Retrieval Mode**: Toggle between full document retrieval or traditional snippets by clicking on the file item. This mode enhances document capabilities and supports comprehensive tasks like summarization by utilizing the entire content instead of RAG.
- **📄 Extracted File Content Display**: View extracted content directly by clicking on the file item, simplifying file analysis.
- **🎨 Artifacts Feature**: Render web content and SVGs directly in the interface, supporting quick iterations and live changes.
- **🖊️ Editable Code Blocks**: Supercharged code blocks now allow live editing directly in the LLM response, with live reloads supported by artifacts.
- **🔧 Code Block Enhancements**: Introduced a floating copy button in code blocks to facilitate easier code copying without scrolling.
- **🔍 SVG Pan/Zoom**: Enhanced interaction with SVG images, including Mermaid diagrams, via new pan and zoom capabilities.
- **🔍 Text Select Quick Actions**: New floating buttons appear when text is highlighted in LLM responses, offering deeper interactions like "Ask a Question" or "Explain".
- **🗃️ Database Pool Configuration**: Enhanced database handling to support scalable user growth.
- **🔊 Experimental Audio Compression**: Compress audio files to navigate around the 25MB limit for OpenAI's speech-to-text processing.
- **🔍 Query Embedding**: Adjusted embedding behavior to enhance system performance by not repeating query embedding.
- **💾 Lazy Load Optimizations**: Implemented lazy loading of large dependencies to minimize initial memory usage, boosting performance.
- **🍏 Apple Touch Icon Support**: Optimizes the display of icons for web bookmarks on Apple mobile devices.
- **🔽 Expandable Content Markdown Support**: Introducing 'details', 'summary' tag support for creating expandable content sections in markdown, facilitating cleaner, organized documentation and interactive content display.

### Fixed

- **🔘 Action Button Issue**: Resolved a bug where action buttons were not functioning, enhancing UI reliability.
- **🔄 Multi-Model Chat Loop**: Fixed an infinite loop issue in multi-model chat environments, ensuring smoother chat operations.
- **📄 Chat PDF/TXT Export Issue**: Resolved problems with exporting chat logs to PDF and TXT formats.
- **🔊 Call to Text-to-Speech Issues**: Rectified problems with text-to-speech functions to improve audio interactions.

### Changed

- **⚙️ Endpoint Renaming**: Renamed 'rag' endpoints to 'retrieval' for clearer function description.
- **🎨 Styling and Interface Updates**: Multiple refinements across the platform to enhance visual appeal and user interaction.

### Removed

- **🗑️ Deprecated 'DOCS_DIR'**: Removed the outdated 'docs_dir' variable in favor of more direct file management solutions, with direct file directory syncing and API uploads for a more integrated experience.

### Fixed Changes for Open_WebUI [0.3.30] - 2024-09-26

- **🍞 Update Available Toast Dismissal**: Enhanced user experience by ensuring that once the update available notification is dismissed, it won't reappear for 24 hours.
- **📋 Ollama /embed Form Data**: Adjusted the integration inaccuracies in the /embed form data to ensure it perfectly matches with Ollama's specifications.
- **🔧 O1 Max Completion Tokens Issue**: Resolved compatibility issues with OpenAI's o1 models max_completion_tokens param to ensure smooth operation.
- **🔄 Pip Install Database Issue**: Fixed a critical issue where database changes during pip installations were reverting and not saving chat logs, now ensuring data persistence and reliability in chat operations.
- **🏷️ Chat Rename Tab Update**: Fixed the functionality to change the web browser's tab title simultaneously when a chat is renamed, keeping tab titles consistent.

### Fixed Changes for OpenWebUI  [0.3.29] - 2023-09-25

- **🔧 KaTeX Rendering Improvement**: Resolved specific corner cases in KaTeX rendering to enhance the display of complex mathematical notation.
- **📞 'Call' URL Parameter Fix**: Corrected functionality for 'call' URL search parameter ensuring reliable activation of voice calls through URL triggers.
- **🔄 Configuration Reset Fix**: Fixed the RESET_CONFIG_ON_START to ensure settings revert to default correctly upon each startup, improving reliability in configuration management.
- **🌍 Filter Outlet Hook Fix**: Addressed issues in the filter outlet hook, ensuring all filter functions operate as intended.

### Fixed Changes for OpenWebUI  [0.3.28] - 2024-09-24

- **🔍 Web Search Functionality**: Corrected an issue where the web search option was not functioning properly.

### Fixed Changes for OpenWebUI  [0.3.27] - 2024-09-24

- **🔄 Periodic Cleanup Error Resolved**: Fixed a critical RuntimeError related to the 'periodic_usage_pool_cleanup' coroutine, ensuring smooth and efficient performance post-pip install, correcting a persisting issue from version 0.3.26.
- **📊 Enhanced LaTeX Rendering**: Improved rendering for LaTeX content, enhancing clarity and visual presentation in documents and mathematical models.


### Fixed Changes for  OpenWebUI [0.3.26] - 2024-09-24

- **🔄 Event Loop Error Resolution**: Addressed a critical error where a missing running event loop caused 'periodic_usage_pool_cleanup' to fail with pip installs. This fix ensures smoother and more reliable updates and installations, enhancing overall system stability.



### Fixed updates for OpenWebUI [0.3.25] - 2024-09-24

- **🖼️ Image Generation Functionality**: Resolved an issue where image generation was not functioning, restoring full capability for visual content creation.
- **⚖️ Rate Response Corrections**: Addressed a problem where rate responses were not working, ensuring reliable feedback mechanisms are operational.

### Added changes for OpenWebUI [0.3.24] - 2024-09-24

- **🚀 Rendering Optimization**: Significantly improved message rendering performance, enhancing user experience and webui responsiveness.
- **💖 Favorite Response Feature in Chat Overview**: Users can now mark responses as favorite directly from the chat overview, enhancing ease of retrieval and organization of preferred responses.
- **💬 Create Message Pairs with Shortcut**: Implemented creation of new message pairs using Cmd/Ctrl+Shift+Enter, making conversation editing faster and more intuitive.
- **🌍 Expanded User Prompt Variables**: Added weekday, timezone, and language information variables to user prompts to match system prompt variables.
- **🎵 Enhanced Audio Support**: Now includes support for 'audio/x-m4a' files, broadening compatibility with audio content within the platform.
- **🔏 Model URL Search Parameter**: Added an ability to select a model directly via URL parameters, streamlining navigation and model access.
- **📄 Enhanced PDF Citations**: PDF citations now open at the associated page, streamlining reference checks and document handling.
- **🔧Use of Redis in Sockets**: Enhanced socket implementation to fully support Redis, enabling effective stateless instances suitable for scalable load balancing.
- **🌍 Stream Individual Model Responses**: Allows specific models to have individualized streaming settings, enhancing performance and customization.
- **🕒 Display Model Hash and Last Modified Timestamp for Ollama Models**: Provides critical model details directly in the Models workspace for enhanced tracking.
- **❗ Update Info Notification for Admins**: Ensures administrators receive immediate updates upon login, keeping them informed of the latest changes and system statuses.

### Fixed

- **🗑️ Temporary File Handling On Windows**: Fixed an issue causing errors when accessing a temporary file being used by another process, Tools & Functions should now work as intended.
- **🔓 Authentication Toggle Issue**: Resolved the malfunction where setting 'WEBUI_AUTH=False' did not appropriately disable authentication, ensuring that user experience and system security settings function as configured.
- **🔧 Save As Copy Issue for Many Model Chats**: Resolved an error preventing users from save messages as copies in many model chats.
- **🔒 Sidebar Closure on Mobile**: Resolved an issue where the mobile sidebar remained open after menu engagement, improving user interface responsivity and comfort.
- **🛡️ Tooltip XSS Vulnerability**: Resolved a cross-site scripting (XSS) issue within tooltips, ensuring enhanced security and data integrity during user interactions.

### Changed

- **↩️ Deprecated Interface Stream Response Settings**: Moved to advanced parameters to streamline interface settings and enhance user clarity.
- **⚙️ Renamed 'speedRate' to 'playbackRate'**: Standardizes terminology, improving usability and understanding in media settings.

### Added changes for OpenWebUI  [0.3.23] - 2024-09-21

- **🚀 WebSocket Redis Support**: Enhanced load balancing capabilities for multiple instance setups, promoting better performance and reliability in WebUI.
- **🔧 Adjustable Chat Controls**: Introduced width-adjustable chat controls, enabling a personalized and more comfortable user interface.
- **🌎 i18n Updates**: Improved and updated the Chinese translations.

### Fixed

- **🌐 Task Model Unloading Issue**: Modified task handling to use the Ollama /api/chat endpoint instead of OpenAI compatible endpoint, ensuring models stay loaded and ready with custom parameters, thus minimizing delays in task execution.
- **📝 Title Generation Fix for OpenAI Compatible APIs**: Resolved an issue preventing the generation of titles, enhancing consistency and reliability when using multiple API providers.
- **🗃️ RAG Duplicate Collection Issue**: Fixed a bug causing repeated processing of the same uploaded file. Now utilizes indexed files to prevent unnecessary duplications, optimizing resource usage.
- **🖼️ Image Generation Enhancement**: Refactored OpenAI image generation endpoint to be asynchronous, preventing the WebUI from becoming unresponsive during processing, thus enhancing user experience.
- **🔓 Downgrade Authlib**: Reverted Authlib to version 1.3.1 to address and resolve issues concerning OAuth functionality.

### Changed

- **🔍 Improved Message Interaction**: Enhanced the message node interface to allow for easier focus redirection with a simple click, streamlining user interaction.
- **✨ Styling Refactor**: Updated WebUI styling for a cleaner, more modern look, enhancing user experience across the platform.

### Added changes for OpenWebUI [0.3.22] - 2024-09-19

- **⭐ Chat Overview**: Introducing a node-based interactive messages diagram for improved visualization of conversation flows.
- **🔗 Multiple Vector DB Support**: Now supports multiple vector databases, including the newly added Milvus support. Community contributions for additional database support are highly encouraged!
- **📡 Experimental Non-Stream Chat Completion**: Experimental feature allowing the use of OpenAI o1 models, which do not support streaming, ensuring more versatile model deployment.
- **🔍 Experimental Colbert-AI Reranker Integration**: Added support for "jinaai/jina-colbert-v2" as a reranker, enhancing search relevance and accuracy. Note: it may not function at all on low-spec computers.
- **🕸️ ENABLE_WEBSOCKET_SUPPORT**: Added environment variable for instances to ignore websocket upgrades, stabilizing connections on platforms with websocket issues.
- **🔊 Azure Speech Service Integration**: Added support for Azure Speech services for Text-to-Speech (TTS).
- **🎚️ Customizable Playback Speed**: Playback speed control is now available in Call mode settings, allowing users to adjust audio playback speed to their preferences.
- **🧠 Enhanced Error Messaging**: System now displays helpful error messages directly to users during chat completion issues.
- **📂 Save Model as Transparent PNG**: Model profile images are now saved as PNGs, supporting transparency and improving visual integration.
- **📱 iPhone Compatibility Adjustments**: Added padding to accommodate the iPhone navigation bar, improving UI display on these devices.
- **🔗 Secure Response Headers**: Implemented security response headers, bolstering web application security.
- **🔧 Enhanced AUTOMATIC1111 Settings**: Users can now configure 'CFG Scale', 'Sampler', and 'Scheduler' parameters directly in the admin settings, enhancing workflow flexibility without source code modifications.
- **🌍 i18n Updates**: Enhanced translations for Chinese, Ukrainian, Russian, and French, fostering a better localized experience.

### Fixed

- **🛠️ Chat Message Deletion**: Resolved issues with chat message deletion, ensuring a smoother user interaction and system stability.
- **🔢 Ordered List Numbering**: Fixed the incorrect ordering in lists.

### Changed

- **🎨 Transparent Icon Handling**: Allowed model icons to be displayed on transparent backgrounds, improving UI aesthetics.
- **📝 Improved RAG Template**: Enhanced Retrieval-Augmented Generation template, optimizing context handling and error checking for more precise operation.

## [0.1.0] - 2024-09-13

### Added new modifications 
- **📊 Chat Metrics Report**: Report on User Chat Metrics allocated to be loaded into S3 Bucket.
- **🔀 Application Session Automation**: Application start and logging started at Hosted instance restart. 
- **🛠️ Upload Files Retention**: Script allocated for data files deletion from server.
- **📄 Logging Enhancement**: Enhanced logs in json format for ELK Agent ingestion.
  
### Added changes for OpenwebUI v 0.3.21

- **📊 Document Count Display**: Now displays the total number of documents directly within the dashboard.
- **🚀 Ollama Embed API Endpoint**: Enabled /api/embed endpoint proxy support.

### Fixed

- **🐳 Docker Launch Issue**: Resolved the problem preventing Open-WebUI from launching correctly when using Docker.

### Changed

- **🔍 Enhanced Search Prompts**: Improved the search query generation prompts for better accuracy and user interaction, enhancing the overall search experience.

### Added changes for OpenwebUI v 0.3.20

- **🌐 Translation Update**: Updated Catalan translations to improve user experience for Catalan speakers.

### Fixed

- **📄 PDF Download**: Resolved a configuration issue with fonts directory, ensuring PDFs are now downloaded with the correct formatting.
- **🛠️ Installation of Tools & Functions Requirements**: Fixed a bug where necessary requirements for tools and functions were not properly installing.
- **🔗 Inline Image Link Rendering**: Enabled rendering of images directly from links in chat.
- **📞 Post-Call User Interface Cleanup**: Adjusted UI behavior to automatically close chat controls after a voice call ends, reducing screen clutter.
- **🎙️ Microphone Deactivation Post-Call**: Addressed an issue where the microphone remained active after calls.
- **✍️ Markdown Spacing Correction**: Corrected spacing in Markdown rendering, ensuring text appears neatly and as expected.
- **🔄 Message Re-rendering**: Fixed an issue causing all response messages to re-render with each new message, now improving chat performance.

### Changed

- **🌐 Refined Web Search Integration**: Deprecated the Search Query Generation Prompt threshold; introduced a toggle button for "Enable Web Search Query Generation" allowing users to opt-in to using web search more judiciously.
- **📝 Default Prompt Templates Update**: Emptied environment variable templates for search and title generation now default to the Open WebUI default prompt templates, simplifying configuration efforts.

### Added changes for Openwebui v 0.3.19

- **🌐 Translation Update**: Improved Chinese translations.

### Fixed

- **📂 DATA_DIR Overriding**: Fixed an issue to avoid overriding DATA_DIR, preventing errors when directories are set identically, ensuring smoother operation and data management.
- **🛠️ Frontmatter Extraction**: Fixed the extraction process for frontmatter in tools and functions.

### Changed

- **🎨 UI Styling**: Refined the user interface styling for enhanced visual coherence and user experience.

### Added changes for OpenwebUI v 0.3.18

- **🛠️ Direct Database Execution for Tools & Functions**: Enhanced the execution of Python files for tools and functions, now directly loading from the database for a more streamlined backend process.

### Fixed

- **🔄 Automatic Rewrite of Import Statements in Tools & Functions**: Tool and function scripts that import 'utils', 'apps', 'main', 'config' will now automatically rename these with 'open_webui.', ensuring compatibility and consistency across different modules.
- **🎨 Styling Adjustments**: Minor fixes in the visual styling to improve user experience and interface consistency.

### Added changes for OpenwebUI v 0.3.17

- **🔄 Import/Export Configuration**: Users can now import and export webui configurations from admin settings > Database, simplifying setup replication across systems.
- **🌍 Web Search via URL Parameter**: Added support for activating web search directly through URL by setting 'web-search=true'.
- **🌐 SearchApi Integration**: Added support for SearchApi as an alternative web search provider, enhancing search capabilities within the platform.
- **🔍 Literal Type Support in Tools**: Tools now support the Literal type.
- **🌍 Updated Translations**: Improved translations for Chinese, Ukrainian, and Catalan.

### Fixed

- **🔧 Pip Install Issue**: Resolved the issue where pip install failed due to missing 'alembic.ini', ensuring smoother installation processes.
- **🌃 Automatic Theme Update**: Fixed an issue where the color theme did not update dynamically with system changes.
- **🛠️ User Agent in ComfyUI**: Added default headers in ComfyUI to fix access issues, improving reliability in network communications.
- **🔄 Missing Chat Completion Response Headers**: Ensured proper return of proxied response headers during chat completion, improving API reliability.
- **🔗 Websocket Connection Prioritization**: Modified socket.io configuration to prefer websockets and more reliably fallback to polling, enhancing connection stability.
- **🎭 Accessibility Enhancements**: Added missing ARIA labels for buttons, improving accessibility for visually impaired users.
- **⚖️ Advanced Parameter**: Fixed an issue ensuring that advanced parameters are correctly applied in all scenarios, ensuring consistent behavior of user-defined settings.

### Changed

- **🔁 Namespace Reorganization**: Reorganized all Python files under the 'open_webui' namespace to streamline the project structure and improve maintainability. Tools and functions importing from 'utils' should now use 'open_webui.utils'.
- **🚧 Dependency Updates**: Updated several backend dependencies like 'aiohttp', 'authlib', 'duckduckgo-search', 'flask-cors', and 'langchain' to their latest versions, enhancing performance and security.

### Added changes for OpenwebUI 0.3.16

- **🚀 Config DB Migration**: Migrated configuration handling from config.json to the database, enabling high-availability setups and load balancing across multiple Open WebUI instances.
- **🔗 Call Mode Activation via URL**: Added a 'call=true' URL search parameter enabling direct shortcuts to activate call mode, enhancing user interaction on mobile devices.
- **✨ TTS Content Control**: Added functionality to control how message content is segmented for Text-to-Speech (TTS) generation requests, allowing for more flexible speech output options.
- **😄 Show Knowledge Search Status**: Enhanced model usage transparency by displaying status when working with knowledge-augmented models, helping users understand the system's state during queries.
- **👆 Click-to-Copy for Codespan**: Enhanced interactive experience in the WebUI by allowing users to click to copy content from code spans directly.
- **🚫 API User Blocking via Model Filter**: Introduced the ability to block API users based on customized model filters, enhancing security and control over API access.
- **🎬 Call Overlay Styling**: Adjusted call overlay styling on large screens to not cover the entire interface, but only the chat control area, for a more unobtrusive interaction experience.

### Fixed

- **🔧 LaTeX Rendering Issue**: Addressed an issue that affected the correct rendering of LaTeX.
- **📁 File Leak Prevention**: Resolved the issue of uploaded files mistakenly being accessible across user chats.
- **🔧 Pipe Functions with '**files**' Param**: Fixed issues with '**files**' parameter not functioning correctly in pipe functions.
- **📝 Markdown Processing for RAG**: Fixed issues with processing Markdown in files.
- **🚫 Duplicate System Prompts**: Fixed bugs causing system prompts to duplicate.

### Changed

- **🔋 Wakelock Permission**: Optimized the activation of wakelock to only engage during call mode, conserving device resources and improving battery performance during idle periods.
- **🔍 Content-Type for Ollama Chats**: Added 'application/x-ndjson' content-type to '/api/chat' endpoint responses to match raw Ollama responses.
- **✋ Disable Signups Conditionally**: Implemented conditional logic to disable sign-ups when 'ENABLE_LOGIN_FORM' is set to false.

### Added changes for OpenwebUI 0.3.15

- **🔗 Temporary Chat Activation**: Integrated a new URL parameter 'temporary-chat=true' to enable temporary chat sessions directly through the URL.
- **🌄 ComfyUI Seed Node Support**: Introduced seed node support in ComfyUI for image generation, allowing users to specify node IDs for randomized seed assignment.

### Fixed

- **🛠️ Tools and Functions**: Resolved a critical issue where Tools and Functions were not properly functioning, restoring full capability and reliability to these essential features.
- **🔘 Chat Action Button in Many Model Chat**: Fixed the malfunctioning of chat action buttons in many model chat environments, ensuring a smoother and more responsive user interaction.
- **⏪ Many Model Chat Compatibility**: Restored backward compatibility for many model chats.

### Added changes for OpenwebUI 0.3.14

- **🛠️ Custom ComfyUI Workflow**: Deprecating several older environment variables, this enhancement introduces a new, customizable workflow for a more tailored user experience.
- **🔀 Merge Responses in Many Model Chat**: Enhances the dialogue by merging responses from multiple models into a single, coherent reply, improving the interaction quality in many model chats.
- **✅ Multiple Instances of Same Model in Chats**: Enhanced many model chat to support adding multiple instances of the same model.
- **🔧 Quick Actions in Model Workspace**: Enhanced Shift key quick actions for hiding/unhiding and deleting models, facilitating a smoother workflow.
- **🗨️ Markdown Rendering in User Messages**: User messages are now rendered in Markdown, enhancing readability and interaction.
- **💬 Temporary Chat Feature**: Introduced a temporary chat feature, deprecating the old chat history setting to enhance user interaction flexibility.
- **🖋️ User Message Editing**: Enhanced the user chat editing feature to allow saving changes without sending, providing more flexibility in message management.
- **🛡️ Security Enhancements**: Various security improvements implemented across the platform to ensure safer user experiences.
- **🌍 Updated Translations**: Enhanced translations for Chinese, Ukrainian, and Bahasa Malaysia, improving localization and user comprehension.

### Fixed

- **📑 Mermaid Rendering Issue**: Addressed issues with Mermaid chart rendering to ensure clean and clear visual data representation.
- **🎭 PWA Icon Maskability**: Fixed the Progressive Web App icon to be maskable, ensuring proper display on various device home screens.
- **🔀 Cloned Model Chat Freezing Issue**: Fixed a bug where cloning many model chats would cause freezing, enhancing stability and responsiveness.
- **🔍 Generic Error Handling and Refinements**: Various minor fixes and refinements to address previously untracked issues, ensuring smoother operations.

### Changed

- **🖼️ Image Generation Refactor**: Overhauled image generation processes for improved efficiency and quality.
- **🔨 Refactor Tool and Function Calling**: Refactored tool and function calling mechanisms for improved clarity and maintainability.
- **🌐 Backend Library Updates**: Updated critical backend libraries including SQLAlchemy, uvicorn[standard], faster-whisper, bcrypt, and boto3 for enhanced performance and security.

### Removed

- **🚫 Deprecated ComfyUI Environment Variables**: Removed several outdated environment variables related to ComfyUI settings, simplifying configuration management.


### Added changes from 0.3.13
- **🎨 Enhanced Markdown Rendering**: Significant improvements in rendering markdown, ensuring smooth and reliable display of LaTeX and Mermaid charts, enhancing user experience with more robust visual content.
- **🔄 Auto-Install Tools & Functions Python Dependencies**: For 'Tools' and 'Functions', Open WebUI now automatically install extra python requirements specified in the frontmatter, streamlining setup processes and customization.
- **🌀 OAuth Email Claim Customization**: Introduced an 'OAUTH_EMAIL_CLAIM' variable to allow customization of the default "email" claim within OAuth configurations, providing greater flexibility in authentication processes.
- **📶 Websocket Reconnection**: Enhanced reliability with the capability to automatically reconnect when a websocket is closed, ensuring consistent and stable communication.
- **🤳 Haptic Feedback on Support Devices**: Android devices now support haptic feedback for an immersive tactile experience during certain interactions.

### Fixed

- **🛠️ ComfyUI Performance Improvement**: Addressed an issue causing FastAPI to stall when ComfyUI image generation was active; now runs in a separate thread to prevent UI unresponsiveness.
- **🔀 Session Handling**: Fixed an issue mandating session_id on client-side to ensure smoother session management and transitions.
- **🖋️ Minor Bug Fixes and Format Corrections**: Various minor fixes including typo corrections, backend formatting improvements, and test amendments enhancing overall system stability and performance.

### Changed

- **🚀 Migration to SvelteKit 2**: Upgraded the underlying framework to SvelteKit version 2, offering enhanced speed, better code structure, and improved deployment capabilities.
- **🧹 General Cleanup and Refactoring**: Performed broad cleanup and refactoring across the platform, improving code efficiency and maintaining high standards of code health.
- **🚧 Integration Testing Improvements**: Modified how Cypress integration tests detect chat messages and updated sharing tests for better reliability and accuracy.
- **📁 Standardized '.safetensors' File Extension**: Renamed the '.sft' file extension to '.safetensors' for ComfyUI workflows, standardizing file formats across the platform.

### Removed

- **🗑️ Deprecated Frontend Functions**: Removed frontend functions that were migrated to backend to declutter the codebase and reduce redundancy.

### Ameritas Changes:
- **Logo Changes:** Updated Logo and Name for Ameritas 
- **Customized Environment Variables:** Added config and environment variable customization
- **Application Internal DB:** Allocated Application DB(PostgreSQL) for user Logs and feedback
- **Azure AD SSO:** Ameritas Azure AD SSO integration allocated
- **Bug Fixes :** OpenWebUI 0.3.12 compilation Bugs fixed for Python v.3.9
- **Ollama Server Connection:** Ollama remote server connection tested

### Added base code model from OpenwebUI 0.3.12 version
- **Changes for base version of OpebWebUI**: Base version allocated for ameritasGPT 
