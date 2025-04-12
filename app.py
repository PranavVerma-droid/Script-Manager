from flask import Flask, render_template, request, redirect, url_for, flash
import os
import re

app = Flask(__name__)
app.secret_key = 'downloader_secret_key'

VIDEOS_ENV_PATH = '/scripts/.videos-env'
SONGS_ENV_PATH = '/scripts/.songs-env'

def read_array_from_env(file_path, array_name):
    """Read array from env file"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            pattern = rf'{array_name}=\(\n(.*?)\n\)'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                lines = match.group(1).strip().split('\n')
                # Remove quotes and other characters
                urls = [line.strip().strip('"') for line in lines if line.strip() and not line.strip().startswith('#')]
                return urls
            return []
    except FileNotFoundError:
        return []

def write_array_to_env(file_path, array_name, urls):
    """Write array to env file"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Prepare the new array content
        new_array_content = f'{array_name}=(\n'
        for url in urls:
            new_array_content += f'"{url}"\n'
        new_array_content += ')'
        
        # Replace the existing array with new content
        pattern = rf'{array_name}=\(\n.*?\n\)'
        new_content = re.sub(pattern, new_array_content, content, flags=re.DOTALL)
        
        with open(file_path, 'w') as file:
            file.write(new_content)
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/videos', methods=['GET', 'POST'])
def videos():
    if request.method == 'POST':
        if 'save' in request.form:
            urls = request.form.get('urls', '').split('\n')
            urls = [url.strip() for url in urls if url.strip()]
            if write_array_to_env(VIDEOS_ENV_PATH, 'declare -a VIDEO_SOURCES', urls):
                flash('Video sources updated successfully', 'success')
            else:
                flash('Error updating video sources', 'danger')
        return redirect(url_for('videos'))
    
    video_urls = read_array_from_env(VIDEOS_ENV_PATH, 'declare -a VIDEO_SOURCES')
    return render_template('videos.html', urls=video_urls)

@app.route('/songs', methods=['GET', 'POST'])
def songs():
    if request.method == 'POST':
        if 'save' in request.form:
            urls = request.form.get('urls', '').split('\n')
            urls = [url.strip() for url in urls if url.strip()]
            if write_array_to_env(SONGS_ENV_PATH, 'declare -a PLAYLISTS', urls):
                flash('Playlist sources updated successfully', 'success')
            else:
                flash('Error updating playlist sources', 'danger')
        return redirect(url_for('songs'))
    
    song_urls = read_array_from_env(SONGS_ENV_PATH, 'declare -a PLAYLISTS')
    return render_template('songs.html', urls=song_urls)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
