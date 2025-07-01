# Script Manager

A web-based script management application built with Flask that allows you to manage, edit, create, and execute scripts from a centralized directory. Perfect for managing shell scripts, configuration files, and other text-based files on your server.

I have personally made this to manage all my [Server Scripts for Server 1](https://github.com/PranavVerma-droid/Scripts-S1).

## Features

### 📁 File Management
- **View all files** from a configured directory
- **Create new files** with built-in templates (Bash, Python, Config files)
- **Edit files** with a web-based editor
- **Delete files** with confirmation dialogs
- **Hide/unhide files** to organize your workspace

### 🚀 Script Execution
- **Run shell scripts** (`.sh` files) directly from the web interface
- **Real-time feedback** on script execution status
- **Error handling** with detailed error messages

### 🖥️ Tmux Integration
- **View running tmux sessions**
- **Stream live output** from tmux sessions
- **Kill tmux sessions** remotely
- **Auto-refresh** session list

### � Git Version Control
- **Source control sidebar** (like VS Code) for managing Git repositories
- **Stage/unstage files** with visual status indicators
- **Commit changes** with custom commit messages
- **Push/pull** changes to/from remote repositories
- **Discard changes** for individual files or all changes
- **View git branch** and modified files count
- **Auto-detection** of Git repositories in script directory

### �📱 Mobile-Friendly
- **Responsive design** that works on desktop and mobile
- **Touch-friendly** buttons and interface
- **Optimized layouts** for different screen sizes

## Installation

### Prerequisites
- Python 3.7+
- Flask
- tmux (optional, for session management)

### Setup

1. **Clone or download the project** to your server:
   ```bash
   cd /var/www
   git clone https://github.com/PranavVerma-droid/script-manager
   # or create the directory and copy files
   ```

2. **Install Python dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env to configure your settings
   ```

4. **Set up your script directory**:
   ```bash
   mkdir -p /data/scripts
   chmod 755 /data/scripts
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Secret key for Flask sessions
SECRET_KEY=your-secret-key-here

# Directory where scripts are stored
SCRIPT_DIR=/data/scripts

# Enable/disable Git version control features
GIT_ENABLED=true
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `script_manager_secret_key` | Flask secret key for sessions |
| `SCRIPT_DIR` | `/data/scripts` | Directory containing your scripts |
| `GIT_ENABLED` | `false` | Enable Git version control features |

## Usage

### Running the Application

#### Development Mode
```bash
python3 app.py
```
The application will be available at `http://localhost:4000`

#### Production Mode
Use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:4000 app:app
```

#### System Service (Recommended for Production)

For production deployments, you can run the application as a systemd service:

1. **Copy the service file**:
   ```bash
   sudo cp script-manager.service /etc/systemd/system/
   ```

2. **Update the service file** if needed (edit paths, user, etc.):
   ```bash
   sudo nano /etc/systemd/system/script-manager.service
   ```

3. **Enable and start the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable script-manager.service
   sudo systemctl start script-manager.service
   ```

4. **Check service status**:
   ```bash
   sudo systemctl status script-manager.service
   ```

5. **View logs**:
   ```bash
   sudo journalctl -u script-manager.service -f
   ```

The service will automatically:
- Start on boot
- Restart if it crashes
- Run in production mode
- Log to systemd journal

### Using the Interface

#### 1. Managing Scripts
- **View Scripts**: Navigate to `/scripts` to see all files in your script directory
- **Create New File**: Click "New File" and choose from templates or start blank
- **Edit Files**: Click the pencil icon next to any file to edit it
- **Run Scripts**: Click the play button next to `.sh` files to execute them
- **Delete Files**: Click the trash icon and confirm deletion

#### 2. Hide/Unhide Files
- **Hide Files**: Click the eye-slash icon next to any file to hide it from the list
- **Show Hidden Files**: Click "Show Hidden (X)" in the header to reveal hidden files
- **Unhide Files**: When hidden files are visible, click the eye icon to unhide them
- Hidden files are remembered across browser sessions

#### 3. Tmux Session Management
- **View Sessions**: Click "Tmux Sessions" to see all running tmux sessions
- **Monitor Output**: Click on any session to view its live output
- **Kill Sessions**: Use the X button to terminate sessions
- Sessions auto-refresh every 30 seconds

#### 4. Git Version Control (When Enabled)
- **Source Control Sidebar**: Always visible on desktop, toggle on mobile
- **Stage Changes**: Click the `+` button next to modified files to stage them
- **Unstage Changes**: Click the `-` button next to staged files to unstage them
- **Discard Changes**: Click the `×` button to discard individual file changes
- **Commit**: Enter a commit message and click "Commit" to save staged changes
- **Push/Pull**: Use the Push/Pull buttons to sync with remote repository
- **Discard All**: Reset all changes to the last commit state
- **Auto-refresh**: Git status updates automatically when files change

## File Templates

The application includes built-in templates for quick file creation:

### Bash Script Template
```bash
#!/bin/bash
# Includes error handling, logging, and best practices
```

### Python Script Template
```python
#!/usr/bin/env python3
# Includes logging setup and error handling
```

### Configuration File Template
```ini
# Common configuration file structure
# With sections for database, app settings, etc.
```

## Security Considerations

- **File Access**: Only files within the configured `SCRIPT_DIR` can be accessed
- **Filename Validation**: Prevents directory traversal attacks
- **Script Execution**: Only `.sh` files can be executed
- **CSRF Protection**: Flask's built-in CSRF protection is enabled

## Keyboard Shortcuts

- **Ctrl+S / Cmd+S**: Save file in editor
- **Auto-save warning**: Warns about unsaved changes when leaving the page

## API Endpoints

The application provides REST API endpoints:

### File Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scripts` | GET | View all scripts |
| `/script/create` | GET/POST | Create new script |
| `/script/edit/<filename>` | GET | Edit script |
| `/script/save/<filename>` | POST | Save script |
| `/script/run/<filename>` | GET | Execute script |
| `/script/delete/<filename>` | GET | Delete script |

### Tmux Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tmux/sessions` | GET | List tmux sessions |
| `/tmux/kill/<session>` | GET | Kill tmux session |
| `/tmux/output/<session>` | GET | Get session output |
| `/tmux/stream/<session>` | GET | Stream session output |

### Git Version Control
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/git/status` | GET | Get git repository status |
| `/git/stage/<filename>` | POST | Stage a file for commit |
| `/git/unstage/<filename>` | POST | Unstage a file |
| `/git/discard/<path:filename>` | POST | Discard changes to a file |
| `/git/discard-all` | POST | Discard all changes |
| `/git/commit` | POST | Commit staged changes |
| `/git/push` | POST | Push changes to remote |
| `/git/pull` | POST | Pull changes from remote |

### Statistics API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Get script statistics (for homepage widgets) |

#### Stats API Response
The `/api/stats` endpoint returns JSON data suitable for homepage dashboard widgets:

```json
{
    "total_scripts": 25,
    "executable_scripts": 18,
    "shell_scripts": 15,
    "python_scripts": 8,
    "config_files": 2,
    "total_size_bytes": 45678,
    "git": {
        "enabled": true,
        "branch": "main",
        "modified_files": 3
    },
    "recent_file": {
        "name": "backup-script.sh",
        "modified": 1703894400
    },
    "status": "online",
    "last_updated": 1703894400
}

## File Structure

```
script-manager/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── README.md            # This file
└── templates/
    ├── index.html       # Home page
    ├── scripts.html     # Script management page
    ├── edit_script.html # Script editor
    ├── create_script.html # New script creator
    └── tmux.html       # Tmux session manager
```

## Troubleshooting

### Common Issues

1. **"No scripts found"**: Check that `SCRIPT_DIR` exists and contains files
2. **"Permission denied" when running scripts**: Ensure `.sh` files have execute permissions
3. **Tmux sessions not showing**: Verify tmux is installed and sessions are running
4. **Files not saving**: Check write permissions on the script directory

### Debug Mode

Enable debug mode by setting `debug=True` in `app.py` for detailed error messages.

### Logs

Check the console output where you're running the Flask application for error messages and request logs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Feel free to modify and distribute according to your needs.

---

**Note**: This application is designed for trusted environments. Always review scripts before execution and ensure proper access controls are in place.