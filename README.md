# SciRep Genie - Cardiology Research Tool

This web application extracts data from scientific reports for cardiology research.

## Deployment Instructions

This application is designed to be deployed to Netlify for 24/7 free hosting. Follow these steps:

### Prerequisites

1. GitHub account
2. Netlify account (sign up at https://app.netlify.com - free tier is sufficient)

### Deployment Steps

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/scirep-genie.git
   git push -u origin main
   ```

2. **Connect to Netlify**:
   - Go to [Netlify](https://app.netlify.com)
   - Click "New site from Git"
   - Choose GitHub as your provider
   - Select your repository
   - Use these build settings:
     - Build command: `python build_site.py`
     - Publish directory: `_site`
   - Click "Deploy site"

3. **Enable Netlify Functions**:
   - Go to Site Settings > Functions
   - Ensure the functions directory is set to `netlify/functions`

## Local Development

To run this application locally:

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

## How It Works

The application now uses a completely static frontend with serverless Netlify Functions for data processing:

1. Static HTML/CSS/JS for the user interface
2. Client-side JavaScript handles file uploads
3. Files are read in the browser and sent to serverless functions
4. Serverless functions process the data and return CSV files
5. No persistent server is required, making this solution perfect for free hosting

## Technologies Used

- HTML, CSS, JavaScript (Frontend)
- Node.js (Serverless Functions)
- Python (Build Script)
- Netlify (Hosting & Functions)

---

Made with ❤️ by Kian Soroush + GPT