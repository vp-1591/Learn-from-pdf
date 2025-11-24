# Learn From PDF - AI Study Kit

**Learn From PDF** is an AI-powered study tool built with Streamlit. It converts PDF documents into summaries, flashcards, and quizzes.

> **Note:** This is an MVP (Minimum Viable Product) version currently under development. There is a lot of room for improvement, and I appreciate any feedback or suggestions!

## Features

-   **PDF Text Extraction**: Upload any PDF document, and the app will extract the text for analysis.
-   **AI-Powered Generation**: Uses Google's Gemini Pro model to analyze content.
-   **Smart Summaries**: Get concise key concepts and summary points from your document.
-   **Flashcards**: Automatically generated flashcards with "Reveal Answer" functionality for active recall.
-   **Self-Test Quizzes**: Interactive multiple-choice quizzes with immediate feedback to test your knowledge.
-   **Modern UI**: A clean, responsive interface designed for focus.

## Tech Stack

-   **Python 3.8+**
-   **[Streamlit](https://streamlit.io/)**: For the interactive web interface.
-   **[Google Gemini API](https://ai.google.dev/)**: For advanced natural language processing and content generation.
-   **[PyPDF2](https://pypi.org/project/PyPDF2/)**: For reliable PDF text extraction.

## Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd AI_SAG
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up Environment Variables**
    Create a `.env` file in the root directory and add your Google API Key:
    ```env
    GOOGLE_API_KEY=your_api_key_here
    ```
    *Alternatively, you can enter the API key directly in the app's sidebar.*

## Usage

1.  **Run the application**
    ```bash
    streamlit run app.py
    ```

2.  **Upload a PDF**
    - Click the "Upload PDF" widget to select your file.
    - Click the **Generate** button to start processing.

3.  **Study**
    - Review the **Key Concepts**.
    - Practice with **Flashcards**.
    - Test yourself with the **Self-Test Quiz**.

## Project Structure

-   `app.py`: Main application logic and UI.
-   `requirements.txt`: List of Python dependencies.
-   `.env`: Configuration file for API keys (not committed to version control).
