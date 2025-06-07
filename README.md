
# AI Salesman - Overview

## Overview

The **AI Salesman** is a cutting-edge solution designed to automate and optimize customer interactions via phone calls. This system uses advanced AI technologies to deliver human-like conversations, efficiently handle inquiries, and successfully close sales. By providing fast, reliable, and natural interactions, the AI Salesman helps businesses enhance customer engagement and streamline communication.

For further details read -> [dev.to](https://dev.to/devesh0099/building-an-ai-sales-agent-from-voice-to-pitch-3p6c)
## Key Features

✨ **Real-Time Interaction**  
Provides smooth and low-latency conversations for a seamless user experience.

🤖 **Natural Language Processing (NLP)**  
Ensures context-aware and intelligent responses to customer queries.

🎙️ **Speech-to-Text (STT)**  
Accurately transcribes customer audio input into text for further processing.

🔊 **Text-to-Speech (TTS)**  
Generates natural-sounding audio responses to enhance communication.

📈 **Sales Optimization**  
Engages customers strategically to improve conversion rates.

🔗 **API Integration**  
Leverages external APIs for enhanced functionality, such as data retrieval and analytics.

📡 **Scalability**  
Easily customizable for diverse industries and specific use cases.

---

## Limitations

⚠️ **Language Constraints**  
Supports only English.

⚠️ **Memory Constraints**  
Trades memory for longer calls due to being limited to 8k token memory.

⚠️ **Resource Intensive**  
Real-time processing may demand significant computational resources.

⚠️ **Dependency on APIs**  
System performance relies on the availability and reliability of integrated APIs.

---

## Steps to Run

Follow these steps to install and run the AI Salesman:

1. **Clone the Repository**:

   ```bash
   git clone <repository_link>
   ```

   Replace `<repository_link>` with the URL of the repository.

2. **Navigate to the Project Directory**:

   ```bash
   cd AISalesman
   ```

3. **Create a Virtual Environment**:

   ```bash
   python -m venv env
   ```

   Activate the environment using:

   - On Windows: `env\Scripts\activate`
   - On macOS/Linux: `source env/bin/activate`

4. **Set Up Environment Variables**:

   Create a `.env` file in the project directory and add the following:

   ```env
   PINECONE_API=<your_pinecone_api_key>
   HUGGING_FACE_API=<your_hugging_face_api_key>
   SAMBANOVA_API_KEY=<your_sambanova_api_key>
   ```

   Replace `<your_api_key>` with the respective keys.

5. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

6. **Run the Application**:

   ```bash
   uvicorn web.main:app --host 0.0.0.0 --port 10000
   ```

   This command starts the application on port 10000, accessible at `http://0.0.0.0:10000`.

---

## License

📜 This project is licensed under the **GNU GENERAL PUBLIC LICENSE v3.0**.  
See the `LICENSE` file for additional details.
