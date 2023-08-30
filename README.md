# 🎤 Voice-Driven Code Problem Solver

Transform your spoken code problems into Python solutions! This Streamlit application captures real-time audio to transcribe coding problems and leverages the power of OpenAI to generate Python solutions.

## 🌟 Features:
- 🎙️ Real-time audio transcription via AssemblyAI.
- 🔍 Automatic detection of the end of a problem statement.
- 📝 Conversion of transcribed dialogue into summarized topics.
- 🐍 Python code solution generation for recognized problems using OpenAI's GPT-4.

## 📋 Prerequisites:
- `streamlit`
- `websockets`
- `asyncio`
- `base64`
- `json`
- `rapidfuzz`
- `pyaudio`
- `langchain`
- 🔑 Appropriate API keys for AssemblyAI and OpenAI.
- 📦 `poetry` for package management.

## 🚀 Installation:
1. Clone the repository:
   ```
   git clone <repository_url>
   ```

2. 📂 Navigate to the directory:
   ```
   cd voice_driven_code_problem_solver
   ```

3. 📦 Install the required Python packages using `poetry`:
   ```
   poetry install
   ```

4. Activate the poetry environment:
   ```
   poetry shell
   ```

## 🖥️ Usage:
1. Start the application by running:
   ```
   streamlit run <filename>.py
   ```

2. 🌐 Access the app in your browser using the link provided in the terminal.

3. 🟢 Click on "Start listening" to begin recording your problem statement.

4. 🗣️ Speak your coding problem clearly into your microphone.

5. 🔴 Click on "Stop listening" when done.

6. ⏳ Wait for the app to display the transcribed problem and its Python solution.

## 📌 Notes:
- 🔐 Ensure you've set up the required API keys in `configure.py`.
- 🎧 This application assumes a decent-quality microphone for optimal transcription accuracy.

## 🤝 Contributing:
Contributions to improve the functionality and efficiency of the app are always welcome. Please fork the repository, make your changes, and submit a pull request.

