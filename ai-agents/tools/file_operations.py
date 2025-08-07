"""
File Operations Tools for MCP API Integrator Agent

These tools handle basic file system operations like reading, writing, and listing directories.
"""

import os
import logging
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class ReadFileInput(BaseModel):
    """Input schema for ReadFileTool."""
    file_path: str = Field(
        ..., 
        description="Absolute or relative path to the file to read. Use relative paths from the MCP server directory."
    )


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = """
    Read the contents of a file from the filesystem. 
    
    Use this tool to:
    - Read existing MCP server files (package.json, tsconfig.json, etc.)
    - Read template files for reference
    - Read generated TypeScript files to check their content
    
    The file_path should be relative to the MCP server directory or an absolute path.
    """
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        """Read the contents of a file."""
        logger.debug(f"📖 ReadFileTool._run called with file_path={file_path}")
        
        try:
            # Resolve the absolute path
            if not os.path.isabs(file_path):
                # Try relative to current working directory first
                abs_path = os.path.abspath(file_path)
                if not os.path.exists(abs_path):
                    # Try relative to parent directory (common for mcp-servers)
                    abs_path = os.path.abspath(os.path.join('..', file_path))
            else:
                abs_path = file_path
            
            logger.debug(f"📖 Resolved path: {abs_path}")
            
            if not os.path.exists(abs_path):
                return f"Error: File not found: {abs_path}"
            
            if not os.path.isfile(abs_path):
                return f"Error: Path is not a file: {abs_path}"
            
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"📖 Successfully read {len(content)} characters from {abs_path}")
            return f"Successfully read file {abs_path}:\n\n{content}"
            
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(f"📖 {error_msg}")
            return error_msg


class WriteFileInput(BaseModel):
    """Input schema for WriteFileTool."""
    file_path: str = Field(
        ..., 
        description="Absolute or relative path where to write the file. Directories will be created if they don't exist."
    )
    content: str = Field(
        ..., 
        description="Content to write to the file. For TypeScript files, ensure proper formatting and syntax."
    )


class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = """
    Write content to a file, creating directories as needed.
    
    Use this tool to:
    - Create new TypeScript files in the MCP server
    - Update configuration files
    - Write generated code to specific locations
    
    The tool will automatically create any missing directories in the path.
    Be careful not to overwrite important files without reading them first.
    """
    args_schema: Type[BaseModel] = WriteFileInput

    def _run(self, file_path: str, content: str) -> str:
        """Write content to a file."""
        logger.debug(f"✍️ WriteFileTool._run called with file_path={file_path}, content_length={len(content)}")
        
        try:
            # Resolve the absolute path
            if not os.path.isabs(file_path):
                abs_path = os.path.abspath(file_path)
            else:
                abs_path = file_path
                
            logger.debug(f"✍️ Resolved path: {abs_path}")
            
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(abs_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"✍️ Created directory: {dir_path}")
            
            # Write the file
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.debug(f"✍️ Successfully wrote {len(content)} characters to {abs_path}")
            return f"Successfully wrote {len(content)} characters to {abs_path}"
            
        except Exception as e:
            error_msg = f"Error writing file {file_path}: {str(e)}"
            logger.error(f"✍️ {error_msg}")
            return error_msg


class ListDirectoryInput(BaseModel):
    """Input schema for ListDirectoryTool."""
    dir_path: str = Field(
        ..., 
        description="Absolute or relative path to the directory to list. Use '.' for current directory."
    )


class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = """
    List the contents of a directory to understand the file structure.
    
    Use this tool to:
    - Explore the MCP server directory structure
    - Check if required files exist before reading/writing
    - Understand the layout of template directories
    - Verify that generated files were created correctly
    
    Returns a list of files and subdirectories in the specified path.
    """
    args_schema: Type[BaseModel] = ListDirectoryInput

    def _run(self, dir_path: str) -> str:
        """List contents of a directory."""
        logger.debug(f"📂 ListDirectoryTool._run called with dir_path={dir_path}")
        
        try:
            # Resolve the absolute path
            if not os.path.isabs(dir_path):
                abs_path = os.path.abspath(dir_path)
            else:
                abs_path = dir_path
                
            logger.debug(f"📂 Resolved path: {abs_path}")
            
            if not os.path.exists(abs_path):
                return f"Error: Directory not found: {abs_path}"
            
            if not os.path.isdir(abs_path):
                return f"Error: Path is not a directory: {abs_path}"
            
            items = os.listdir(abs_path)
            items.sort()
            
            # Categorize items
            files = []
            directories = []
            
            for item in items:
                item_path = os.path.join(abs_path, item)
                if os.path.isdir(item_path):
                    directories.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    files.append(f"📄 {item} ({size} bytes)")
            
            result_lines = [f"Contents of {abs_path}:"]
            
            if directories:
                result_lines.append("\nDirectories:")
                result_lines.extend(directories)
            
            if files:
                result_lines.append("\nFiles:")
                result_lines.extend(files)
            
            if not directories and not files:
                result_lines.append("\n(Directory is empty)")
            
            result = "\n".join(result_lines)
            logger.debug(f"📂 Successfully listed {len(items)} items in {abs_path}")
            return result
            
        except Exception as e:
            error_msg = f"Error listing directory {dir_path}: {str(e)}"
            logger.error(f"📂 {error_msg}")
            return error_msg
