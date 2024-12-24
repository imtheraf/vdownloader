from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS  # Import Flask-CORS
from yt_dlp import YoutubeDL
import os

app = Flask(__name__)
CORS(app)

# Global variable to store the available formats and video details
available_formats = []
video_details = {}
video_title = ''

def get_available_formats(video_url):
    """Fetch available formats, video name, and thumbnail for the provided YouTube video URL."""
    global available_formats, video_details
    try:
        ydl_opts = {
            'quiet': True,  # Suppress unnecessary output
            'format': 'bestvideo+bestaudio/best',
            'noplaylist': True,  # Avoid downloading playlists
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])
            
            # Extract video details
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
        return str(e)

def get_download_url(video_url, format_id):
    """Fetch the direct download URL for a specific format."""
    try:
        ydl_opts = {
            'quiet': True,  # Suppress unnecessary output
            'format': format_id,
            'noplaylist': True,  # Avoid downloading playlists
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            formats = info_dict.get('formats', [])
            for f in formats:
                if f.get('format_id') == format_id:
                    return f.get('url')  # Return the direct download URL
            return "Format not found"
    except Exception as e:
        return str(e)

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
    app.run(debug=True, port=5000)
