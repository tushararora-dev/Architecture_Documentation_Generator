import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
import logging

def validate_github_url(url: str) -> bool:
    """Validate if the provided URL is a valid GitHub repository URL."""
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        if parsed.netloc != 'github.com':
            return False
        
        # Check if path matches GitHub repo pattern
        path_parts = parsed.path.strip('/').split('/')
        if len(path_parts) != 2:
            return False
        
        # Check for valid owner and repo names
        owner, repo = path_parts
        if not owner or not repo:
            return False
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        # Basic validation for GitHub username/repo naming rules
        pattern = r'^[a-zA-Z0-9\-_.]+$'
        if not re.match(pattern, owner) or not re.match(pattern, repo):
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"Error validating GitHub URL: {e}")
        return False

def extract_repo_info(url: str) -> Optional[Dict[str, str]]:
    """Extract owner and repository name from GitHub URL."""
    if not validate_github_url(url):
        return None
    
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        owner, repo = path_parts
        
        # Remove .git suffix if present
        if repo.endswith('.git'):
            repo = repo[:-4]
        
        return {
            'owner': owner,
            'repo': repo,
            'full_name': f"{owner}/{repo}"
        }
        
    except Exception as e:
        logging.error(f"Error extracting repo info: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes = int(size_bytes / 1024.0)
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename

def parse_mermaid_diagram(text: str) -> Optional[str]:
    """Extract Mermaid diagram code from text."""
    try:
        # Look for mermaid code blocks
        patterns = [
            r'```mermaid\s*\n(.*?)\n```',
            r'```\s*\n(graph\s+.*?)\n```',
            r'```\s*\n(flowchart\s+.*?)\n```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
        
    except Exception as e:
        logging.error(f"Error parsing Mermaid diagram: {e}")
        return None

def create_modules_table(modules_text: str) -> List[Dict[str, str]]:
    """Parse modules text and create structured table data."""
    try:
        modules = []
        
        # Try to parse structured module information
        lines = modules_text.split('\n')
        current_module = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for module headers or bullet points
            if line.startswith('- ') or line.startswith('* '):
                if current_module:
                    modules.append(current_module)
                    current_module = {}
                
                # Extract module name
                module_name = line[2:].split(':')[0].strip()
                current_module['name'] = module_name
                
                # Extract purpose if available
                if ':' in line:
                    purpose = ':'.join(line.split(':')[1:]).strip()
                    current_module['purpose'] = purpose
                else:
                    current_module['purpose'] = ''
                
                current_module['files'] = ''
                current_module['dependencies'] = ''
            
            elif line and current_module:
                # Add additional information to current module
                if 'files' not in current_module or not current_module['files']:
                    current_module['files'] = line
                elif 'dependencies' not in current_module or not current_module['dependencies']:
                    current_module['dependencies'] = line
        
        # Add last module
        if current_module:
            modules.append(current_module)
        
        return modules
        
    except Exception as e:
        logging.error(f"Error creating modules table: {e}")
        return []

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
