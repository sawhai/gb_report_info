#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 22 22:23:17 2025

@author: ha
"""
"""
SQL Generator Chatbot - Streamlit Web Interface
Beautiful web UI for generating SQL from natural language
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
import os

# Add path for imports
sys.path.append('/Users/ha/Documents/gb_report_info/')
from sql_chatbot_core import SQLChatbot

# Page configuration
st.set_page_config(
    page_title="SQL Generator AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid;
    }
    
    .user-message {
        background: #f0f2f6;
        border-left-color: #667eea;
    }
    
    .assistant-message {
        background: #e8f4f8;
        border-left-color: #00c896;
    }
    
    .sql-code {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        margin: 1rem 0;
        overflow-x: auto;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .example-query {
        background: white;
        padding: 0.8rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .example-query:hover {
        border-color: #667eea;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }
    
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chatbot' not in st.session_state:
    with st.spinner('🤖 Initializing AI SQL Generator...'):
        st.session_state.chatbot = SQLChatbot()
    st.session_state.history = []
    st.session_state.query_count = 0

# Sidebar
with st.sidebar:
    st.markdown("### 🤖 SQL Generator AI")
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Statistics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(st.session_state.chatbot.queries_db)}</div>
            <div class="metric-label">Queries</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(st.session_state.chatbot.table_catalog)}</div>
            <div class="metric-label">Tables</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Session stats
    st.markdown("### 📈 Session Stats")
    st.metric("Queries Generated", st.session_state.query_count)
    st.metric("Conversation History", len(st.session_state.history))
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.query_count = 0
        st.rerun()
    
    if st.button("📥 Download History"):
        if st.session_state.history:
            history_json = json.dumps(st.session_state.history, indent=2)
            st.download_button(
                label="Download JSON",
                data=history_json,
                file_name=f"sql_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    st.markdown("---")
    
    # Example queries
    st.markdown("### 📚 Example Queries")
    
    examples = [
        "Show all customer transactions",
        "List customers with deposits > 10000",
        "Find pending items by branch",
        "Get customer account details",
        "Show credit transactions last month"
    ]
    
    for example in examples:
        if st.button(example, key=f"ex_{example}", use_container_width=True):
            st.session_state.user_input = example
    
    st.markdown("---")
    
    # Info
    with st.expander("ℹ️ About"):
        st.markdown("""
        **SQL Generator AI** uses advanced RAG (Retrieval-Augmented Generation) 
        to create SQL queries from your natural language requirements.
        
        **How it works:**
        1. Searches your existing queries
        2. Finds similar patterns
        3. Uses your data dictionary
        4. Generates optimized SQL
        
        **Powered by:**
        - OpenAI GPT-4
        - Semantic Search
        - Your query database
        """)

# Main content
st.markdown('<h1 class="main-header">🤖 SQL Generator AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Transform natural language into SQL queries instantly</p>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Available Data", "📜 History"])

with tab1:
    # Chat interface
    st.markdown("### Ask me to generate SQL!")
    
    # Display chat history
    for item in st.session_state.history:
        # User message
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 You:</strong><br>
            {item['requirement']}
        </div>
        """, unsafe_allow_html=True)
        
        # Assistant message
        if item['success']:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Assistant:</strong><br>
                {item['explanation']}
            </div>
            """, unsafe_allow_html=True)
            
            # SQL Code
            st.code(item['sql'], language='sql')
            
            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📊 **Tables:** {', '.join(item['tables_used'][:3])}")
            with col2:
                st.info(f"🔗 **Based on:** {', '.join(item['similar_queries'][:2])}")
            with col3:
                # Copy button
                st.button(f"📋 Copy SQL", key=f"copy_{item['timestamp']}")
        else:
            st.error(f"❌ Error: {item['error']}")
        
        st.markdown("---")
    
    # Input form
    with st.form("query_form", clear_on_submit=True):
        user_input = st.text_area(
            "What SQL query do you need?",
            placeholder="Example: Show me all customers with deposits greater than 5000 in the last 30 days",
            height=100,
            key="query_input"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submit = st.form_submit_button("🚀 Generate SQL", use_container_width=True)
        with col2:
            show_similar = st.checkbox("Show similar queries", value=True)
        with col3:
            show_context = st.checkbox("Show context", value=False)
        
        if submit and user_input:
            with st.spinner('🔍 Searching similar queries and generating SQL...'):
                # Find similar queries
                similar_queries = st.session_state.chatbot.find_similar_queries(user_input, top_k=3)
                
                # Show similar queries if requested
                if show_similar and similar_queries:
                    st.markdown("### 🔍 Similar Queries Found:")
                    for i, match in enumerate(similar_queries, 1):
                        with st.expander(f"{i}. {match['query']['name']} (Similarity: {match['similarity']:.2%})"):
                            st.markdown(f"**Description:** {match['query']['description']}")
                            st.markdown(f"**Tables:** {match['query']['tables']}")
                            st.code(match['query']['sql'][:300] + "...", language='sql')
                
                # Generate SQL
                result = st.session_state.chatbot.generate_sql(user_input, explain=True)
                
                # Add to history
                history_item = {
                    'timestamp': datetime.now().isoformat(),
                    'requirement': user_input,
                    'success': result['success']
                }
                
                if result['success']:
                    history_item.update({
                        'sql': result['sql'],
                        'explanation': result['explanation'],
                        'tables_used': result['tables_used'],
                        'similar_queries': result['similar_queries'],
                        'notes': result.get('notes', '')
                    })
                    st.session_state.query_count += 1
                else:
                    history_item['error'] = result['error']
                
                st.session_state.history.append(history_item)
                
                # Show context if requested
                if show_context and result['success']:
                    with st.expander("🔍 View Generation Context"):
                        st.markdown("**Similar Queries Used:**")
                        for sq in result['similar_queries']:
                            st.markdown(f"- {sq}")
                        st.markdown(f"\n**Tables Involved:** {', '.join(result['tables_used'])}")
                
                st.rerun()

with tab2:
    # Available data
    st.markdown("### 📊 Available Database Information")
    
    # Tables
    st.markdown("#### 🗄️ Tables")
    if st.session_state.chatbot.table_catalog:
        table_df = pd.DataFrame([
            {
                'Table Name': table_name,
                'Fields': len(info['fields']),
                'Used in Reports': len(info['used_in_reports']),
                'Connections': ', '.join(info['connections'])
            }
            for table_name, info in st.session_state.chatbot.table_catalog.items()
        ])
        
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Table details
        selected_table = st.selectbox("Select a table to view details:", list(st.session_state.chatbot.table_catalog.keys()))
        
        if selected_table:
            table_info = st.session_state.chatbot.table_catalog[selected_table]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Fields:**")
                st.write(", ".join(table_info['fields'][:20]))
                if len(table_info['fields']) > 20:
                    st.caption(f"... and {len(table_info['fields']) - 20} more fields")
            
            with col2:
                st.markdown("**Used in Reports:**")
                for report in table_info['used_in_reports'][:5]:
                    st.write(f"• {report}")
                if len(table_info['used_in_reports']) > 5:
                    st.caption(f"... and {len(table_info['used_in_reports']) - 5} more reports")
    else:
        st.warning("📭 Table catalog not loaded. Run generate_documentation.py first.")
    
    st.markdown("---")
    
    # Example queries
    st.markdown("#### 📚 Example Queries in Database")
    query_df = pd.DataFrame([
        {
            'Report Name': q['name'],
            'Folder': q['folder'],
            'Tables': len(q['tables'].split(',')) if q['tables'] else 0,
            'Description': q['description'][:100] + '...' if len(q['description']) > 100 else q['description']
        }
        for q in st.session_state.chatbot.queries_db
    ])
    
    st.dataframe(
        query_df,
        use_container_width=True,
        hide_index=True
    )

with tab3:
    # History
    st.markdown("### 📜 Conversation History")
    
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"Query {len(st.session_state.history) - i + 1}: {item['requirement'][:50]}..."):
                st.markdown(f"**📅 Time:** {item['timestamp']}")
                st.markdown(f"**💬 Requirement:** {item['requirement']}")
                
                if item['success']:
                    st.markdown("**✅ Status:** Success")
                    st.markdown(f"**📝 Explanation:** {item['explanation']}")
                    st.code(item['sql'], language='sql')
                    st.markdown(f"**📊 Tables:** {', '.join(item['tables_used'])}")
                    st.markdown(f"**🔗 Similar Queries:** {', '.join(item['similar_queries'])}")
                    if item.get('notes'):
                        st.markdown(f"**💡 Notes:** {item['notes']}")
                else:
                    st.markdown("**❌ Status:** Failed")
                    st.error(f"Error: {item['error']}")
    else:
        st.info("💬 No queries generated yet. Start chatting to see history!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🤖 Powered by OpenAI GPT-4 | Built with Streamlit</p>
    <p style="font-size: 0.8rem;">Generate SQL queries from natural language using AI and your existing query patterns</p>
</div>
""", unsafe_allow_html=True)