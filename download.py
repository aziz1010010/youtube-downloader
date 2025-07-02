#!/usr/bin/env python3
"""
Complete YouTube Downloader - Single Page Web Application
Combines Flask backend with HTML/CSS/JavaScript frontend in one file

Requirements:
pip install flask yt-dlp

Usage:
python app.py

Then open: http://localhost:5000
"""

import os
import sys
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_file, url_for
import yt_dlp

# Initialize Flask app
app = Flask(__name__)

# Global variables and configurations
download_progress = {}

def get_downloads_folder():
    """Get the system's Downloads folder path"""
    if sys.platform == "win32":
        import winreg
        sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return str(Path.home() / "Downloads")

# Get the default downloads path
DEFAULT_DOWNLOADS_PATH = get_downloads_folder()

# Ensure required directories exist
if not os.path.exists('./static'):
    os.makedirs('./static')
if not os.path.exists('./downloads'):
    os.makedirs('./downloads')

class ProgressHook:
    def __init__(self, download_id):
        self.download_id = download_id
        
    def __call__(self, d):
        global download_progress
        if d['status'] == 'downloading':
            download_progress[self.download_id] = {
                'status': 'downloading',
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes': d.get('total_bytes', 0),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'percent': d.get('_percent_str', '0%')
            }
        elif d['status'] == 'finished':
            download_progress[self.download_id] = {
                'status': 'finished',
                'filename': d['filename']
            }

def get_video_info(url):
    """Get video information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return {'success': False, 'error': 'Could not fetch video information'}
                
            return {
                'success': True,
                'data': {
                    'title': info.get('title', 'N/A'),
                    'duration': str(info.get('duration', 'N/A')) + ' seconds' if info.get('duration') else 'N/A',
                    'uploader': info.get('uploader', 'N/A'),
                    'view_count': f"{info.get('view_count', 0):,}" if info.get('view_count') else 'N/A',
                    'upload_date': info.get('upload_date', 'N/A'),
                    'description': info.get('description', 'N/A')[:200] + '...' if info.get('description') else 'N/A'
                }
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def download_video_async(url, download_type, quality, output_path, download_id):
    """Download video asynchronously"""
    global download_progress
    
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # Common options to speed up downloads
        common_opts = {
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'progress_hooks': [ProgressHook(download_id)],
            'concurrent_fragments': 3,  # Download multiple fragments at once
            'file_access_retries': 3,   # Retry on file access errors
            'retries': 3,               # Retry on download errors
            'fragment_retries': 3,      # Retry on fragment download errors
            'skip_download': False,
            'quiet': True,              # Reduce console output
            'no_warnings': True,
        }
        
        # Configure options based on download type
        if download_type == 'audio':
            # Map quality string to yt-dlp preferredquality
            preferred_quality_map = {
                '320kbps': '320',
                '192kbps': '192',
                '128kbps': '128'
            }
            preferred_quality = preferred_quality_map.get(quality, '192')

            ydl_opts = {
                **common_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': preferred_quality,
                }],
            }
        else:
            # Video download with optimized format selection
            format_map = {
                '1080p': 'bv*[height<=1080]+ba/b[height<=1080] / bv*+ba/b',
                '720p': 'bv*[height<=720]+ba/b[height<=720] / bv*+ba/b',
                '480p': 'bv*[height<=480]+ba/b[height<=480] / bv*+ba/b',
                '360p': 'bv*[height<=360]+ba/b[height<=360] / bv*+ba/b'
            }
            
            ydl_opts = {
                **common_opts,
                'format': format_map.get(quality, 'bv*[height<=720]+ba/b[height<=720]'),
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        download_progress[download_id]['status'] = 'completed'
        
    except Exception as e:
        download_progress[download_id] = {
            'status': 'error',
            'error': str(e)
        }

# HTML Template with embedded CSS and JavaScript
# IMPORTANT: The url_for('static', filename='favicon.png') part will be rendered by Flask
# before the HTML is sent to the browser.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader - Complete App</title>
    <link rel="icon" type="image/png" href="{{ url_for('static', filename='favicon.png') }}">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }

        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }

        .form-section {
            margin-bottom: 30px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }

        input[type="text"], select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }

        .radio-group {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }

        .radio-option {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        input[type="radio"] {
            width: 18px;
            height: 18px;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            margin-right: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.6;
            transform: none;
            cursor: not-allowed;
        }

        .btn-full {
            width: 100%;
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #555;
            border: 1px solid #ccc;
        }

        .btn-secondary:hover {
            background: #e0e0e0;
        }

        .video-info {
            display: none !important;
            visibility: hidden;
            height: 0;
            overflow: hidden;
        }

        .info-item {
            margin-bottom: 15px;
            padding: 10px;
            background: white;
            border-radius: 8px;
        }

        .info-label {
            font-weight: 600;
            color: #555;
            margin-bottom: 5px;
        }

        .info-value {
            color: #333;
        }

        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }

        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .progress-section {
            display: none;
            margin-top: 20px;
            transition: all 0.3s ease;
            opacity: 0;
        }
        
        .progress-section.visible {
            display: block;
            opacity: 1;
        }

        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e1e1e1;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            border-radius: 10px;
            transition: width 0.3s;
        }

        .progress-text {
            text-align: center;
            color: #555;
        }

        .downloads-section {
            margin-top: 30px;
            border-top: 2px solid #e1e1e1;
            padding-top: 20px;
        }

        .download-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .download-info {
            flex-grow: 1;
        }

        .download-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-completed {
            background: #d4edda;
            color: #155724;
        }

        .status-downloading {
            background: #d1ecf1;
            color: #0c5460;
        }

        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 YouTube Downloader</h1>
        
        <div class="form-section">
            <div class="form-group">
                <label for="videoUrl">YouTube Video URL:</label>
                <input type="text" id="videoUrl" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>

            <div class="form-group">
                <label>Download Type:</label>
                <div class="radio-group">
                    <div class="radio-option">
                        <input type="radio" id="video" name="downloadType" value="video" checked>
                        <label for="video">Video (MP4)</label>
                    </div>
                    <div class="radio-option">
                        <input type="radio" id="audio" name="downloadType" value="audio">
                        <label for="audio">Audio Only (MP3)</label>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label for="quality">Quality:</label>
                <select id="quality">
                    <option value="1080p">1080p</option>
                    <option value="720p">720p</option>
                    <option value="480p">480p</option>
                    <option value="360p">360p</option>
                </select>
            </div>

            <button onclick="getVideoInfo()" class="btn btn-full" id="infoBtn">Download</button>
        </div>

        <div id="videoTitle" style="display:none;position:absolute;visibility:hidden;"></div>

        <div id="progressSection" class="progress-section">
            <h3>📊 Download Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-text" id="progressText">Preparing download...</div>
            <button onclick="startNewDownload()" class="btn btn-full btn-secondary" id="newDownloadBtn" style="margin-top: 20px; display: none;">
                ⬇️ Download Another Video
            </button>
        </div>

        <div id="status" class="status"></div>

        <div class="downloads-section">
            <h3>📁 Recent Downloads</h3>
            <div id="downloadsList">
                <p style="color: #888; text-align: center; padding: 20px;">No downloads yet</p>
            </div>
        </div>
    </div>

    <script>
        let currentDownloadId = null;
        let progressInterval = null;

        // Define options for video and audio
        const videoQualityOptions = [
            { value: '1080p', text: '1080p' },
            { value: '720p', text: '720p' },
            { value: '480p', text: '480p' },
            { value: '360p', text: '360p' }
        ];

        const audioQualityOptions = [
            { value: '320kbps', text: '320 kbps' },
            { value: '192kbps', text: '192 kbps' },
            { value: '128kbps', text: '128 kbps' }
        ];

        function updateQualityOptions() {
            const downloadType = document.querySelector('input[name="downloadType"]:checked').value;
            const qualitySelect = document.getElementById('quality');
            
            // Clear existing options
            qualitySelect.innerHTML = '';

            let optionsToUse = [];
            if (downloadType === 'video') {
                optionsToUse = videoQualityOptions;
            } else { // audio
                optionsToUse = audioQualityOptions;
            }

            // Add new options
            optionsToUse.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                qualitySelect.appendChild(opt);
            });
        }

        // Add event listeners to the radio buttons
        document.querySelectorAll('input[name="downloadType"]').forEach(radio => {
            radio.addEventListener('change', updateQualityOptions);
        });

        // Initialize quality options on page load
        document.addEventListener('DOMContentLoaded', updateQualityOptions);


        async function getVideoInfo() {
            const url = document.getElementById('videoUrl').value;
            const infoBtn = document.getElementById('infoBtn');
            
            if (!url) {
                showStatus('Please enter a YouTube URL', 'error');
                return;
            }

            if (!isValidYouTubeUrl(url)) {
                showStatus('Please enter a valid YouTube URL', 'error');
                return;
            }

            // Show progress immediately
            showProgressSection();
            document.getElementById('newDownloadBtn').style.display = 'none';
            document.getElementById('status').style.display = 'none';
            
            infoBtn.disabled = true;
            infoBtn.textContent = 'Starting...';
            
            // Start both info fetch and download in parallel
            try {
                const response = await fetch('/api/info', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });

                const result = await response.json();

                if (result.success) {
                    document.getElementById('videoTitle').textContent = result.data.title;
                    startDownload();
                } else {
                    hideProgressSection();
                    showStatus(`Error: ${result.error}`, 'error');
                    infoBtn.disabled = false;
                    infoBtn.textContent = 'Download';
                }
            } catch (error) {
                hideProgressSection();
                showStatus(`Network error: ${error.message}`, 'error');
                infoBtn.disabled = false;
                infoBtn.textContent = 'Download';
            }
        }

        function hideProgressSection() {
            const progressSection = document.getElementById('progressSection');
            progressSection.classList.remove('visible');
            setTimeout(() => progressSection.style.display = 'none', 300);
        }

        function showProgressSection() {
            const progressSection = document.getElementById('progressSection');
            progressSection.style.display = 'block';
            // Small delay to trigger the transition
            setTimeout(() => progressSection.classList.add('visible'), 10);
        }

        async function startDownload() {
            const url = document.getElementById('videoUrl').value;
            const downloadType = document.querySelector('input[name="downloadType"]:checked').value;
            const quality = document.getElementById('quality').value;
            const outputPath = "{{ default_downloads_path }}";  // Use the default downloads path directly
            const infoBtn = document.getElementById('infoBtn');
            
            // Progress is already shown by getVideoInfo
            document.getElementById('progressText').textContent = 'Starting download...';

            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        url: url,
                        download_type: downloadType,
                        quality: quality,
                        output_path: outputPath
                    })
                });

                const result = await response.json();

                if (result.success) {
                    currentDownloadId = result.download_id;
                    startProgressMonitoring();
                    addDownloadToList(url, downloadType, quality);
                } else {
                    showStatus(`Error: ${result.error}`, 'error');
                    downloadBtn.disabled = false;
                    downloadBtn.textContent = '🚀 Start Download';
                    document.getElementById('newDownloadBtn').style.display = 'block'; // Show button on error
                }
            } catch (error) {
                showStatus(`Network error: ${error.message}`, 'error');
                downloadBtn.disabled = false;
                downloadBtn.textContent = '🚀 Start Download';
                document.getElementById('newDownloadBtn').style.display = 'block'; // Show button on network error
            }
        }

        function startProgressMonitoring() {
            progressInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/progress/${currentDownloadId}`);
                    const progress = await response.json();

                    updateProgress(progress);

                    if (progress.status === 'completed' || progress.status === 'error') {
                        clearInterval(progressInterval);
                        
                        const infoBtn = document.getElementById('infoBtn');
                        infoBtn.disabled = false;
                        infoBtn.textContent = 'Download';
                        document.getElementById('newDownloadBtn').style.display = 'block'; // Show "Download Another" button

                        if (progress.status === 'completed') {
                            showStatus('Download completed successfully!', 'success');
                        } else {
                            showStatus(`Download failed: ${progress.error}`, 'error');
                        }
                    }
                } catch (error) {
                    console.error('Progress monitoring error:', error);
                    clearInterval(progressInterval);
                    showStatus(`Progress monitoring stopped due to error: ${error.message}`, 'error');
                    const infoBtn = document.getElementById('infoBtn');
                    infoBtn.disabled = false;
                    infoBtn.textContent = 'Download';
                    document.getElementById('newDownloadBtn').style.display = 'block'; // Show button on monitoring error
                }
            }, 1000);
        }

        function updateProgress(progress) {
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            const downloadStatusElement = document.getElementById(`status-${currentDownloadId}`);

            if (progress.status === 'downloading') {
                const percent = progress.percent || '0%';
                progressFill.style.width = percent;
                
                const speed = progress.speed ? formatBytes(progress.speed) + '/s' : 'Unknown';
                const eta = progress.eta ? `${progress.eta}s remaining` : '';
                
                progressText.textContent = `${percent} - Speed: ${speed} ${eta}`;
                if (downloadStatusElement) {
                    downloadStatusElement.textContent = 'Downloading';
                    downloadStatusElement.className = 'download-status status-downloading';
                }
            } else if (progress.status === 'completed') {
                progressFill.style.width = '100%';
                progressText.textContent = 'Download completed!';
                if (downloadStatusElement) {
                    downloadStatusElement.textContent = 'Completed';
                    downloadStatusElement.className = 'download-status status-completed';
                }
            } else if (progress.status === 'error') {
                progressText.textContent = `Error: ${progress.error}`;
                 if (downloadStatusElement) {
                    downloadStatusElement.textContent = 'Error';
                    downloadStatusElement.className = 'download-status status-error';
                }
            }
        }

        function displayVideoInfo(data) {
            document.getElementById('videoTitle').textContent = data.title;
            // Keep video info hidden
            document.getElementById('videoInfo').style.display = 'none';
        }

        function addDownloadToList(url, type, quality) {
            const downloadsList = document.getElementById('downloadsList');
            
            if (downloadsList.children.length === 1 && downloadsList.children[0].tagName === 'P') {
                downloadsList.innerHTML = '';
            }

            const downloadItem = document.createElement('div');
            downloadItem.className = 'download-item';
            downloadItem.innerHTML = `
                <div class="download-info">
                    <div><strong>${document.getElementById('videoTitle').textContent}</strong></div>
                    <div style="font-size: 12px; color: #666;">${type} - ${quality} - ${new Date().toLocaleTimeString()}</div>
                </div>
                <div class="download-status status-downloading" id="status-${currentDownloadId}">Downloading</div>
            `;
            
            downloadsList.insertBefore(downloadItem, downloadsList.firstChild);
        }

        function isValidYouTubeUrl(url) {
            const regex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)[a-zA-Z0-9_-]{11}/;
            return regex.test(url);
        }

        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
            
            // Keep success/error messages visible longer, or until a new action
            if (type === 'success' || type === 'error') {
                // No timeout for these, they stay until user initiates new action
            } else {
                setTimeout(() => {
                    status.style.display = 'none';
                }, 5000);
            }
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        // NEW FUNCTION: Reset UI for a new download
        function startNewDownload() {
            // Clear input field and focus it
            document.getElementById('videoUrl').value = '';
            document.getElementById('videoUrl').focus();

            // Hide all sections with smooth transition
            hideProgressSection();
            document.getElementById('status').style.display = 'none';
            document.getElementById('newDownloadBtn').style.display = 'none';

            // Reset progress bar to initial state
            document.getElementById('progressFill').style.width = '0%';
            document.getElementById('progressText').textContent = 'Preparing download...';

            // Enable and reset the download button
            document.getElementById('infoBtn').disabled = false;
            document.getElementById('infoBtn').textContent = 'Download';

            // Clear any running progress monitoring
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            currentDownloadId = null;
        }

        // Allow Enter key to trigger info fetch
        document.getElementById('videoUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                getVideoInfo();
            }
        });
    </script>
</body>
</html>
"""

# Flask Routes
@app.route('/')
def index():
    # When rendering the template string, Flask's Jinja2 templating engine
    # will process `url_for` to generate the correct URL for the static file.
    return render_template_string(HTML_TEMPLATE, default_downloads_path=DEFAULT_DOWNLOADS_PATH)

@app.route('/api/info', methods=['POST'])
def api_info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    result = get_video_info(url)
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def api_download():
    """Handle download requests"""
    data = request.get_json()
    url = data.get('url')
    download_type = data.get('download_type', 'video')
    quality = data.get('quality', 'best')
    # Use downloads folder as default
    output_path = './downloads'
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # Generate unique download ID
    download_id = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize progress
    download_progress[download_id] = {'status': 'starting'}
    
    # Start download in background thread
    thread = threading.Thread(
        target=download_video_async,
        args=(url, download_type, quality, output_path, download_id)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'download_id': download_id})

@app.route('/api/progress/<download_id>')
def api_progress(download_id):
    progress = download_progress.get(download_id, {'status': 'unknown'})
    return jsonify(progress)

# Application configuration
def configure_app():
    """Configure the Flask application"""
    # Set production configurations
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    return app

if __name__ == '__main__':
    print("🚀 Starting YouTube Downloader Server...")
    print("📋 Make sure you have installed: pip install flask yt-dlp")
    print("🌐 Open your browser and go to: http://localhost:5000")
    print("⚠️  Remember to respect YouTube's Terms of Service!")
    print(f"📂 Downloads will be saved to: ./downloads")
    print("-" * 50)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)