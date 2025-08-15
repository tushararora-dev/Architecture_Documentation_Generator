# Overview

This is a GitHub Architecture Documentation Generator built with Streamlit that analyzes GitHub repositories and generates comprehensive architecture documentation using AI. The application leverages Google's Gemini AI API to analyze repository code and structure, then automatically generates professional documentation in PDF and DOCX formats. The tool provides insights into high-level architecture, component breakdown, data flow descriptions, design patterns, and includes Mermaid diagrams for visual representation.

# User Preferences

Preferred communication style: Simple, everyday language.
Code architecture preference: Function-based approach (no classes)
File analysis scope: Analyze ALL relevant files in repositories while filtering out test files and build artifacts

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit web application framework
- **Layout**: Wide layout with sidebar configuration and main content area using column-based design
- **User Interface**: Simple form-based interface for GitHub URL input and API key configuration
- **State Management**: Streamlit's built-in session state management

## Backend Architecture
- **Core Functions** (Function-based architecture per user preference):
  - `github_analyzer_functions.py`: Functions for GitHub repository analysis and data extraction
  - `document_generator_functions.py`: Functions for document creation in PDF and DOCX formats

## AI Integration
- **AI Provider**: Google Gemini AI API for code analysis and documentation generation
- **Analysis Scope**: Supports multiple programming languages and file types including Python, JavaScript, TypeScript, Java, C++, HTML, CSS, configuration files
- **Priority Files**: Focuses on key files like package.json, requirements.txt, README.md for comprehensive analysis

## Document Generation
- **PDF Generation**: Uses ReportLab library with custom styling and professional formatting
- **DOCX Generation**: Utilizes python-docx library for Microsoft Word document creation
- **Styling**: Custom styles for titles, headings, and content sections with professional color schemes

## Data Processing Pipeline
1. **URL Validation**: Validates GitHub repository URLs and extracts owner/repository information
2. **Comprehensive Repository Analysis**: Fetches ALL repository files while intelligently filtering out test files, build artifacts, and non-essential files
3. **Smart File Processing**: Analyzes all relevant code files with priority given to configuration files, README files, and core source code
4. **AI-Powered Code Analysis**: Uses Gemini AI to analyze complete code structure, identify patterns, and generate comprehensive insights
5. **Professional Document Generation**: Creates formatted documentation with architecture diagrams and component descriptions

# External Dependencies

## Third-Party APIs
- **GitHub API**: Repository data fetching and file content access
- **Google Gemini AI API**: Code analysis and documentation generation

## Core Libraries
- **Streamlit**: Web application framework for user interface
- **PyGithub**: GitHub API integration library
- **google-genai**: Google Gemini AI client library
- **ReportLab**: PDF document generation
- **python-docx**: Microsoft Word document creation

## File Processing
- **Supported Formats**: Python, JavaScript, TypeScript, Java, C/C++, C#, PHP, Ruby, Go, Rust, Swift, Kotlin, Scala, HTML, CSS, SCSS, Vue, Svelte, JSON, XML, YAML, TOML
- **Configuration Files**: package.json, requirements.txt, Cargo.toml, pom.xml, build.gradle, Gemfile, composer.json, setup.py

## Authentication
- **GitHub Token**: Optional GitHub personal access token for enhanced rate limits
- **Gemini API Key**: Required for AI-powered code analysis and documentation generation