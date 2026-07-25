# Streamlit Deployment Guide — Zepto Reviews AI

This guide explains how to deploy **Zepto Reviews AI** onto **Streamlit Community Cloud** (free 1-click cloud deployment) or run it locally using Docker.

---

## Option 1: Streamlit Community Cloud (Free Public Hosting)

### Step 1: Push Code to GitHub
1. Initialize git and commit your workspace:
   ```bash
   git init
   git add .
   git commit -m "Zepto Reviews AI — Streamlit Customer Behavioral Discovery Engine"
   ```
2. Push your repository to GitHub:
   ```bash
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/Zepto-Reviews-AI.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New App"**.
3. Select your repository: `Zepto-Reviews-AI`.
4. Main file path: `app.py`.
5. Click **"Advanced Settings"** -> **"Secrets"** and add your environment variable:
   ```toml
   GEMINI_API_KEY = "your-google-ai-studio-key"
   ```
6. Click **"Deploy!"**
   * Your app will be live at `https://zepto-reviews-ai.streamlit.app` in $< 2$ minutes!

---

## Option 2: Local Streamlit Execution

Run the Streamlit server directly on your machine:
```bash
pip install -r requirements.txt
streamlit run app.py
```
* Access the app locally at: **`http://localhost:8501`**

---

## Option 3: Docker Deployment

Build and run using Docker:
```bash
docker build -t zepto-reviews-streamlit .
docker run -p 8501:8501 zepto-reviews-streamlit
```
