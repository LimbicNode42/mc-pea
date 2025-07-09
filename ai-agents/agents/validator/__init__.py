"""
Validator Agent - Validates MCP servers for protocol compliance and quality.
"""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from core.base_agent import BaseAgent
from tools.file_operations import FileOperations
from tools.mcp_validators import MCPValidator


class ValidatorAgent(BaseAgent):
    """Agent that validates MCP servers for protocol compliance and quality."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_ops = FileOperations()
        self.mcp_validators = MCPValidator()
        self.validation_cache = {}
    
    async def validate_mcp_server(self, server_path: str, validation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate an MCP server for protocol compliance and quality.
        
        Args:
            server_path: Path to the MCP server directory
            validation_config: Optional validation configuration
            
        Returns:
            Validation results with scores and recommendations
        """
        try:
            cache_key = f"validation_{hash(server_path)}"
            
            if cache_key in self.validation_cache:
                return self.validation_cache[cache_key]
            
            # Initialize validation results
            results = {
                'server_path': server_path,
                'validation_timestamp': self._get_timestamp(),
                'protocol_compliance': {},
                'code_quality': {},
                'security_analysis': {},
                'performance_metrics': {},
                'overall_score': 0,
                'recommendations': [],
                'errors': [],
                'warnings': []
            }
            
            # Run validation checks
            await self._validate_protocol_compliance(server_path, results)
            await self._validate_code_quality(server_path, results)
            await self._validate_security(server_path, results)
            await self._validate_performance(server_path, results)
            
            # Calculate overall score
            results['overall_score'] = self._calculate_overall_score(results)
            
            # Generate recommendations
            results['recommendations'] = self._generate_recommendations(results)
            
            # Cache results
            self.validation_cache[cache_key] = results
            
            await self._emit_message('server_validated', {
                'server_path': server_path,
                'overall_score': results['overall_score'],
                'error_count': len(results['errors']),
                'warning_count': len(results['warnings'])
            })
            
            return results
            
        except Exception as e:
            await self._emit_message('validation_error', {
                'error': str(e),
                'server_path': server_path
            })
            raise
    
    async def _validate_protocol_compliance(self, server_path: str, results: Dict[str, Any]):
        """Validate MCP protocol compliance."""
        compliance = {
            'mcp_sdk_usage': False,
            'stdio_transport': False,
            'tool_registration': False,
            'resource_handling': False,
            'error_handling': False,
            'schema_validation': False,
            'score': 0
        }
        
        try:
            # Check for MCP SDK usage
            if await self._check_mcp_sdk_import(server_path):
                compliance['mcp_sdk_usage'] = True
            
            # Check for stdio transport
            if await self._check_stdio_transport(server_path):
                compliance['stdio_transport'] = True
            
            # Check for proper tool registration
            if await self._check_tool_registration(server_path):
                compliance['tool_registration'] = True
            
            # Check for resource handling
            if await self._check_resource_handling(server_path):
                compliance['resource_handling'] = True
            
            # Check for error handling
            if await self._check_error_handling(server_path):
                compliance['error_handling'] = True
            
            # Check for schema validation
            if await self._check_schema_validation(server_path):
                compliance['schema_validation'] = True
            
            # Calculate compliance score
            total_checks = 6
            passed_checks = sum(1 for v in compliance.values() if isinstance(v, bool) and v)
            compliance['score'] = (passed_checks / total_checks) * 100
            
            # Add specific validation using MCP SDK client
            sdk_validation = await self._run_mcp_sdk_validation(server_path)
            compliance['sdk_validation'] = sdk_validation
            
            results['protocol_compliance'] = compliance
            
        except Exception as e:
            results['errors'].append(f"Protocol compliance validation failed: {str(e)}")
    
    async def _validate_code_quality(self, server_path: str, results: Dict[str, Any]):
        """Validate code quality metrics."""
        quality = {
            'typescript_compilation': False,
            'eslint_score': 0,
            'test_coverage': 0,
            'documentation_score': 0,
            'type_safety': False,
            'score': 0
        }
        
        try:
            # Check TypeScript compilation
            if await self._check_typescript_compilation(server_path):
                quality['typescript_compilation'] = True
            
            # Run ESLint
            quality['eslint_score'] = await self._run_eslint(server_path)
            
            # Check test coverage
            quality['test_coverage'] = await self._check_test_coverage(server_path)
            
            # Evaluate documentation
            quality['documentation_score'] = await self._evaluate_documentation(server_path)
            
            # Check type safety
            if await self._check_type_safety(server_path):
                quality['type_safety'] = True
            
            # Calculate quality score
            quality['score'] = (
                (quality['typescript_compilation'] * 20) +
                (quality['eslint_score'] * 0.3) +
                (quality['test_coverage'] * 0.3) +
                (quality['documentation_score'] * 0.15) +
                (quality['type_safety'] * 15)
            )
            
            results['code_quality'] = quality
            
        except Exception as e:
            results['errors'].append(f"Code quality validation failed: {str(e)}")
    
    async def _validate_security(self, server_path: str, results: Dict[str, Any]):
        """Validate security aspects."""
        security = {
            'input_validation': False,
            'authentication_handling': False,
            'secret_management': False,
            'dependency_vulnerabilities': 0,
            'secure_communication': False,
            'score': 0
        }
        
        try:
            # Check input validation
            if await self._check_input_validation(server_path):
                security['input_validation'] = True
            
            # Check authentication handling
            if await self._check_authentication_handling(server_path):
                security['authentication_handling'] = True
            
            # Check secret management
            if await self._check_secret_management(server_path):
                security['secret_management'] = True
            
            # Check dependencies for vulnerabilities
            security['dependency_vulnerabilities'] = await self._check_dependency_vulnerabilities(server_path)
            
            # Check secure communication
            if await self._check_secure_communication(server_path):
                security['secure_communication'] = True
            
            # Calculate security score
            vuln_penalty = min(security['dependency_vulnerabilities'] * 5, 50)
            security['score'] = max(0, (
                (security['input_validation'] * 20) +
                (security['authentication_handling'] * 20) +
                (security['secret_management'] * 20) +
                (security['secure_communication'] * 20) +
                20 - vuln_penalty
            ))
            
            results['security_analysis'] = security
            
        except Exception as e:
            results['errors'].append(f"Security validation failed: {str(e)}")
    
    async def _validate_performance(self, server_path: str, results: Dict[str, Any]):
        """Validate performance characteristics."""
        performance = {
            'startup_time': 0,
            'memory_usage': 0,
            'response_time': 0,
            'resource_efficiency': 0,
            'score': 0
        }
        
        try:
            # Measure startup time
            performance['startup_time'] = await self._measure_startup_time(server_path)
            
            # Measure memory usage
            performance['memory_usage'] = await self._measure_memory_usage(server_path)
            
            # Measure response time
            performance['response_time'] = await self._measure_response_time(server_path)
            
            # Calculate resource efficiency
            performance['resource_efficiency'] = await self._calculate_resource_efficiency(performance)
            
            # Calculate performance score
            startup_score = max(0, 100 - (performance['startup_time'] / 100))  # Penalty for slow startup
            memory_score = max(0, 100 - (performance['memory_usage'] / 1024))  # Penalty for high memory
            response_score = max(0, 100 - (performance['response_time'] / 10))  # Penalty for slow response
            
            performance['score'] = (startup_score + memory_score + response_score) / 3
            
            results['performance_metrics'] = performance
            
        except Exception as e:
            results['errors'].append(f"Performance validation failed: {str(e)}")
    
    async def _check_mcp_sdk_import(self, server_path: str) -> bool:
        """Check if MCP SDK is properly imported."""
        try:
            index_file = os.path.join(server_path, 'src', 'index.ts')
            if os.path.exists(index_file):
                content = await self.file_ops.read_file(index_file)
                return '@modelcontextprotocol/sdk' in content
            return False
        except Exception:
            return False
    
    async def _check_stdio_transport(self, server_path: str) -> bool:
        """Check if stdio transport is used."""
        try:
            index_file = os.path.join(server_path, 'src', 'index.ts')
            if os.path.exists(index_file):
                content = await self.file_ops.read_file(index_file)
                return 'StdioServerTransport' in content
            return False
        except Exception:
            return False
    
    async def _check_tool_registration(self, server_path: str) -> bool:
        """Check if tools are registered properly."""
        try:
            files = await self.file_ops.find_files(server_path, '*.ts')
            for file_path in files:
                content = await self.file_ops.read_file(file_path)
                if 'server.registerTool' in content:
                    return True
            return False
        except Exception:
            return False
    
    async def _run_mcp_sdk_validation(self, server_path: str) -> Dict[str, Any]:
        """Run MCP SDK client validation."""
        try:
            # Build the server first
            build_result = await self._build_server(server_path)
            if not build_result['success']:
                return {'success': False, 'error': 'Build failed'}
            
            # Run MCP SDK client test
            test_script = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tests', 'validate-template.js')
            
            if os.path.exists(test_script):
                result = subprocess.run(
                    ['node', test_script, server_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr if result.returncode != 0 else None
                }
            else:
                return {'success': False, 'error': 'Test script not found'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _build_server(self, server_path: str) -> Dict[str, Any]:
        """Build the TypeScript server."""
        try:
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=server_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall validation score."""
        weights = {
            'protocol_compliance': 0.4,
            'code_quality': 0.3,
            'security_analysis': 0.2,
            'performance_metrics': 0.1
        }
        
        total_score = 0
        for category, weight in weights.items():
            if category in results and 'score' in results[category]:
                total_score += results[category]['score'] * weight
        
        # Apply penalties for errors
        error_penalty = min(len(results.get('errors', [])) * 5, 50)
        
        return max(0, total_score - error_penalty)
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Protocol compliance recommendations
        protocol = results.get('protocol_compliance', {})
        if not protocol.get('mcp_sdk_usage', False):
            recommendations.append("Import and use the official MCP SDK")
        if not protocol.get('stdio_transport', False):
            recommendations.append("Use StdioServerTransport for MCP protocol compliance")
        if not protocol.get('tool_registration', False):
            recommendations.append("Register tools using server.registerTool() method")
        
        # Code quality recommendations
        quality = results.get('code_quality', {})
        if not quality.get('typescript_compilation', False):
            recommendations.append("Fix TypeScript compilation errors")
        if quality.get('eslint_score', 0) < 80:
            recommendations.append("Improve code quality by fixing ESLint issues")
        if quality.get('test_coverage', 0) < 70:
            recommendations.append("Increase test coverage to at least 70%")
        
        # Security recommendations
        security = results.get('security_analysis', {})
        if not security.get('input_validation', False):
            recommendations.append("Implement proper input validation for all tools")
        if security.get('dependency_vulnerabilities', 0) > 0:
            recommendations.append("Update dependencies to fix security vulnerabilities")
        
        # Performance recommendations
        performance = results.get('performance_metrics', {})
        if performance.get('startup_time', 0) > 5000:
            recommendations.append("Optimize startup time for better performance")
        if performance.get('memory_usage', 0) > 512:
            recommendations.append("Reduce memory usage for better resource efficiency")
        
        return recommendations
    
    # Placeholder methods for additional validation checks
    async def _check_resource_handling(self, server_path: str) -> bool:
        return True  # Implement actual resource handling check
    
    async def _check_error_handling(self, server_path: str) -> bool:
        return True  # Implement actual error handling check
    
    async def _check_schema_validation(self, server_path: str) -> bool:
        return True  # Implement actual schema validation check
    
    async def _check_typescript_compilation(self, server_path: str) -> bool:
        return True  # Implement actual TypeScript compilation check
    
    async def _run_eslint(self, server_path: str) -> float:
        return 85.0  # Implement actual ESLint execution
    
    async def _check_test_coverage(self, server_path: str) -> float:
        return 75.0  # Implement actual test coverage check
    
    async def _evaluate_documentation(self, server_path: str) -> float:
        return 80.0  # Implement actual documentation evaluation
    
    async def _check_type_safety(self, server_path: str) -> bool:
        return True  # Implement actual type safety check
    
    async def _check_input_validation(self, server_path: str) -> bool:
        return True  # Implement actual input validation check
    
    async def _check_authentication_handling(self, server_path: str) -> bool:
        return True  # Implement actual authentication handling check
    
    async def _check_secret_management(self, server_path: str) -> bool:
        return True  # Implement actual secret management check
    
    async def _check_dependency_vulnerabilities(self, server_path: str) -> int:
        return 0  # Implement actual dependency vulnerability check
    
    async def _check_secure_communication(self, server_path: str) -> bool:
        return True  # Implement actual secure communication check
    
    async def _measure_startup_time(self, server_path: str) -> float:
        return 2000.0  # Implement actual startup time measurement
    
    async def _measure_memory_usage(self, server_path: str) -> float:
        return 256.0  # Implement actual memory usage measurement
    
    async def _measure_response_time(self, server_path: str) -> float:
        return 50.0  # Implement actual response time measurement
    
    async def _calculate_resource_efficiency(self, performance: Dict[str, Any]) -> float:
        return 85.0  # Implement actual resource efficiency calculation
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation task."""
        task_type = task.get('type', 'validate_server')
        
        if task_type == 'validate_server':
            server_path = task.get('server_path', '')
            validation_config = task.get('validation_config', {})
            return await self.validate_mcp_server(server_path, validation_config)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
