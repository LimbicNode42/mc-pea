"""MCP protocol validation utilities."""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """Result of MCP validation."""
    
    passed: bool
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]


class MCPValidator:
    """Validator for MCP protocol compliance."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize MCP validator.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger("mcp_validator")
    
    async def validate_server(self, server_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate an MCP server for protocol compliance.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation results
        """
        server_path = Path(server_path)
        
        if not server_path.exists():
            return {
                "passed": False,
                "errors": [f"Server directory not found: {server_path}"],
                "warnings": [],
                "details": {},
            }
        
        results = {
            "passed": True,
            "errors": [],
            "warnings": [],
            "details": {},
        }
        
        # Validate directory structure
        structure_result = await self._validate_directory_structure(server_path)
        results["details"]["structure"] = structure_result
        if not structure_result["passed"]:
            results["passed"] = False
            results["errors"].extend(structure_result["errors"])
        
        # Validate package.json
        package_result = await self._validate_package_json(server_path)
        results["details"]["package"] = package_result
        if not package_result["passed"]:
            results["passed"] = False
            results["errors"].extend(package_result["errors"])
        
        # Validate TypeScript configuration
        typescript_result = await self._validate_typescript_config(server_path)
        results["details"]["typescript"] = typescript_result
        if not typescript_result["passed"]:
            results["passed"] = False
            results["errors"].extend(typescript_result["errors"])
        
        # Validate source code
        source_result = await self._validate_source_code(server_path)
        results["details"]["source"] = source_result
        if not source_result["passed"]:
            results["passed"] = False
            results["errors"].extend(source_result["errors"])
        
        # Compile TypeScript (if possible)
        compile_result = await self._validate_typescript_compilation(server_path)
        results["details"]["compilation"] = compile_result
        if not compile_result["passed"]:
            results["warnings"].extend(compile_result["errors"])
        
        self.logger.info(f"Validation complete for {server_path}: {'PASSED' if results['passed'] else 'FAILED'}")
        
        return results
    
    async def _validate_directory_structure(self, server_path: Path) -> Dict[str, Any]:
        """Validate the server directory structure.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        required_files = [
            "package.json",
            "tsconfig.json",
            "src/index.ts",
        ]
        
        recommended_files = [
            "README.md",
            "Dockerfile",
            "src/registrations.ts",
        ]
        
        errors = []
        warnings = []
        
        # Check required files
        for file_path in required_files:
            full_path = server_path / file_path
            if not full_path.exists():
                errors.append(f"Required file missing: {file_path}")
        
        # Check recommended files
        for file_path in recommended_files:
            full_path = server_path / file_path
            if not full_path.exists():
                warnings.append(f"Recommended file missing: {file_path}")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    async def _validate_package_json(self, server_path: Path) -> Dict[str, Any]:
        """Validate package.json file.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        package_file = server_path / "package.json"
        
        if not package_file.exists():
            return {
                "passed": False,
                "errors": ["package.json not found"],
                "warnings": [],
            }
        
        try:
            with open(package_file, 'r') as f:
                package_data = json.load(f)
        except Exception as e:
            return {
                "passed": False,
                "errors": [f"Failed to parse package.json: {e}"],
                "warnings": [],
            }
        
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["name", "version", "main", "dependencies"]
        for field in required_fields:
            if field not in package_data:
                errors.append(f"Missing required field in package.json: {field}")
        
        # Check for MCP SDK dependency
        dependencies = package_data.get("dependencies", {})
        if "@modelcontextprotocol/sdk" not in dependencies:
            errors.append("Missing MCP SDK dependency: @modelcontextprotocol/sdk")
        
        # Check scripts
        scripts = package_data.get("scripts", {})
        recommended_scripts = ["build", "start", "test"]
        for script in recommended_scripts:
            if script not in scripts:
                warnings.append(f"Recommended script missing: {script}")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    async def _validate_typescript_config(self, server_path: Path) -> Dict[str, Any]:
        """Validate TypeScript configuration.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        tsconfig_file = server_path / "tsconfig.json"
        
        if not tsconfig_file.exists():
            return {
                "passed": False,
                "errors": ["tsconfig.json not found"],
                "warnings": [],
            }
        
        try:
            with open(tsconfig_file, 'r') as f:
                tsconfig_data = json.load(f)
        except Exception as e:
            return {
                "passed": False,
                "errors": [f"Failed to parse tsconfig.json: {e}"],
                "warnings": [],
            }
        
        errors = []
        warnings = []
        
        # Check compiler options
        compiler_options = tsconfig_data.get("compilerOptions", {})
        
        # Check required options
        if compiler_options.get("strict") is not True:
            warnings.append("TypeScript strict mode is not enabled")
        
        if "outDir" not in compiler_options:
            warnings.append("No output directory specified")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    async def _validate_source_code(self, server_path: Path) -> Dict[str, Any]:
        """Validate source code files.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        src_path = server_path / "src"
        
        if not src_path.exists():
            return {
                "passed": False,
                "errors": ["src directory not found"],
                "warnings": [],
            }
        
        errors = []
        warnings = []
        
        # Check index.ts
        index_file = src_path / "index.ts"
        if index_file.exists():
            index_result = await self._validate_index_file(index_file)
            if not index_result["passed"]:
                errors.extend(index_result["errors"])
            warnings.extend(index_result["warnings"])
        
        # Check for TypeScript files
        ts_files = list(src_path.rglob("*.ts"))
        if len(ts_files) == 0:
            errors.append("No TypeScript files found in src directory")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    async def _validate_index_file(self, index_file: Path) -> Dict[str, Any]:
        """Validate the main index.ts file.
        
        Args:
            index_file: Path to index.ts
            
        Returns:
            Validation result
        """
        try:
            with open(index_file, 'r') as f:
                content = f.read()
        except Exception as e:
            return {
                "passed": False,
                "errors": [f"Failed to read index.ts: {e}"],
                "warnings": [],
            }
        
        errors = []
        warnings = []
        
        # Check for MCP SDK imports
        required_imports = [
            "@modelcontextprotocol/sdk",
        ]
        
        for import_name in required_imports:
            if import_name not in content:
                warnings.append(f"Missing import: {import_name}")
        
        # Check for stdio transport usage
        if "stdio" not in content.lower():
            warnings.append("Consider using stdio transport for MCP compliance")
        
        # Check for server.registerTool usage
        if "registerTool" not in content:
            warnings.append("No tool registration found")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }
    
    async def _validate_typescript_compilation(self, server_path: Path) -> Dict[str, Any]:
        """Validate TypeScript compilation.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        # Check if TypeScript is available
        try:
            result = await asyncio.create_subprocess_exec(
                "npx", "tsc", "--version",
                cwd=server_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.wait()
        except Exception:
            return {
                "passed": False,
                "errors": ["TypeScript compiler not available"],
                "warnings": [],
            }
        
        # Try to compile
        try:
            result = await asyncio.create_subprocess_exec(
                "npx", "tsc", "--noEmit",
                cwd=server_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return {
                    "passed": True,
                    "errors": [],
                    "warnings": [],
                }
            else:
                error_output = stderr.decode() if stderr else stdout.decode()
                return {
                    "passed": False,
                    "errors": [f"TypeScript compilation failed: {error_output}"],
                    "warnings": [],
                }
                
        except Exception as e:
            return {
                "passed": False,
                "errors": [f"Failed to run TypeScript compiler: {e}"],
                "warnings": [],
            }
    
    async def validate_mcp_protocol(self, server_path: Union[str, Path]) -> ValidationResult:
        """Validate MCP protocol compliance using MCP SDK.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        # This would use the MCP SDK client to test the server
        # For now, return a placeholder result
        return ValidationResult(
            passed=True,
            errors=[],
            warnings=["MCP protocol validation not yet implemented"],
            details={"note": "Protocol validation requires running server"},
        )
    
    async def validate_tools_and_resources(self, server_path: Union[str, Path]) -> ValidationResult:
        """Validate tool and resource implementations.
        
        Args:
            server_path: Path to the server directory
            
        Returns:
            Validation result
        """
        # Validate that tools and resources are properly implemented
        # This would analyze the source code for proper MCP patterns
        return ValidationResult(
            passed=True,
            errors=[],
            warnings=[],
            details={"note": "Tool and resource validation not yet implemented"},
        )
