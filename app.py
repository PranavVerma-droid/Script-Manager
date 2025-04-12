from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import os
import re
import subprocess
import time

app = Flask(__name__)
app.secret_key = 'downloader_secret_key'

VIDEOS_ENV_PATH = '/scripts/.videos-env'
SONGS_ENV_PATH = '/scripts/.songs-env'
VIDEOS_SCRIPT_PATH = '/scripts/videos-download.sh'
SONGS_SCRIPT_PATH = '/scripts/songs-download.sh'

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

def execute_script(script_path):
    """Execute a shell script and return the result"""
    try:
        # Check if the script exists and is executable
        if not os.path.isfile(script_path):
            return False, "Script file not found"
        
        if not os.access(script_path, os.X_OK):
            # Try to make it executable
            os.chmod(script_path, 0o755)
        
        # Execute the script
        process = subprocess.Popen([script_path], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            return True, "Script executed successfully"
        else:
            return False, f"Script execution failed: {stderr.decode('utf-8')}"
    except Exception as e:
        return False, f"Error executing script: {str(e)}"

def get_tmux_sessions():
    """Get all running tmux sessions"""
    try:
        result = subprocess.run(['tmux', 'list-sessions'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode != 0:
            return []
        
        sessions = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # Parse session name (everything before the first colon)
                name = line.split(':')[0]
                sessions.append({
                    'name': name,
                    'full_info': line
                })
        return sessions
    except Exception as e:
        print(f"Error getting tmux sessions: {e}")
        return []

def kill_tmux_session(session_name):
    """Kill a specific tmux session"""
    try:
        result = subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception as e:
        print(f"Error killing tmux session: {e}")
        return False

def get_tmux_session_output(session_name, window=0, pane=0):
    """Get the current output from a tmux session"""
    try:
        result = subprocess.run(
            ['tmux', 'capture-pane', '-p', '-t', f'{session_name}:{window}.{pane}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return result.stdout
        return "Error capturing output"
    except Exception as e:
        return f"Error: {str(e)}"

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
        elif 'execute' in request.form:
            success, message = execute_script(VIDEOS_SCRIPT_PATH)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
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
        elif 'execute' in request.form:
            success, message = execute_script(SONGS_SCRIPT_PATH)
            if success:
                flash(message, 'success')
            else:
                flash(message, 'danger')
        return redirect(url_for('songs'))
    
    song_urls = read_array_from_env(SONGS_ENV_PATH, 'declare -a PLAYLISTS')
    return render_template('songs.html', urls=song_urls)

@app.route('/tmux/sessions')
def tmux_sessions():
    """Get all running tmux sessions"""
    sessions = get_tmux_sessions()
    return jsonify(sessions)

@app.route('/tmux/kill/<session_name>')
def tmux_kill_session(session_name):
    """Kill a specific tmux session"""
    success = kill_tmux_session(session_name)
    if success:
        return jsonify({"status": "success", "message": f"Session {session_name} killed"})
    else:
        return jsonify({"status": "error", "message": f"Failed to kill session {session_name}"})

@app.route('/tmux/output/<session_name>')
def tmux_session_output(session_name):
    """Get output from a tmux session"""
    output = get_tmux_session_output(session_name)
    return jsonify({"status": "success", "output": output})

@app.route('/tmux/stream/<session_name>')
def tmux_stream_session(session_name):
    """Stream output from a tmux session"""
    def generate():
        last_output = ""
        while True:
            output = get_tmux_session_output(session_name)
            if output != last_output:
                last_output = output
                # Fix the backslash issue in f-string
                escaped_output = output.replace('\n', '\\n')
                yield f"data: {escaped_output}\n\n"
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
