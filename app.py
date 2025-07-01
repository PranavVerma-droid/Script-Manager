from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, abort
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import os
import subprocess

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'script_manager_secret_key')

SCRIPT_DIR = os.getenv('SCRIPT_DIR', '/data/scripts')
GIT_ENABLED = os.getenv('GIT_ENABLED', 'false').lower() == 'true'

# Custom Jinja2 filter for datetime formatting
@app.template_filter('datetime')
def datetime_filter(timestamp, format='%Y-%m-%d %H:%M'):
    """Convert timestamp to formatted datetime string"""
    return datetime.fromtimestamp(timestamp).strftime(format)

def get_all_files():
    """Get all files from the script directory"""
    try:
        if not os.path.exists(SCRIPT_DIR):
            os.makedirs(SCRIPT_DIR, exist_ok=True)
            return []
        
        files = []
        for item in os.listdir(SCRIPT_DIR):
            item_path = os.path.join(SCRIPT_DIR, item)
            if os.path.isfile(item_path):
                file_info = {
                    'name': item,
                    'path': item_path,
                    'size': os.path.getsize(item_path),
                    'modified': os.path.getmtime(item_path),
                    'is_executable': item.endswith('.sh'),
                    'extension': os.path.splitext(item)[1].lower()
                }
                files.append(file_info)
        
        # Sort files by name
        files.sort(key=lambda x: x['name'].lower())
        return files
    except Exception as e:
        print(f"Error getting files: {e}")
        return []

def read_file_content(file_path):
    """Read content of a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # If UTF-8 fails, try with latin-1
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file_content(file_path, content):
    """Write content to a file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False

def delete_file(file_path):
    """Delete a file"""
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
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

# Git helper functions
def is_git_repo():
    """Check if the script directory is a git repository"""
    try:
        if not os.path.exists(SCRIPT_DIR):
            return False
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def get_git_status():
    """Get git status of files in the repository"""
    try:
        if not is_git_repo():
            return None
        
        # Get status
        result = subprocess.run(['git', 'status', '--porcelain'], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode != 0:
            return None
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                status = line[:2]
                filename = line[3:]
                files.append({
                    'filename': filename,
                    'status': status,
                    'staged': status[0] != ' ' and status[0] != '?',
                    'modified': status[1] != ' ',
                    'untracked': status == '??'
                })
        
        return files
    except Exception as e:
        print(f"Error getting git status: {e}")
        return None

def get_git_branch():
    """Get current git branch"""
    try:
        if not is_git_repo():
            return None
        
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None

def git_add_file(filename):
    """Add a file to git staging area"""
    try:
        result = subprocess.run(['git', 'add', filename], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def git_unstage_file(filename):
    """Remove a file from git staging area"""
    try:
        result = subprocess.run(['git', 'reset', 'HEAD', filename], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def git_discard_changes(filename):
    """Discard changes to a file"""
    try:
        # First, check if file is in working directory
        result = subprocess.run(['git', 'checkout', 'HEAD', '--', filename], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE)
        return result.returncode == 0
    except Exception:
        return False

def git_discard_all_changes():
    """Discard all changes in the working directory"""
    try:
        # Reset all staged changes
        reset_result = subprocess.run(['git', 'reset', 'HEAD'], 
                                     cwd=SCRIPT_DIR, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        
        # Discard all working directory changes
        checkout_result = subprocess.run(['git', 'checkout', 'HEAD', '--', '.'], 
                                        cwd=SCRIPT_DIR, 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.PIPE)
        
        # Clean untracked files
        clean_result = subprocess.run(['git', 'clean', '-fd'], 
                                     cwd=SCRIPT_DIR, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
        
        return reset_result.returncode == 0 and checkout_result.returncode == 0
    except Exception:
        return False

def git_commit(message):
    """Commit staged changes"""
    try:
        if not message.strip():
            return False, "Commit message cannot be empty"
        
        result = subprocess.run(['git', 'commit', '-m', message], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode == 0:
            return True, "Changes committed successfully"
        else:
            return False, result.stderr or "Commit failed"
    except Exception as e:
        return False, str(e)

def git_push():
    """Push changes to remote repository"""
    try:
        result = subprocess.run(['git', 'push'], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode == 0:
            return True, "Changes pushed successfully"
        else:
            return False, result.stderr or "Push failed"
    except Exception as e:
        return False, str(e)

def git_pull():
    """Pull changes from remote repository"""
    try:
        result = subprocess.run(['git', 'pull'], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode == 0:
            return True, result.stdout or "Repository updated"
        else:
            return False, result.stderr or "Pull failed"
    except Exception as e:
        return False, str(e)

def get_commit_history(limit=10):
    """Get recent commit history"""
    try:
        if not is_git_repo():
            return []
        
        result = subprocess.run(['git', 'log', '--oneline', f'-{limit}'], 
                               cwd=SCRIPT_DIR, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode != 0:
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })
        
        return commits
    except Exception:
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scripts')
def scripts():
    """Main scripts management page"""
    files = get_all_files()
    git_enabled = GIT_ENABLED
    git_configured = is_git_repo() if git_enabled else False
    current_branch = get_git_branch() if git_configured else None
    
    return render_template('scripts.html', 
                         files=files, 
                         git_enabled=git_enabled,
                         git_configured=git_configured,
                         current_branch=current_branch)

@app.route('/script/edit/<filename>')
def edit_script(filename):
    """Edit a specific script file"""
    file_path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    content = read_file_content(file_path)
    file_info = {
        'name': filename,
        'path': file_path,
        'size': os.path.getsize(file_path),
        'modified': os.path.getmtime(file_path),
        'is_executable': filename.endswith('.sh'),
        'extension': os.path.splitext(filename)[1].lower()
    }
    return render_template('edit_script.html', file=file_info, content=content)

@app.route('/script/save/<filename>', methods=['POST'])
def save_script(filename):
    """Save changes to a script file"""
    file_path = os.path.join(SCRIPT_DIR, filename)
    content = request.form.get('content', '')
    
    if write_file_content(file_path, content):
        flash(f'File "{filename}" saved successfully', 'success')
    else:
        flash(f'Error saving file "{filename}"', 'danger')
    
    return redirect(url_for('edit_script', filename=filename))

@app.route('/script/run/<filename>')
def run_script(filename):
    """Execute a shell script"""
    if not filename.endswith('.sh'):
        return jsonify({"status": "error", "message": "Only .sh files can be executed"})
    
    file_path = os.path.join(SCRIPT_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "Script not found"})
    
    success, message = execute_script(file_path)
    if success:
        return jsonify({"status": "success", "message": message})
    else:
        return jsonify({"status": "error", "message": message})

@app.route('/script/create', methods=['GET', 'POST'])
def create_script():
    """Create a new script file"""
    if request.method == 'POST':
        filename = request.form.get('filename', '').strip()
        content = request.form.get('content', '')
        
        if not filename:
            flash('Filename is required', 'danger')
            return redirect(url_for('create_script'))
        
        # Validate filename
        if '/' in filename or '\\' in filename or '..' in filename:
            flash('Invalid filename', 'danger')
            return redirect(url_for('create_script'))
        
        file_path = os.path.join(SCRIPT_DIR, filename)
        if os.path.exists(file_path):
            flash('File already exists', 'danger')
            return redirect(url_for('create_script'))
        
        if write_file_content(file_path, content):
            # Make .sh files executable
            if filename.endswith('.sh'):
                os.chmod(file_path, 0o755)
            flash(f'File "{filename}" created successfully', 'success')
            return redirect(url_for('edit_script', filename=filename))
        else:
            flash(f'Error creating file "{filename}"', 'danger')
    
    return render_template('create_script.html')

@app.route('/tmux')
def tmux_manager():
    """Tmux sessions management page"""
    return render_template('tmux.html')

@app.route('/script/delete/<filename>')
def delete_script(filename):
    """Delete a script file"""
    file_path = os.path.join(SCRIPT_DIR, filename)
    if delete_file(file_path):
        return jsonify({"status": "success", "message": f"File {filename} deleted"})
    else:
        return jsonify({"status": "error", "message": f"Failed to delete file {filename}"})

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

# Source Control Routes
@app.route('/git/status')
def git_status():
    """Get git status"""
    if not GIT_ENABLED:
        return jsonify({"error": "Git is not enabled"}), 400
    
    if not is_git_repo():
        return jsonify({"error": "Not a git repository"}), 400
    
    status = get_git_status()
    branch = get_git_branch()
    commits = get_commit_history(5)
    
    return jsonify({
        "status": status or [],
        "branch": branch,
        "commits": commits
    })

@app.route('/git/stage/<filename>', methods=['POST'])
def git_stage_file(filename):
    """Stage a file for commit"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    success = git_add_file(filename)
    if success:
        return jsonify({"message": f"File {filename} staged"})
    else:
        return jsonify({"error": f"Failed to stage file {filename}"}), 500

@app.route('/git/unstage/<filename>', methods=['POST'])
def git_unstage_file_route(filename):
    """Unstage a file"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    success = git_unstage_file(filename)
    if success:
        return jsonify({"message": f"File {filename} unstaged"})
    else:
        return jsonify({"error": f"Failed to unstage file {filename}"}), 500

@app.route('/git/discard/<path:filename>', methods=['POST'])
def git_discard_file_route(filename):
    """Discard changes to a file"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    success = git_discard_changes(filename)
    if success:
        return jsonify({"message": f"Changes to {filename} discarded"})
    else:
        return jsonify({"error": f"Failed to discard changes to {filename}"}), 500

@app.route('/git/discard-all', methods=['POST'])
def git_discard_all_route():
    """Discard all changes"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    success = git_discard_all_changes()
    if success:
        return jsonify({"message": "All changes discarded"})
    else:
        return jsonify({"error": "Failed to discard all changes"}), 500

@app.route('/git/commit', methods=['POST'])
def git_commit_route():
    """Commit staged changes"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    data = request.get_json()
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"error": "Commit message is required"}), 400
    
    success, result_message = git_commit(message)
    if success:
        return jsonify({"message": result_message})
    else:
        return jsonify({"error": result_message}), 500

@app.route('/git/push', methods=['POST'])
def git_push_route():
    """Push changes to remote"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    success, message = git_push()
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 500

@app.route('/git/pull', methods=['POST'])
def git_pull_route():
    """Pull changes from remote"""
    if not GIT_ENABLED or not is_git_repo():
        return jsonify({"error": "Git not available"}), 400
    
    success, message = git_pull()
    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 500

# API Routes for Homepage Widget
@app.route('/api/stats')
def api_stats():
    """API endpoint for homepage widget - returns script statistics"""
    try:
        files = get_all_files()
        
        # Count different file types
        total_scripts = len(files)
        executable_scripts = len([f for f in files if f.get('executable', False)])
        shell_scripts = len([f for f in files if f['name'].endswith('.sh')])
        python_scripts = len([f for f in files if f['name'].endswith('.py')])
        config_files = len([f for f in files if f['name'].endswith(('.conf', '.cfg', '.ini', '.env', '.yaml', '.yml', '.json'))])
        
        # Calculate total size
        total_size = sum(f.get('size', 0) for f in files)
        
        # Get git info if available
        git_info = {}
        if GIT_ENABLED and is_git_repo():
            git_status = get_git_status()
            git_branch = get_git_branch()
            git_info = {
                'enabled': True,
                'branch': git_branch or 'unknown',
                'modified_files': len(git_status) if git_status else 0
            }
        else:
            git_info = {'enabled': False}
        
        # Get most recent file
        recent_file = None
        if files:
            most_recent = max(files, key=lambda x: x.get('modified', 0))
            recent_file = {
                'name': most_recent['name'],
                'modified': most_recent.get('modified', 0)
            }
        
        return jsonify({
            'total_scripts': total_scripts,
            'executable_scripts': executable_scripts,
            'shell_scripts': shell_scripts,
            'python_scripts': python_scripts,
            'config_files': config_files,
            'total_size_bytes': total_size,
            'git': git_info,
            'recent_file': recent_file,
            'status': 'online',
            'last_updated': int(datetime.now().timestamp())
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'last_updated': int(datetime.now().timestamp())
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=True)
