#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 18 15:26:40 2025

@author: ha
"""
"""
SQL Generator Chatbot - Core Engine (Phase 1)
RAG-based system that generates SQL from natural language requirements
Uses existing queries as examples and data dictionary as context
"""

import pandas as pd
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from typing import List, Dict, Tuple

# Configuration
PROJECT_FOLDER = '/Users/ha/Documents/gb_report_info/'
INPUT_FILE = 'report_info_formatted.xlsx'
TABLE_CATALOG = 'documentation/table_catalog.json'

class SQLChatbot:
    def __init__(self):
        """Initialize the chatbot with data and OpenAI client"""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No API key found!")
        
        self.client = OpenAI(api_key=api_key)
        self.queries_db = []  # Store queries with embeddings
        self.table_catalog = {}
        
        print("🤖 Initializing SQL Generator Chatbot...")
        self._load_data()
        self._create_embeddings()
        print("✅ Chatbot ready!\n")
    
    def _load_data(self):
        """Load SQL queries and data dictionary"""
        os.chdir(PROJECT_FOLDER)
        
        # Load queries
        print("📖 Loading SQL queries...")
        df = pd.read_excel(INPUT_FILE)
        
        for idx, row in df.iterrows():
            if pd.notna(row['SQL Query']):
                self.queries_db.append({
                    'id': idx,
                    'name': row['Report Name'],
                    'description': row['Description'] if pd.notna(row['Description']) else '',
                    'sql': row['SQL Query'],
                    'tables': row['tables'] if pd.notna(row['tables']) else '',
                    'fields': row['tbl_fields'] if pd.notna(row['tbl_fields']) else '',
                    'folder': row['Folder Path'] if pd.notna(row['Folder Path']) else ''
                })
        
        print(f"✓ Loaded {len(self.queries_db)} queries")
        
        # Load table catalog if available
        catalog_path = os.path.join(PROJECT_FOLDER, TABLE_CATALOG)
        if os.path.exists(catalog_path):
            print("📚 Loading table catalog...")
            with open(catalog_path, 'r') as f:
                self.table_catalog = json.load(f)
            print(f"✓ Loaded {len(self.table_catalog)} tables")
        else:
            print("⚠️  Table catalog not found. Run generate_documentation.py first for best results.")
    
    def _create_embeddings(self):
        """Create embeddings for all queries for semantic search"""
        print("🔄 Creating embeddings for semantic search...")
        
        for query in self.queries_db:
            # Combine name, description, and tables for embedding
            text = f"{query['name']}. {query['description']}. Tables: {query['tables']}"
            
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                query['embedding'] = response.data[0].embedding
            except Exception as e:
                print(f"  Warning: Failed to create embedding for {query['name']}: {e}")
                query['embedding'] = None
        
        print(f"✓ Created embeddings for {len([q for q in self.queries_db if q['embedding']])} queries")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not a or not b:
            return 0.0
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def find_similar_queries(self, requirement: str, top_k: int = 3) -> List[Dict]:
        """Find most similar queries using semantic search"""
        print(f"\n🔍 Searching for similar queries...")
        
        # Get embedding for requirement
        req_embedding = self._get_embedding(requirement)
        if not req_embedding:
            return []
        
        # Calculate similarities
        similarities = []
        for query in self.queries_db:
            if query['embedding']:
                similarity = self._cosine_similarity(req_embedding, query['embedding'])
                similarities.append({
                    'query': query,
                    'similarity': similarity
                })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top K
        top_matches = similarities[:top_k]
        
        print(f"✓ Found {len(top_matches)} similar queries:")
        for i, match in enumerate(top_matches, 1):
            print(f"  {i}. {match['query']['name']} (similarity: {match['similarity']:.2f})")
        
        return top_matches
    
    def _build_context(self, similar_queries: List[Dict], requirement: str) -> str:
        """Build context for GPT-4 from similar queries and table catalog"""
        
        context = f"""You are an expert SQL developer helping to write queries for an FCUBS banking database.

USER REQUIREMENT:
{requirement}

SIMILAR EXISTING QUERIES:
"""
        
        # Add similar queries as examples
        for i, match in enumerate(similar_queries, 1):
            query = match['query']
            context += f"""
Example {i}: {query['name']}
Description: {query['description']}
Tables used: {query['tables']}
SQL:
{query['sql'][:500]}...
---
"""
        
        # Add relevant table information
        context += "\n\nAVAILABLE TABLES AND FIELDS:\n"
        
        # Extract tables mentioned in requirement or similar queries
        mentioned_tables = set()
        for match in similar_queries:
            if match['query']['tables']:
                tables = [t.strip().split('.')[-1] for t in match['query']['tables'].split(',')]
                mentioned_tables.update(tables)
        
        # Add table details
        for table_name in list(mentioned_tables)[:10]:  # Limit to 10 tables to avoid token limits
            if table_name in self.table_catalog:
                table_info = self.table_catalog[table_name]
                fields = ', '.join(table_info['fields'][:20])  # First 20 fields
                context += f"\n{table_name}: {fields}"
                if len(table_info['fields']) > 20:
                    context += f" ... (+{len(table_info['fields']) - 20} more)"
        
        return context
    
    def generate_sql(self, requirement: str, explain: bool = True) -> Dict:
        """Generate SQL from natural language requirement"""
        
        print("\n" + "="*70)
        print("🎯 SQL GENERATION REQUEST")
        print("="*70)
        print(f"Requirement: {requirement}\n")
        
        # Find similar queries
        similar_queries = self.find_similar_queries(requirement, top_k=3)
        
        if not similar_queries:
            return {
                'success': False,
                'error': 'No similar queries found. Please provide more details.'
            }
        
        # Build context
        context = self._build_context(similar_queries, requirement)
        
        # Generate SQL using GPT-4
        print("\n🤖 Generating SQL with GPT-4...")
        
        prompt = f"""{context}

Based on the similar queries and available tables above, generate a SQL query that fulfills the user requirement.

IMPORTANT INSTRUCTIONS:
1. Follow the same patterns and style as the example queries
2. Use ONLY the tables and fields that actually exist in the database (shown above)
3. Include proper JOINs based on the examples
4. Use appropriate WHERE clauses and filters
5. Add helpful comments in the SQL
6. Make sure the query is syntactically correct for Oracle database
7. Use table aliases for readability

Provide your response in this JSON format:
{{
  "sql": "the complete SQL query",
  "explanation": "brief explanation of what the query does",
  "tables_used": ["list", "of", "tables"],
  "notes": "any important notes or assumptions"
}}

Generate the SQL now:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert SQL developer for FCUBS banking systems."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON from response
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            
            # Add metadata
            result['success'] = True
            result['similar_queries'] = [q['query']['name'] for q in similar_queries]
            
            print("✅ SQL generated successfully!\n")
            
            return result
            
        except Exception as e:
            print(f"❌ Error generating SQL: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def chat(self):
        """Interactive chat interface"""
        print("\n" + "="*70)
        print("🤖 SQL GENERATOR CHATBOT")
        print("="*70)
        print("\nI can help you generate SQL queries based on your requirements.")
        print("I'll search through existing queries and use your data dictionary.")
        print("\nCommands:")
        print("  - Type your requirement to generate SQL")
        print("  - 'examples' - Show available query examples")
        print("  - 'tables' - List available tables")
        print("  - 'quit' or 'exit' - Exit the chatbot")
        print("="*70)
        
        while True:
            print("\n")
            user_input = input("💬 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye! Happy querying!")
                break
            
            elif user_input.lower() == 'examples':
                print("\n📚 Available Query Examples:")
                print("-" * 70)
                for i, query in enumerate(self.queries_db[:10], 1):
                    print(f"{i}. {query['name']}")
                    print(f"   Folder: {query['folder']}")
                    print(f"   Tables: {query['tables'][:80]}...")
                    print()
                if len(self.queries_db) > 10:
                    print(f"... and {len(self.queries_db) - 10} more queries")
                continue
            
            elif user_input.lower() == 'tables':
                print("\n🗄️  Available Tables:")
                print("-" * 70)
                if self.table_catalog:
                    for table_name, info in list(self.table_catalog.items())[:15]:
                        print(f"• {table_name} ({len(info['fields'])} fields)")
                    if len(self.table_catalog) > 15:
                        print(f"... and {len(self.table_catalog) - 15} more tables")
                else:
                    print("Table catalog not loaded. Run generate_documentation.py first.")
                continue
            
            # Generate SQL
            result = self.generate_sql(user_input)
            
            if result['success']:
                print("\n" + "="*70)
                print("✨ GENERATED SQL")
                print("="*70)
                print(f"\n{result['sql']}\n")
                print("="*70)
                print(f"\n📝 Explanation:")
                print(f"{result['explanation']}\n")
                print(f"📊 Tables used: {', '.join(result['tables_used'])}")
                print(f"🔗 Based on: {', '.join(result['similar_queries'])}")
                if 'notes' in result:
                    print(f"\n💡 Notes: {result['notes']}")
                print("="*70)
            else:
                print(f"\n❌ Error: {result['error']}")

def main():
    """Main function"""
    
    try:
        # Initialize chatbot
        chatbot = SQLChatbot()
        
        # Start interactive chat
        chatbot.chat()
        
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()