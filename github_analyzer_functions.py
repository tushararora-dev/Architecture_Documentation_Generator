import os
import re
import requests
import base64
from typing import Dict, List, Optional, Any
from google import genai
from google.genai import types
import json
import logging

# Initialize Gemini client globally
gemini_client = None
github_session = None
github_headers = {}

def initialize_clients(gemini_api_key: str, github_token: Optional[str] = None):
    """Initialize the clients for GitHub API and Gemini."""
    global gemini_client, github_session, github_headers
    
    gemini_client = genai.Client(api_key=gemini_api_key)
    github_session = requests.Session()
    
    # Set up headers for GitHub API
    github_headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-Architecture-Analyzer'
    }
    if github_token:
        github_headers['Authorization'] = f'token {github_token}'

# Supported file extensions for analysis
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.md',
    '.txt', '.dockerfile', '.makefile', '.gradle', '.properties'
}

# Files and directories to prioritize for analysis
PRIORITY_FILES = {
    'package.json', 'requirements.txt', 'cargo.toml', 'pom.xml',
    'build.gradle', 'gemfile', 'composer.json', 'setup.py',
    'readme.md', 'architecture.md', 'design.md', 'contributing.md',
    'dockerfile', 'makefile', 'changelog.md', 'license'
}

# Directories and files to skip (not important for architecture)
SKIP_PATTERNS = {
    'test', 'tests', '__tests__', 'spec', 'specs', '__pycache__',
    'node_modules', '.git', '.github', 'dist', 'build', 'target',
    'coverage', '.coverage', '.pytest_cache', '.tox', 'venv', 'env',
    '.env', 'logs', 'tmp', 'temp', '.DS_Store', '.vscode', '.idea',
    'vendor', 'public/assets', 'static/assets', 'assets/images'
}

def should_skip_path(path: str) -> bool:
    """Check if a path should be skipped based on skip patterns."""
    path_lower = path.lower()
    
    # Skip if any part of the path matches skip patterns
    for skip_pattern in SKIP_PATTERNS:
        if skip_pattern in path_lower:
            return True
    
    # Skip common non-code files
    if path_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
                           '.pdf', '.zip', '.tar', '.gz', '.exe', '.dmg',
                           '.app', '.deb', '.rpm', '.msi')):
        return True
    
    return False

def validate_repository(github_url: str) -> Optional[Dict[str, str]]:
    """Validate and extract repository information from GitHub URL."""
    try:
        # Extract owner and repo name from URL
        pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.search(pattern, github_url)
        
        if not match:
            return None
        
        owner, repo_name = match.groups()
        
        # Fetch repository info via GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        response = github_session.get(api_url, headers=github_headers)
        
        if response.status_code != 200:
            logging.error(f"GitHub API error: {response.status_code}")
            return None
        
        repo_data = response.json()
        
        return {
            'owner': owner,
            'name': repo_name,
            'full_name': repo_data.get('full_name', f"{owner}/{repo_name}"),
            'description': repo_data.get('description', ''),
            'language': repo_data.get('language', 'Unknown'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'url': github_url
        }
        
    except Exception as e:
        logging.error(f"Error validating repository: {e}")
        return None

def get_file_type(filename: str) -> str:
    """Determine file type based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    
    type_mapping = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.h': 'Header',
        '.cs': 'C#',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.json': 'JSON',
        '.md': 'Markdown',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.dockerfile': 'Docker',
        '.makefile': 'Makefile'
    }
    
    return type_mapping.get(ext, 'Other')

def fetch_repository_contents(owner: str, repo_name: str, path: str = "") -> List[Dict]:
    """Fetch repository contents for a specific path."""
    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
        response = github_session.get(api_url, headers=github_headers)
        
        if response.status_code != 200:
            logging.warning(f"Could not fetch contents for path {path}: {response.status_code}")
            return []
        
        contents = response.json()
        if not isinstance(contents, list):
            contents = [contents]
        
        return contents
        
    except Exception as e:
        logging.warning(f"Error fetching contents for path {path}: {e}")
        return []

def fetch_all_repository_files(github_url: str) -> Dict[str, Any]:
    """Fetch all relevant repository files and structure."""
    try:
        # Extract owner and repo name
        pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.search(pattern, github_url)
        if not match:
            raise ValueError("Invalid GitHub URL")
            
        owner, repo_name = match.groups()
        
        # Initialize structure
        structure = {
            'files': [],
            'directories': [],
            'key_files': {},
            'statistics': {
                'total_files': 0,
                'code_files': 0,
                'analyzed_files': 0,
                'skipped_files': 0,
                'languages': {}
            }
        }
        
        # Queue for breadth-first traversal
        paths_to_process = [""]
        processed_paths = set()
        
        while paths_to_process:
            current_path = paths_to_process.pop(0)
            
            if current_path in processed_paths:
                continue
            processed_paths.add(current_path)
            
            # Skip if path matches skip patterns
            if current_path and should_skip_path(current_path):
                structure['statistics']['skipped_files'] += 1
                continue
            
            contents = fetch_repository_contents(owner, repo_name, current_path)
            
            for content in contents:
                content_path = content['path']
                
                # Skip if matches skip patterns
                if should_skip_path(content_path):
                    structure['statistics']['skipped_files'] += 1
                    continue
                
                if content['type'] == "dir":
                    structure['directories'].append(content_path)
                    # Add directory to processing queue
                    paths_to_process.append(content_path)
                    
                elif content['type'] == "file":
                    file_info = {
                        'path': content_path,
                        'name': content['name'],
                        'size': content['size'],
                        'type': get_file_type(content['name'])
                    }
                    
                    structure['files'].append(file_info)
                    structure['statistics']['total_files'] += 1
                    
                    # Count file by extension
                    ext = os.path.splitext(content['name'])[1].lower()
                    if ext in CODE_EXTENSIONS:
                        structure['statistics']['code_files'] += 1
                        structure['statistics']['languages'][ext] = structure['statistics']['languages'].get(ext, 0) + 1
                    
                    # Fetch content for relevant files
                    should_analyze = (
                        content['name'].lower() in [f.lower() for f in PRIORITY_FILES] or
                        ext in CODE_EXTENSIONS or
                        content['size'] < 100000  # Files under 100KB
                    )
                    
                    if should_analyze:
                        try:
                            # Get file content
                            file_response = github_session.get(content['download_url'])
                            if file_response.status_code == 200:
                                file_content = file_response.text
                                structure['key_files'][content_path] = {
                                    'content': file_content,
                                    'size': content['size'],
                                    'type': ext
                                }
                                structure['statistics']['analyzed_files'] += 1
                        except Exception as e:
                            logging.warning(f"Could not fetch file {content_path}: {e}")
        
        return structure
        
    except Exception as e:
        logging.error(f"Error fetching repository structure: {e}")
        raise

def build_analysis_prompt(repo_structure: Dict, options: Dict[str, bool]) -> str:
    """Build comprehensive analysis prompt for Gemini."""
    
    # Build file structure summary
    stats = repo_structure['statistics']
    structure_summary = f"""## Repository Structure:
- Total files: {stats['total_files']}
- Code files: {stats['code_files']}
- Analyzed files: {stats['analyzed_files']}
- Skipped files: {stats['skipped_files']}
- Main directories: {', '.join(repo_structure['directories'][:20])}

"""
    
    # Add key file contents (prioritize important files)
    key_files_content = "## Key Files Content:\n"
    
    # Sort files by priority (priority files first, then by size)
    sorted_files = sorted(
        repo_structure['key_files'].items(),
        key=lambda x: (
            x[0].lower().split('/')[-1] not in [f.lower() for f in PRIORITY_FILES],
            x[1]['size']
        )
    )
    
    for file_path, file_data in sorted_files[:25]:  # Analyze up to 25 most important files
        key_files_content += f"\n### {file_path}:\n"
        content_preview = file_data['content'][:15000]  # First 3000 chars
        if len(file_data['content']) > 15000:
            content_preview += "...\n[File truncated for analysis]"
        key_files_content += f"```{file_data['type']}\n{content_preview}\n```\n"
    

    # # Analyze ALL relevant files (no artificial limit)
    # for file_path, file_data in sorted_files:
    #     key_files_content += f"\n### {file_path}:\n"
        
    #     # For larger files, use intelligent truncation
    #     content = file_data['content']
    #     if len(content) > 5000:
    #         # For large files, include beginning, middle snippet, and end
    #         content_preview = (
    #             content[:2000] + 
    #             "\n... [middle section truncated] ...\n" +
    #             content[-2000:]
    #         )
    #         content_preview += f"\n[File size: {len(content)} chars, showing key sections]"
    #     else:
    #         content_preview = content
            
    #     key_files_content += f"```{file_data['type']}\n{content_preview}\n```\n"



    # Build analysis requirements
    requirements = []
    if options.get('include_diagrams', True):
        requirements.append("- Generate Mermaid diagrams showing component relationships")
    if options.get('include_patterns', True):
        requirements.append("- Identify and explain design patterns used")
    if options.get('include_dependencies', True):
        requirements.append("- Analyze module dependencies and relationships")
    if options.get('include_data_flow', True):
        requirements.append("- Describe data flow from input to output")
    
    prompt = f"""You are a senior software architect analyzing a complete codebase. Based on the repository structure and key files provided below, create comprehensive architecture documentation.

{structure_summary}

{key_files_content}

## Analysis Requirements:
{chr(10).join(requirements)}

## Required Output Format:
Please provide your analysis in the following structured format:

### 1. OVERVIEW
Provide a high-level summary of the project's purpose, main functionality, and architectural approach.

### 2. ARCHITECTURE
Describe the high-level architecture, how major components interact, and the overall system design.

### 3. MODULES
Create a detailed breakdown of major modules/components:
- Module name
- Purpose/responsibility
- Key files
- Dependencies

### 4. DATA_FLOW
Explain how data flows through the system from user input to final output.

### 5. DESIGN_PATTERNS
Identify and explain the key design patterns used in the codebase.

### 6. MERMAID_ARCHITECTURE_DIAGRAM
Provide a Mermaid diagram showing the main architectural components and their relationships.

### 7. MERMAID_DATA_FLOW_DIAGRAM
Provide a Mermaid diagram showing data flow through the system.

Please be thorough and developer-friendly in your analysis. Focus on actionable insights that would help new developers understand and contribute to the codebase.
"""
    
    return prompt

def parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """Parse structured response from Gemini."""
    try:
        result = {
            'overview': '',
            'architecture': '',
            'modules': '',
            'data_flow': '',
            'design_patterns': '',
            'architecture_diagram': '',
            'data_flow_diagram': ''
        }
        
        # Parse sections using regex
        sections = {
            'overview': r'### 1\. OVERVIEW\s*\n(.*?)(?=### 2\. ARCHITECTURE|$)',
            'architecture': r'### 2\. ARCHITECTURE\s*\n(.*?)(?=### 3\. MODULES|$)',
            'modules': r'### 3\. MODULES\s*\n(.*?)(?=### 4\. DATA_FLOW|$)',
            'data_flow': r'### 4\. DATA_FLOW\s*\n(.*?)(?=### 5\. DESIGN_PATTERNS|$)',
            'design_patterns': r'### 5\. DESIGN_PATTERNS\s*\n(.*?)(?=### 6\. MERMAID_ARCHITECTURE_DIAGRAM|$)',
            'architecture_diagram': r'### 6\. MERMAID_ARCHITECTURE_DIAGRAM\s*\n```mermaid\s*\n(.*?)\n```',
            'data_flow_diagram': r'### 7\. MERMAID_DATA_FLOW_DIAGRAM\s*\n```mermaid\s*\n(.*?)\n```'
        }
        
        for section, pattern in sections.items():
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            if match:
                result[section] = match.group(1).strip()
        
        # If no structured sections found, use the entire response as overview
        if not any(result.values()):
            result['overview'] = response_text
        
        return result
        
    except Exception as e:
        logging.warning(f"Error parsing Gemini response: {e}")
        return {'overview': response_text}

def get_main_language(languages: Dict[str, int]) -> str:
    """Get the main programming language based on file count."""
    if not languages:
        return 'Unknown'
    
    main_ext = max(languages.keys(), key=lambda k: languages[k])
    return main_ext.replace('.', '').upper()

def analyze_repository_with_ai(repo_structure: Dict, options: Dict[str, bool]) -> Dict[str, Any]:
    """Analyze repository structure using Gemini LLM."""
    try:
        # Prepare analysis prompt
        analysis_prompt = build_analysis_prompt(repo_structure, options)
        
        # Call Gemini API
        response = gemini_client.models.generate_content(
            model="gemini-2.5-pro",
            contents=analysis_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8192
            )
        )
        
        # Parse response
        response_text = response.text if response.text else ""
        analysis_result = parse_gemini_response(response_text)
        
        # Add statistics
        analysis_result['key_statistics'] = {
            'total_files': repo_structure['statistics']['total_files'],
            'code_files': repo_structure['statistics']['code_files'],
            'analyzed_files': repo_structure['statistics']['analyzed_files'],
            'skipped_files': repo_structure['statistics']['skipped_files'],
            'main_language': get_main_language(repo_structure['statistics']['languages']),
            'modules_count': len(repo_structure['directories'])
        }
        
        return analysis_result
        
    except Exception as e:
        logging.error(f"Error analyzing repository: {e}")
        raise