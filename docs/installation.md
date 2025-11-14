# Installation Guide

This guide covers installing and setting up Rev Exporter on your system.

## Prerequisites

- **Python 3.8 or higher** - Check your version with `python --version` or `python3 --version`
- **Rev.com API credentials** - You'll need:
  - Client API Key
  - User API Key
  
  These can be obtained from your Rev.com account settings under API access.

## Installation Methods

### Method 1: From Source (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/actuallyrizzn/rev.com-export.git
   cd rev.com-export
   ```

2. **Create a virtual environment:**
   
   On Windows:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
   
   On Linux/Mac:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package:**
   ```bash
   pip install -e .
   ```

5. **Verify installation:**
   ```bash
   rev-exporter --help
   ```

### Method 2: Using pip (if published to PyPI)

```bash
pip install rev-exporter
```

## Configuration

Rev Exporter supports multiple methods for providing API credentials, in order of priority:

### 1. Environment Variables (Recommended)

Environment variables are the most secure method and take precedence over other methods.

**Windows (PowerShell):**
```powershell
$env:REV_CLIENT_API_KEY="your_client_api_key"
$env:REV_USER_API_KEY="your_user_api_key"
```

**Windows (Command Prompt):**
```cmd
set REV_CLIENT_API_KEY=your_client_api_key
set REV_USER_API_KEY=your_user_api_key
```

**Linux/Mac:**
```bash
export REV_CLIENT_API_KEY="your_client_api_key"
export REV_USER_API_KEY="your_user_api_key"
```

**Making environment variables persistent:**

- **Windows**: Add them through System Properties → Environment Variables, or use `setx` command
- **Linux/Mac**: Add to `~/.bashrc`, `~/.zshrc`, or `~/.profile`:
  ```bash
  export REV_CLIENT_API_KEY="your_client_api_key"
  export REV_USER_API_KEY="your_user_api_key"
  ```

### 2. Config File

Create a JSON configuration file in one of these locations (checked in order):

1. Current directory: `./config.json`
2. User home directory: `~/.rev-exporter/config.json`

**Example `config.json`:**
```json
{
  "client_api_key": "your_client_api_key",
  "user_api_key": "your_user_api_key"
}
```

**Note:** Make sure to set appropriate file permissions to protect your API keys:
```bash
chmod 600 config.json  # Linux/Mac
```

### 3. Single API Key Format

If you have a single API key that works for both client and user authentication, you can use:

**Environment variable:**
```bash
export REV_API_KEY="your_api_key"
```

**Config file:**
```json
{
  "api_key": "your_api_key"
}
```

**Combined format (CLIENT:USER):**
```bash
export REV_API_KEY="client_key:user_key"
```

## Verifying Configuration

After setting up your credentials, test the connection:

```bash
rev-exporter test-connection
```

You should see:
```
[OK] Connection test successful!
```

If you see an error, check:
- API keys are correct
- Environment variables are set (if using that method)
- Config file exists and is valid JSON (if using that method)
- You have internet connectivity
- Rev.com API is accessible

## Troubleshooting Installation

### Python Version Issues

If you get a "Python version not supported" error:
- Ensure you have Python 3.8 or higher
- On some systems, use `python3` instead of `python`
- Consider using `pyenv` to manage multiple Python versions

### Virtual Environment Issues

**Activation not working:**
- Windows: Use `venv\Scripts\activate.bat` in Command Prompt or `venv\Scripts\Activate.ps1` in PowerShell
- Linux/Mac: Ensure the script is executable: `chmod +x venv/bin/activate`

**Package installation fails:**
- Upgrade pip: `python -m pip install --upgrade pip`
- On some systems, you may need `pip3` instead of `pip`

### Permission Errors

If you encounter permission errors:
- Use a virtual environment (recommended)
- On Linux/Mac, avoid using `sudo` with pip in virtual environments
- Check file permissions on config files

### Network Issues

If installation fails due to network issues:
- Check your internet connection
- Some corporate networks block PyPI; consider using a proxy or VPN
- Try using `--trusted-host` flag with pip if SSL verification fails

## Next Steps

Once installation is complete, proceed to the [User Guide](user-guide.md) to learn how to use Rev Exporter.

