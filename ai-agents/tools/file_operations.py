"""File operations utilities for AI agents."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles


class FileOperations:
    """Utility class for file operations."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize file operations.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("file_operations")
    
    async def read_file(self, file_path: Union[str, Path]) -> str:
        """Read a file asynchronously.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as string
        """
        file_path = Path(file_path)
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            self.logger.debug(f"Read file: {file_path}")
            return content
            
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {e}")
            raise
    
    async def write_file(
        self, file_path: Union[str, Path], content: str
    ) -> None:
        """Write content to a file asynchronously.
        
        Args:
            file_path: Path to the file
            content: Content to write
        """
        file_path = Path(file_path)
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            self.logger.debug(f"Wrote file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            raise
    
    async def read_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Read a JSON file asynchronously.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON data
        """
        content = await self.read_file(file_path)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from {file_path}: {e}")
            raise
    
    async def write_json(
        self, file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2
    ) -> None:
        """Write data to a JSON file asynchronously.
        
        Args:
            file_path: Path to the JSON file
            data: Data to write
            indent: JSON indentation
        """
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        await self.write_file(file_path, content)
    
    async def copy_file(
        self, source_path: Union[str, Path], dest_path: Union[str, Path]
    ) -> None:
        """Copy a file asynchronously.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
        """
        content = await self.read_file(source_path)
        await self.write_file(dest_path, content)
        
        self.logger.debug(f"Copied file: {source_path} -> {dest_path}")
    
    async def copy_directory(
        self, source_dir: Union[str, Path], dest_dir: Union[str, Path]
    ) -> None:
        """Copy a directory recursively.
        
        Args:
            source_dir: Source directory path
            dest_dir: Destination directory path
        """
        source_dir = Path(source_dir)
        dest_dir = Path(dest_dir)
        
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for item in source_dir.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(source_dir)
                dest_file = dest_dir / relative_path
                await self.copy_file(item, dest_file)
        
        self.logger.info(f"Copied directory: {source_dir} -> {dest_dir}")
    
    def list_files(
        self, directory: Union[str, Path], pattern: str = "*"
    ) -> List[Path]:
        """List files in a directory.
        
        Args:
            directory: Directory path
            pattern: File pattern (glob)
            
        Returns:
            List of file paths
        """
        directory = Path(directory)
        
        if not directory.exists():
            return []
        
        return list(directory.glob(pattern))
    
    def list_files_recursive(
        self, directory: Union[str, Path], pattern: str = "*"
    ) -> List[Path]:
        """List files in a directory recursively.
        
        Args:
            directory: Directory path
            pattern: File pattern (glob)
            
        Returns:
            List of file paths
        """
        directory = Path(directory)
        
        if not directory.exists():
            return []
        
        return list(directory.rglob(pattern))
    
    async def delete_file(self, file_path: Union[str, Path]) -> None:
        """Delete a file.
        
        Args:
            file_path: Path to the file
        """
        file_path = Path(file_path)
        
        if file_path.exists():
            file_path.unlink()
            self.logger.debug(f"Deleted file: {file_path}")
    
    async def delete_directory(self, directory: Union[str, Path]) -> None:
        """Delete a directory and its contents.
        
        Args:
            directory: Directory path
        """
        import shutil
        
        directory = Path(directory)
        
        if directory.exists():
            shutil.rmtree(directory)
            self.logger.debug(f"Deleted directory: {directory}")
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if a file exists.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file exists
        """
        return Path(file_path).exists()
    
    def directory_exists(self, directory: Union[str, Path]) -> bool:
        """Check if a directory exists.
        
        Args:
            directory: Directory path
            
        Returns:
            True if directory exists
        """
        return Path(directory).is_dir()
    
    async def get_file_stats(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file statistics.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File statistics
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        
        return {
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_file": file_path.is_file(),
            "is_directory": file_path.is_dir(),
        }
    
    async def create_directory_structure(self, structure: Dict[str, Any], base_path: Union[str, Path]) -> None:
        """Create a directory structure from a dictionary.
        
        Args:
            structure: Directory structure definition
            base_path: Base path for the structure
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        for name, content in structure.items():
            path = base_path / name
            
            if isinstance(content, dict):
                # It's a directory
                await self.create_directory_structure(content, path)
            else:
                # It's a file
                await self.write_file(path, str(content))
        
        self.logger.info(f"Created directory structure at: {base_path}")
