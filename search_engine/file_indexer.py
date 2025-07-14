"""
File Indexer
Scans folders and extracts content from PDF, DOCX, and TXT files.
"""

import os
import sys
from pdfminer.high_level import extract_text as extract_pdf_text
from pdfminer.pdfparser import PDFSyntaxError
from docx import Document
import re

class FileIndexer:
    def __init__(self):
        """Initialize the file indexer."""
        self.supported_extensions = {'.pdf', '.docx', '.txt'}
        self.system_folders = {
            'C:\\Windows',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            'C:\\System32',
            'C:\\ProgramData',
            'C:\\Users\\Default',
            'C:\\Boot',
            'C:\\Recovery'
        }
    
    def index_folder(self, folder_path):
        """
        Index all supported files in a folder.
        
        Args:
            folder_path (str): Path to the folder to index
            
        Returns:
            list: List of tuples (file_path, content)
        """
        if not os.path.exists(folder_path):
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        if self._is_system_folder(folder_path):
            raise ValueError(f"Cannot index system folder: {folder_path}")
        
        files_data = []
        
        print(f"Scanning folder: {folder_path}")
        
        # Walk through directory tree
        for root, dirs, files in os.walk(folder_path):
            # Skip system directories
            dirs[:] = [d for d in dirs if not self._is_system_folder(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check if file has supported extension
                _, ext = os.path.splitext(file.lower())
                if ext in self.supported_extensions:
                    try:
                        content = self._extract_content(file_path, ext)
                        if content and content.strip():
                            files_data.append((file_path, content))
                            print(f"Indexed: {file}")
                        else:
                            print(f"Empty content: {file}")
                    except Exception as e:
                        print(f"Error indexing {file}: {e}")
                        continue
        
        print(f"Indexed {len(files_data)} files")
        return files_data
    
    def _extract_content(self, file_path, extension):
        """
        Extract text content from a file based on its extension.
        
        Args:
            file_path (str): Path to the file
            extension (str): File extension
            
        Returns:
            str: Extracted text content
        """
        try:
            if extension == '.txt':
                return self._extract_txt_content(file_path)
            elif extension == '.pdf':
                return self._extract_pdf_content(file_path)
            elif extension == '.docx':
                return self._extract_docx_content(file_path)
            else:
                return ""
        except Exception as e:
            print(f"Error extracting content from {file_path}: {e}")
            return ""
    
    def _extract_txt_content(self, file_path):
        """Extract content from TXT file."""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    return self._clean_text(content)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading TXT file {file_path}: {e}")
                return ""
        
        print(f"Could not decode TXT file {file_path} with any encoding")
        return ""
    
    def _extract_pdf_content(self, file_path):
        """Extract content from PDF file."""
        try:
            content = extract_pdf_text(file_path)
            return self._clean_text(content)
        except PDFSyntaxError:
            print(f"Invalid PDF file: {file_path}")
            return ""
        except Exception as e:
            print(f"Error extracting PDF content from {file_path}: {e}")
            return ""
    
    def _extract_docx_content(self, file_path):
        """Extract content from DOCX file."""
        try:
            doc = Document(file_path)
            paragraphs = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text.strip())
            
            content = '\n'.join(paragraphs)
            return self._clean_text(content)
            
        except Exception as e:
            print(f"Error extracting DOCX content from {file_path}: {e}")
            return ""
    
    def _clean_text(self, text):
        """
        Clean and normalize extracted text.
        
        Args:
            text (str): Raw text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Limit text length to prevent memory issues
        max_length = 10000  # Adjust as needed
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    def _is_system_folder(self, folder_path):
        """
        Check if a folder is a system folder that should be avoided.
        
        Args:
            folder_path (str): Path to check
            
        Returns:
            bool: True if it's a system folder
        """
        if not folder_path:
            return False
        
        normalized_path = os.path.normpath(folder_path.upper())
        
        for sys_folder in self.system_folders:
            if normalized_path.startswith(sys_folder.upper()):
                return True
        
        return False
    
    def get_supported_extensions(self):
        """
        Get list of supported file extensions.
        
        Returns:
            set: Set of supported file extensions
        """
        return self.supported_extensions.copy()
    
    def is_supported_file(self, file_path):
        """
        Check if a file is supported for indexing.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            bool: True if the file is supported
        """
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_extensions
