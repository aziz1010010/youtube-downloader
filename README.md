# YouTube Downloader Web App

A web-based YouTube video and audio downloader built with Flask and yt-dlp.

## Features

- Download YouTube videos in various qualities (1080p, 720p, 480p, 360p)
- Download audio in different bitrates (320kbps, 192kbps, 128kbps)
- Real-time download progress
- Clean and modern user interface
- Downloads saved to user's Downloads folder

## Deployment Instructions

### Local Development
1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python download.py
   ```
4. Open http://localhost:5000 in your browser

### Deploy on PythonAnywhere

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com)

2. Once logged in:
   - Go to the "Web" tab
   - Click "Add a new web app"
   - Choose "Flask" as your web framework
   - Select Python 3.8 or higher

3. In the "Code" section:
   - Set the source code directory to where you uploaded the files
   - Set the WSGI configuration file to point to your Flask app
   - The WSGI file should contain:
     ```python
     import sys
     path = '/home/YOUR_USERNAME/YOUR_PROJECT_DIRECTORY'
     if path not in sys.path:
         sys.path.append(path)
     
     from download import app as application
     ```

4. Install requirements:
   - Open a PythonAnywhere console
   - Navigate to your project directory
   - Run: `pip install -r requirements.txt`

5. Configure static files:
   - In the "Web" tab, go to "Static Files"
   - Add /static/ to URL and path to your static directory

6. Reload your web app and it should be live!

### Important Notes

- Make sure FFmpeg is installed on your hosting platform
- The downloads folder path will need to be configured for the hosting environment
- Consider adding rate limiting for production use
- Monitor your hosting platform's CPU and bandwidth usage

## License

MIT License - Feel free to use and modify as needed.

## Support

For issues or questions, please open a GitHub issue. 