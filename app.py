import streamlit as st
import os
import tempfile
import github_analyzer_functions as github_funcs
import document_generator_functions as doc_funcs
import base64

def main():
    st.set_page_config(
        page_title="GitHub Architecture Documentation Generator",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 GitHub Architecture Documentation Generator")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Key configuration
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY"),
            type="password",
            help="Enter your Gemini API key"
        )
        
        github_token = st.text_input(
            "GitHub Token (Optional)",
            value=os.getenv("GITHUB_TOKEN", ""),
            type="password",
            help="GitHub personal access token for higher rate limits"
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool analyzes GitHub repositories and generates comprehensive architecture documentation including:
        - High-level architecture overview
        - Module/component breakdown
        - Data flow descriptions
        - Design patterns identification
        - Mermaid diagrams
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Repository Analysis")
        
        # GitHub URL input
        github_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/slab/quill",
            help="Enter the full GitHub repository URL"
        )
        
        # Analysis options
        st.subheader("Analysis Options")
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            include_diagrams = st.checkbox("Include Mermaid Diagrams", value=True)
            include_patterns = st.checkbox("Analyze Design Patterns", value=True)
        
        with col_opt2:
            include_dependencies = st.checkbox("Analyze Dependencies", value=True)
            include_data_flow = st.checkbox("Include Data Flow Analysis", value=True)
        
        st.info("📁 This tool will analyze ALL relevant files in the repository while automatically skipping test files, build artifacts, and other non-essential files.")
        
        # Analyze button
        if st.button("🔍 Analyze Repository"):
            if not github_url:
                st.error("Please enter a GitHub repository URL")
                return
            
            if not gemini_api_key:
                st.error("Please provide a Gemini API key")
                return
            
            try:
                # Initialize clients
                github_funcs.initialize_clients(gemini_api_key, github_token if github_token else None)
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Validate and fetch repository
                status_text.text("Validating repository...")
                progress_bar.progress(10)
                
                repo_info = github_funcs.validate_repository(github_url)
                if not repo_info:
                    st.error("Invalid repository URL or repository not accessible")
                    return
                
                st.success(f"Repository found: {repo_info['name']} by {repo_info['owner']}")
                
                # Step 2: Fetch ALL repository files (not limited)
                status_text.text("Fetching all repository files...")
                progress_bar.progress(30)
                
                repo_structure = github_funcs.fetch_all_repository_files(github_url)
                
                # Show progress info
                stats = repo_structure['statistics']
                st.info(f"Found {stats['total_files']} total files, analyzing {stats['analyzed_files']} relevant files (skipped {stats['skipped_files']} test/build files)")
                
                # Step 3: Analyze with Gemini
                status_text.text("Analyzing repository with AI...")
                progress_bar.progress(60)
                
                analysis_options = {
                    'include_diagrams': include_diagrams,
                    'include_patterns': include_patterns,
                    'include_dependencies': include_dependencies,
                    'include_data_flow': include_data_flow
                }
                
                documentation = github_funcs.analyze_repository_with_ai(repo_structure, analysis_options)
                
                # Step 4: Prepare for document generation
                status_text.text("Preparing documentation...")
                progress_bar.progress(90)
                
                # Store results in session state
                st.session_state.documentation = documentation
                st.session_state.repo_info = repo_info
                
                progress_bar.progress(100)
                status_text.text("Analysis complete!")
                
                st.success("✅ Documentation generated successfully!")
                
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.exception(e)
    
    with col2:


        st.subheader("💡 Quick Examples")        
        example_repos = [
            {
                "name": "Quill Editor",
                "url": "https://github.com/slab/quill",
                "description": "Modern WYSIWYG editor"
            }
        ]

        for repo in example_repos:
            if st.button(f"📁 {repo['name']}", key=repo['url']):
                st.text((f"📄 {repo['url']}"))
    
    # Display results if available
    if hasattr(st.session_state, 'documentation') and st.session_state.documentation:
        st.markdown("---")
        st.header("📋 Generated Documentation")
        
        # Create tabs for different sections
        tabs = st.tabs([
            "Overview", 
            "Architecture", 
            "Modules", 
            "Data Flow", 
            "Design Patterns",
            "Export"
        ])
        
        doc = st.session_state.documentation
        
        with tabs[0]:  # Overview
            st.subheader("Repository Overview")
            st.markdown(doc.get('overview', 'No overview available'))
            
            if 'key_statistics' in doc:
                col1, col2, col3, col4, col5 = st.columns(5)
                stats = doc['key_statistics']
                col1.metric("Total Files", stats.get('total_files', 'N/A'))
                col2.metric("Code Files", stats.get('code_files', 'N/A'))
                col3.metric("Analyzed Files", stats.get('analyzed_files', 'N/A'))
                col4.metric("Main Language", stats.get('main_language', 'N/A'))
                col5.metric("Modules Found", stats.get('modules_count', 'N/A'))
        
        with tabs[1]:  # Architecture
            st.subheader("High-Level Architecture")
            st.markdown(doc.get('architecture', 'No architecture description available'))
            
            if 'architecture_diagram' in doc:
                st.subheader("Architecture Diagram")
                st.code(doc['architecture_diagram'], language='mermaid')
        
        with tabs[2]:  # Modules
            st.subheader("Module Breakdown")
            
            if 'modules_table' in doc:
                st.dataframe(doc['modules_table'], use_container_width=True)
            else:
                st.markdown(doc.get('modules', 'No module information available'))
        
        with tabs[3]:  # Data Flow
            st.subheader("Data Flow Analysis")
            st.markdown(doc.get('data_flow', 'No data flow analysis available'))
            
            if 'data_flow_diagram' in doc:
                st.subheader("Data Flow Diagram")
                st.code(doc['data_flow_diagram'], language='mermaid')
        
        with tabs[4]:  # Design Patterns
            st.subheader("Design Patterns")
            st.markdown(doc.get('design_patterns', 'No design patterns analysis available'))
        
        with tabs[5]:  # Export
            st.subheader("Export Documentation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download as PDF"):
                    try:
                        pdf_buffer = doc_funcs.generate_pdf_document(
                            st.session_state.documentation,
                            st.session_state.repo_info
                        )
                        
                        st.download_button(
                            label="💾 Download PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"{st.session_state.repo_info['name']}_architecture.pdf",
                            mime="application/pdf"
                        )
                        
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
            
            with col2:
                if st.button("📝 Download as DOCX", type="secondary"):
                    try:
                        docx_buffer = doc_funcs.generate_docx_document(
                            st.session_state.documentation,
                            st.session_state.repo_info
                        )
                        
                        st.download_button(
                            label="💾 Download DOCX",
                            data=docx_buffer.getvalue(),
                            file_name=f"{st.session_state.repo_info['name']}_architecture.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        
                    except Exception as e:
                        st.error(f"Error generating DOCX: {str(e)}")

if __name__ == "__main__":
    main()
