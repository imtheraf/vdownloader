from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS  # Import Flask-CORS
from yt_dlp import YoutubeDL
import os
import browser_cookie3

app = Flask(__name__)
CORS(app)

# Global variable to store the available formats and video details
available_formats = []
video_details = {}
video_title = ''

import browser_cookie3
from yt_dlp import YoutubeDL

def get_available_formats(video_url):
    global available_formats, video_details
    try:
        # Automatically fetch cookies from your default browser (e.g., Chrome)
        cookies = browser_cookie3.chrome()  # You can use browser_cookie3.firefox() if using Firefox

        # Set up yt-dlp options with the fetched cookies
        ydl_opts = {
            'quiet': True,
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': True,
            'cookiefile': cookies,  # Pass cookies directly
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])

            video_details = {
                'title': info_dict.get('title', 'Unknown Title'),
                'thumbnail': info_dict.get('thumbnail', ''),
            }

            available_formats = []
            for i, f in enumerate(formats):
                format_note = f.get('format_note', 'N/A')
                resolution = f.get('height', 'N/A')
                format_id = f.get('format_id', 'N/A')
                available_formats.append({
                    'index': i + 1,
                    'format_note': format_note,
                    'resolution': resolution,
                    'format_id': format_id,
                    'extension': f.get('ext', 'mp4'),
                })

            return available_formats

    except Exception as e:
        return {"error": f"Failed to fetch formats: {str(e)}"}

def get_download_url(video_url, format_id):
    try:
        # Automatically fetch cookies from the browser
        cookies = browser_cookie3.chrome()  # Use browser_cookie3.firefox() if using Firefox

        ydl_opts = {
            'quiet': True,
            'format': format_id,
            'noplaylist': True,
            'cookiefile': cookies,  # Pass cookies directly
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])
            for f in formats:
                if f.get('format_id') == format_id:
                    return f.get('url')  # Return the direct download URL
            return "Format not found"
    except Exception as e:
        return {"error": f"Failed to fetch download URL: {str(e)}"}

@app.route('/')
def index():
    return '''
    <form action="/get_formats" method="POST">
        YouTube Video URL: <input type="text" name="url" required><br>
        <input type="submit" value="Get Available Formats">
    </form>
    '''

@app.route('/get_formats', methods=['POST'])
def get_formats():
    global video_title

    video_url = request.form['url']
    if not video_url:
        return jsonify({"error": "No video URL provided."}), 400

    # Fetch available formats and video details
    formats = get_available_formats(video_url)

    if isinstance(formats, str):  # Error occurred
        return jsonify({"error": formats}), 400

    video_title = video_details.get("title", "Unknown Title")

    # Include video details in the response
    response = {
        "video_title": video_title,
        "thumbnail_url": video_details.get("thumbnail", ""),
        "formats": formats
    }
    return jsonify(response)


@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['url']
    format_id = request.form['format_id']

    if not video_url or not format_id:
        return jsonify({"error": "Missing video URL or format ID."}), 400

    # Get the direct download URL
    download_url = get_download_url(video_url, format_id)

    if isinstance(download_url, str) and 'error' in download_url.lower():
        return jsonify({"error": download_url}), 400

    # Provide the download URL to the client
    return jsonify({"url"  : download_url, "title" : video_title})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 locally if PORT is not set
    app.run(debug=True, host="0.0.0.0", port=port)
