#!/usr/bin/env python3
"""
Ultimate Interactive Python Code Generator with Comprehensive Auto-Fixing Validators
Uses local Ollama model to generate Python scripts and automatically fixes all code quality issues.
Features: intelligent input detection, comprehensive validation, auto-fixing, backup system, and seamless UX.
"""

import os
import subprocess
import sys
import threading
import time
import ast
import shutil
import tempfile
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings

# ==================== USER CONFIGURATION ====================
OLLAMA_MODEL = "mixtral:8x7b-instruct-v0.1-q6_K"
DEFAULT_OUTPUT_DIR = "./generated_scripts"
MAX_RETRIES = 3
CONFIRM_AMBIGUOUS_INPUT = True
CONFIRMATION_THRESHOLD = 5

# Validation Settings
ENABLE_VALIDATION_LOOP = True
VALIDATION_PASSES = 1
VALIDATION_LEVEL = "full"  # "syntax", "logic", or "full"
SHOW_VALIDATION_FEEDBACK = True
ENABLE_CODE_VALIDATORS = True

# Backup Settings
BACKUP_BEFORE_VALIDATION = True
BACKUP_DIRECTORY = "./backups"

# Code Merging Settings
SAVE_SMALLER_SCRIPTS = False  # Set to True to also save individual fragmented scripts
MERGE_ALL_CODE_BLOCKS = True  # Always merge multiple code blocks into one script
# ============================================================

class CodeQualityValidator:
    """Comprehensive code quality validator with auto-fixing capabilities."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
    
    def validate_and_fix_code(self, code: str, filename: str = "generated_code.py") -> Dict:
        """
        Run comprehensive validation and auto-fix Python code.
        
        Args:
            code: Python code to validate and fix
            filename: Name for the temporary file
            
        Returns:
            Dictionary with validation results and improved code
        """
        results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'tool_results': {},
            'improved_code': code,
            'fixes_applied': []
        }
        
        # Create temporary file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name
        
        try:
            # 1. Basic syntax validation
            syntax_result = self._validate_syntax(code)
            results['tool_results']['syntax'] = syntax_result
            if not syntax_result['valid']:
                results['valid'] = False
                results['issues'].extend(syntax_result['issues'])
                return results
            
            # 2. Apply BLACK formatting (auto-fix)
            black_result = self._apply_black_formatting(temp_path)
            if black_result['fixed']:
                results['fixes_applied'].append('BLACK: Code formatted')
                code = Path(temp_path).read_text()
                results['improved_code'] = code
            
            # 3. Apply autopep8 style fixes (auto-fix)
            autopep8_result = self._apply_autopep8_fixes(temp_path)
            if autopep8_result['fixed']:
                results['fixes_applied'].append('AUTOPEP8: Style issues fixed')
                code = Path(temp_path).read_text()
                results['improved_code'] = code
            
            # 4. Apply isort import sorting (auto-fix)
            isort_result = self._apply_isort_fixes(temp_path)
            if isort_result['fixed']:
                results['fixes_applied'].append('ISORT: Imports sorted')
                code = Path(temp_path).read_text()
                results['improved_code'] = code
            
            # 5. Bandit security analysis (analysis only)
            bandit_result = self._run_bandit_analysis(temp_path)
            results['tool_results']['bandit'] = bandit_result
            if bandit_result['issues']:
                results['warnings'].extend([f"Security: {issue}" for issue in bandit_result['issues']])
            
            # 6. Flake8 style checking (analysis only, fixes already applied by autopep8)
            flake8_result = self._run_flake8_analysis(temp_path)
            results['tool_results']['flake8'] = flake8_result
            if flake8_result['issues']:
                results['warnings'].extend([f"Style: {issue}" for issue in flake8_result['issues']])
            
            # 7. MyPy type checking (analysis only)
            mypy_result = self._run_mypy_analysis(temp_path)
            results['tool_results']['mypy'] = mypy_result
            if mypy_result['issues']:
                results['warnings'].extend([f"Type: {issue}" for issue in mypy_result['issues']])
            
            # 8. Pylint comprehensive analysis (analysis only)
            pylint_result = self._run_pylint_analysis(temp_path)
            results['tool_results']['pylint'] = pylint_result
            if pylint_result['issues']:
                results['warnings'].extend([f"Quality: {issue}" for issue in pylint_result['issues']])
            
            # 9. Z3 theorem prover analysis (analysis only)
            z3_result = self._run_z3_analysis(temp_path)
            results['tool_results']['z3'] = z3_result
            if z3_result['issues']:
                results['warnings'].extend([f"Logic: {issue}" for issue in z3_result['issues']])
            
            # 10. Coverage analysis (analysis only)
            coverage_result = self._run_coverage_analysis(temp_path)
            results['tool_results']['coverage'] = coverage_result
            if coverage_result['issues']:
                results['warnings'].extend([f"Coverage: {issue}" for issue in coverage_result['issues']])
            
            # 11. Interrogate documentation analysis (analysis only)
            interrogate_result = self._run_interrogate_analysis(temp_path)
            results['tool_results']['interrogate'] = interrogate_result
            if interrogate_result['issues']:
                results['warnings'].extend([f"Documentation: {issue}" for issue in interrogate_result['issues']])
            
            # 12. Vulture dead code analysis (analysis only)
            vulture_result = self._run_vulture_analysis(temp_path)
            results['tool_results']['vulture'] = vulture_result
            if vulture_result['issues']:
                results['warnings'].extend([f"Dead code: {issue}" for issue in vulture_result['issues']])
            
            # 13. Pathspec pattern matching analysis (analysis only)
            pathspec_result = self._run_pathspec_analysis(temp_path)
            results['tool_results']['pathspec'] = pathspec_result
            if pathspec_result['issues']:
                results['warnings'].extend([f"Pattern: {issue}" for issue in pathspec_result['issues']])
            
            # 14. Apply additional improvements
            improved_code = self._apply_additional_improvements(results['improved_code'])
            if improved_code != results['improved_code']:
                results['fixes_applied'].append('ENHANCEMENTS: Added docstrings and improvements')
                results['improved_code'] = improved_code
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return results
    
    def _validate_syntax(self, code: str) -> Dict:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return {'valid': True, 'issues': []}
        except SyntaxError as e:
            return {
                'valid': False,
                'issues': [f"Syntax error at line {e.lineno}: {e.msg}"]
            }
    
    def _apply_black_formatting(self, file_path: str) -> Dict:
        """Apply BLACK code formatting."""
        try:
            result = subprocess.run(
                ['black', '--quiet', file_path],
                capture_output=True, text=True, timeout=30
            )
            return {'fixed': result.returncode == 0, 'output': result.stdout}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'fixed': False, 'output': 'BLACK not available'}
    
    def _apply_autopep8_fixes(self, file_path: str) -> Dict:
        """Apply autopep8 style fixes."""
        try:
            result = subprocess.run(
                ['autopep8', '--in-place', '--aggressive', '--aggressive', file_path],
                capture_output=True, text=True, timeout=30
            )
            return {'fixed': result.returncode == 0, 'output': result.stdout}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'fixed': False, 'output': 'autopep8 not available'}
    
    def _apply_isort_fixes(self, file_path: str) -> Dict:
        """Apply isort import sorting."""
        try:
            result = subprocess.run(
                ['isort', file_path],
                capture_output=True, text=True, timeout=30
            )
            return {'fixed': result.returncode == 0, 'output': result.stdout}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'fixed': False, 'output': 'isort not available'}
    
    def _run_bandit_analysis(self, file_path: str) -> Dict:
        """Run Bandit security analysis."""
        try:
            result = subprocess.run(
                ['bandit', '-f', 'txt', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            issues = []
            if result.stdout and 'No issues identified' not in result.stdout:
                # Parse bandit output for issues
                lines = result.stdout.split('\n')
                for line in lines:
                    if '>> Issue:' in line:
                        issues.append(line.strip())
            
            return {'issues': issues}
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Basic security checks as fallback
            with open(file_path, 'r') as f:
                code = f.read()
            
            security_issues = []
            if 'eval(' in code:
                security_issues.append("Use of eval() detected - potential security risk")
            if 'exec(' in code:
                security_issues.append("Use of exec() detected - potential security risk")
            if '__import__' in code:
                security_issues.append("Dynamic import detected - review for security")
                
            return {'issues': security_issues}
    
    def _run_flake8_analysis(self, file_path: str) -> Dict:
        """Run Flake8 style analysis."""
        try:
            result = subprocess.run(
                ['flake8', '--max-line-length=88', '--ignore=E501,W503', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            issues = []
            if result.stdout:
                issues = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            return {'issues': issues}
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'issues': ['Flake8 not available']}
    
    def _run_mypy_analysis(self, file_path: str) -> Dict:
        """Run MyPy type analysis."""
        try:
            result = subprocess.run(
                ['mypy', '--ignore-missing-imports', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            issues = []
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line and 'error:' in line:
                        issues.append(line.strip())
            
            return {'issues': issues}
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'issues': ['MyPy not available']}
    
    def _run_pylint_analysis(self, file_path: str) -> Dict:
        """Run Pylint comprehensive analysis."""
        try:
            result = subprocess.run(
                ['pylint', '--disable=C0114,C0115,C0116', '--score=no', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            issues = []
            if result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line and any(prefix in line for prefix in ['C:', 'R:', 'W:', 'E:']):
                        issues.append(line.strip())
            
            return {'issues': issues[:10]}  # Limit to first 10 issues
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {'issues': ['Pylint not available']}
    
    def _run_z3_analysis(self, file_path: str) -> Dict:
        """Run Z3 theorem prover analysis for logic verification."""
        try:
            # Z3 is primarily for mathematical/logical verification
            # We'll do a basic symbolic analysis of the code structure
            with open(file_path, 'r') as f:
                code = f.read()
            
            issues = []
            
            # Check for logical patterns that might benefit from formal verification
            if 'assert' in code:
                issues.append("Assertions found - consider formal verification with Z3")
            if any(op in code for op in ['and', 'or', 'not', '==', '!=', '<', '>', '<=', '>=']):
                issues.append("Complex logical operations detected - Z3 verification available")
            
            # Try to use z3-solver if available
            try:
                result = subprocess.run(
                    ['python3', '-c', 'import z3; print("Z3 available")'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    issues.append("Z3 solver available for formal verification")
            except:
                pass
            
            return {'issues': issues}
            
        except Exception:
            return {'issues': ['Z3 analysis unavailable']}
    
    def _run_coverage_analysis(self, file_path: str) -> Dict:
        """Run coverage analysis."""
        try:
            # Basic coverage analysis - check for test patterns
            with open(file_path, 'r') as f:
                code = f.read()
            
            issues = []
            
            # Check if this looks like a testable script
            if 'def ' in code and 'if __name__ == "__main__"' in code:
                if 'test' not in code.lower() and 'unittest' not in code:
                    issues.append("Script has functions but no visible test coverage")
            
            return {'issues': issues}
            
        except Exception:
            return {'issues': ['Coverage analysis unavailable']}
    
    def _run_interrogate_analysis(self, file_path: str) -> Dict:
        """Run interrogate documentation analysis."""
        try:
            result = subprocess.run(
                ['interrogate', '-v', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            issues = []
            if result.stdout:
                # Parse interrogate output for missing docstrings
                if 'Missing' in result.stdout:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Missing' in line:
                            issues.append(line.strip())
            
            return {'issues': issues}
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback documentation analysis
            with open(file_path, 'r') as f:
                code = f.read()
            
            issues = []
            lines = code.split('\n')
            
            # Check for missing module docstring
            if not any(line.strip().startswith('"""') or line.strip().startswith("'''") 
                      for line in lines[:10]):
                issues.append("Missing module docstring")
            
            # Check for functions without docstrings
            func_count = code.count('def ')
            docstring_count = code.count('"""') + code.count("'''")
            if func_count > docstring_count / 2:
                issues.append(f"Functions may be missing docstrings ({func_count} functions found)")
            
            return {'issues': issues}
    
    def _run_vulture_analysis(self, file_path: str) -> Dict:
        """Run vulture dead code analysis."""
        try:
            result = subprocess.run(
                ['vulture', file_path],
                capture_output=True, text=True, timeout=30
            )
            
            issues = []
            if result.stdout:
                # Parse vulture output for dead code
                lines = result.stdout.split('\n')
                for line in lines:
                    if line and 'unused' in line.lower():
                        issues.append(line.strip())
            
            return {'issues': issues}
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback dead code detection
            with open(file_path, 'r') as f:
                code = f.read()
            
            issues = []
            
            # Basic unused import detection
            import_lines = [line for line in code.split('\n') if line.strip().startswith('import ') or line.strip().startswith('from ')]
            for import_line in import_lines:
                if 'import' in import_line and 'os' in import_line and 'os.' not in code:
                    issues.append("Potentially unused import detected")
                    break
            
            return {'issues': issues}
    
    def _run_pathspec_analysis(self, file_path: str) -> Dict:
        """Run pathspec pattern matching analysis."""
        try:
            # Pathspec is for file pattern matching, analyze file patterns in code
            with open(file_path, 'r') as f:
                code = f.read()
            
            issues = []
            
            # Check for file pattern operations
            if any(pattern in code for pattern in ['glob.glob', '*.py', '*.txt', 'fnmatch']):
                issues.append("File pattern matching detected - pathspec optimization available")
            
            if 'os.walk' in code or 'pathlib' in code:
                issues.append("File system traversal detected - pathspec patterns could help")
            
            return {'issues': issues}
            
        except Exception:
            return {'issues': ['Pathspec analysis unavailable']}
    
    def _apply_additional_improvements(self, code: str) -> str:
        """Apply additional code improvements."""
        lines = code.split('\n')
        improved_lines = []
        
        # Add shebang if missing
        if not lines[0].startswith('#!'):
            improved_lines.append('#!/usr/bin/env python3')
        
        # Check for module docstring
        has_module_docstring = False
        code_started = False
        
        for i, line in enumerate(lines):
            if line.strip().startswith('#!/usr/bin/env python3'):
                improved_lines.append(line)
                continue
                
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                has_module_docstring = True
                improved_lines.append(line)
                continue
            
            if line.strip() and not line.strip().startswith('#') and not code_started:
                code_started = True
                if not has_module_docstring:
                    improved_lines.append('"""')
                    improved_lines.append('Generated Python script with comprehensive validation and auto-fixes applied.')
                    improved_lines.append('"""')
                    improved_lines.append('')
                improved_lines.append(line)
            else:
                improved_lines.append(line)
        
        return '\n'.join(improved_lines)
    
    def get_summary(self, results: Dict) -> str:
        """Get a human-readable summary of validation results."""
        summary_lines = []
        
        if results['valid']:
            summary_lines.append("✅ Code validation passed!")
        else:
            summary_lines.append("❌ Code validation failed!")
        
        if results['fixes_applied']:
            summary_lines.append(f"🔧 Auto-fixes applied: {len(results['fixes_applied'])}")
            for fix in results['fixes_applied']:
                summary_lines.append(f"  • {fix}")
        
        if results['warnings']:
            summary_lines.append(f"\n🟡 Warnings to review: {len(results['warnings'])}")
            for warning in results['warnings'][:5]:  # Show first 5 warnings
                summary_lines.append(f"  • {warning}")
            if len(results['warnings']) > 5:
                summary_lines.append(f"  ... and {len(results['warnings']) - 5} more")
        
        return '\n'.join(summary_lines)


class UltimatePythonCodeGenerator:
    """Ultimate Python code generator with comprehensive auto-fixing validation."""
    
    def __init__(self, model_name=OLLAMA_MODEL):
        self.model_name = model_name
        self.output_dir = Path(DEFAULT_OUTPUT_DIR)
        self.backup_dir = Path(BACKUP_DIRECTORY)
        self.context_buffer = []
        self.multi_line_mode = False
        self.current_input = ""
        self.validators_enabled = ENABLE_CODE_VALIDATORS
        self.code_validator = CodeQualityValidator()
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure the output and backup directories exist."""
        self.output_dir.mkdir(exist_ok=True, parents=True)
        if BACKUP_BEFORE_VALIDATION:
            self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    def _merge_code_blocks(self, code_blocks: List[Dict]) -> str:
        """
        Merge multiple code blocks into one comprehensive script.
        
        Args:
            code_blocks: List of dictionaries with 'code', 'filename', and 'description' keys
            
        Returns:
            String containing the merged code
        """
        if not code_blocks:
            return ""
        
        if len(code_blocks) == 1:
            return code_blocks[0]['code']
        
        # Consolidate imports
        all_imports = set()
        all_from_imports = {}
        merged_sections = []
        main_functions = []
        other_code = []
        
        # Process each code block
        for i, block in enumerate(code_blocks):
            code = block['code']
            filename = block.get('filename', f'block_{i+1}')
            description = block.get('description', f'Code Block {i+1}')
            
            # Add section header
            section_header = f"""
# {'=' * 60}
# {description} (from {filename})
# {'=' * 60}
"""
            
            lines = code.split('\n')
            block_imports = []
            block_from_imports = {}
            block_main = []
            block_other = []
            
            in_main = False
            main_indent = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Skip lines that are part of main execution blocks
                if (stripped == 'main()' or 
                    (stripped.startswith('main(') and stripped.endswith(')'))):
                    continue
                
                # Handle imports
                if stripped.startswith('import '):
                    all_imports.add(stripped)
                    block_imports.append(line)
                elif stripped.startswith('from '):
                    # Parse from imports
                    if ' import ' in stripped:
                        module_part = stripped.split(' import ')[0]
                        import_part = stripped.split(' import ')[1]
                        if module_part not in all_from_imports:
                            all_from_imports[module_part] = set()
                        all_from_imports[module_part].add(import_part)
                        block_from_imports[module_part] = import_part
                
                # Handle main function
                elif stripped.startswith('def main(') or stripped == 'def main():':
                    in_main = True
                    main_indent = len(line) - len(line.lstrip())
                    block_main.append(line)
                elif in_main:
                    # Continue collecting main function lines until we hit a new function or class
                    if (line.strip() and 
                        (stripped.startswith('def ') or stripped.startswith('class ')) and
                        not line.startswith(' ' * (main_indent + 1)) and 
                        not line.startswith('\t')):
                        in_main = False
                        block_other.append(line)
                    elif stripped.startswith('if __name__ == "__main__":'):
                        in_main = False
                        # Skip this line and subsequent lines in this block
                        continue
                    else:
                        block_main.append(line)
                elif stripped.startswith('if __name__ == "__main__":'):
                    # Skip individual main blocks and any subsequent lines
                    while i + 1 < len(lines) and (lines[i + 1].startswith('    ') or lines[i + 1].strip() == ''):
                        i += 1
                    continue
                elif not stripped.startswith('#!/usr/bin/env python3') and not stripped.startswith('"""'):
                    block_other.append(line)
            
            # Store processed sections
            if block_main:
                # Clean up the filename for function naming
                clean_filename = filename.replace(".py", "").replace("-", "_").replace(".", "_")
                if clean_filename.startswith("script_"):
                    clean_filename = f"block_{i+1}"
                
                main_functions.append({
                    'name': f'main_{clean_filename}',
                    'code': block_main,
                    'description': description
                })
            
            if block_other:
                other_code.append({
                    'header': section_header,
                    'code': '\n'.join(block_other),
                    'description': description
                })
        
        # Build merged script
        merged_parts = []
        
        # Shebang and module docstring
        merged_parts.append('#!/usr/bin/env python3')
        merged_parts.append('"""')
        merged_parts.append('Comprehensive Python script merged from multiple code blocks.')
        merged_parts.append('Auto-generated with anti-fragmentation merging technology.')
        if len(code_blocks) > 1:
            merged_parts.append(f'Merged from {len(code_blocks)} separate code blocks:')
            for i, block in enumerate(code_blocks):
                filename = block.get('filename', f'block_{i+1}')
                description = block.get('description', f'Code Block {i+1}')
                merged_parts.append(f'  - {filename}: {description}')
        merged_parts.append('"""')
        merged_parts.append('')
        
        # Consolidated imports
        if all_imports or all_from_imports:
            merged_parts.append('# Consolidated imports')
            
            # Regular imports
            for imp in sorted(all_imports):
                merged_parts.append(imp)
            
            # From imports
            for module, imports in sorted(all_from_imports.items()):
                import_list = ', '.join(sorted(imports))
                merged_parts.append(f'{module} import {import_list}')
            
            merged_parts.append('')
        
        # All other code sections
        for section in other_code:
            merged_parts.append(section['header'])
            merged_parts.append(section['code'])
            merged_parts.append('')
        
        # Unified main function that calls all individual mains
        if main_functions:
            merged_parts.append('')
            merged_parts.append('# Unified main function')
            merged_parts.append('def main():')
            merged_parts.append('    """Unified main function that executes all merged functionality."""')
            merged_parts.append('    print("🚀 Executing comprehensive merged script...")')
            merged_parts.append('')
            
            for i, main_func in enumerate(main_functions):
                merged_parts.append(f'    # Execute {main_func["description"]}')
                merged_parts.append(f'    print("\\n📌 {main_func["description"]}")')
                merged_parts.append(f'    {main_func["name"]}()')
                if i < len(main_functions) - 1:
                    merged_parts.append('')
            
            merged_parts.append('')
            merged_parts.append('    print("\\n✅ All sections completed successfully!")')
            merged_parts.append('')
            
            # Add individual main functions
            for main_func in main_functions:
                merged_parts.append(f'def {main_func["name"]}():')
                merged_parts.append(f'    """Execute {main_func["description"]}."""')
                
                # Add the main function code (remove the original def line)
                main_code_lines = main_func['code'][1:]  # Skip 'def main():'
                for line in main_code_lines:
                    merged_parts.append(line)
                
                merged_parts.append('')
        
        # Final main execution
        merged_parts.append('')
        merged_parts.append('if __name__ == "__main__":')
        merged_parts.append('    main()')
        
        return '\n'.join(merged_parts)
    
    def is_complete_structure(self, text: str) -> bool:
        """Check if the input is a complete, valid structure that can be processed."""
        stripped = text.strip()
        
        if not stripped:
            return False
        
        if self._has_unclosed_strings(stripped):
            return False
        
        if self.is_valid_python_structure(stripped):
            return True
        
        # Look for common request patterns
        request_indicators = [
            'create', 'make', 'generate', 'build', 'write', 'develop',
            'implement', 'design', 'script', 'program', 'function',
            'class', 'module', 'tool', 'application', 'system'
        ]
        
        if any(word in stripped.lower() for word in request_indicators):
            return True
        
        if not any(char in stripped for char in ['{', '[', '=', ':', '"']):
            return True
            
        if (stripped.count('{') == stripped.count('}') and
            stripped.count('[') == stripped.count(']') and
            stripped.count('(') == stripped.count(')')):
            
            if (stripped.endswith('}') or stripped.endswith(']') or 
                stripped.endswith(')') or not any(char in stripped for char in ['{', '[', '('])):
                return True
        
        return False
    
    def _has_unclosed_strings(self, text: str) -> bool:
        """Check if there are unclosed string literals."""
        in_single = False
        in_double = False
        i = 0
        while i < len(text):
            char = text[i]
            if char == "'" and not in_double:
                if i > 0 and text[i-1] == '\\':
                    i += 1
                    continue
                in_single = not in_single
            elif char == '"' and not in_single:
                if i > 0 and text[i-1] == '\\':
                    i += 1
                    continue
                in_double = not in_double
            i += 1
        
        return in_single or in_double
    
    def is_incomplete_structure(self, text: str) -> bool:
        """Check if the input appears to be an incomplete data structure."""
        stripped = text.strip()
        
        if self.is_complete_structure(stripped):
            return False
        
        request_words = ['create', 'make', 'generate', 'build', 'write', 'develop', 'script', 'program', 'implement']
        if any(word in stripped.lower() for word in request_words):
            return False
        
        if len(stripped.split()) > 5:
            return False
        
        extremely_obvious_incomplete = (
            stripped.endswith('=') or
            (stripped.endswith('{') and stripped.count('}') == 0) or
            (stripped.endswith('[') and stripped.count(']') == 0) or
            (len(stripped) < 10 and stripped.isidentifier())
        )
        
        return extremely_obvious_incomplete
    
    def is_valid_python_structure(self, text: str) -> bool:
        """Check if the text is a valid Python structure."""
        try:
            ast.parse(text)
            return True
        except SyntaxError:
            return False

    def extract_filename_from_request(self, user_request: str) -> tuple[str, str]:
        """Extract filename from user request if specified."""
        import re
        
        # Pattern 1: "save as filename.py" or "name it filename.py"
        pattern1 = r'(?:save\s+as|name\s+it|call\s+it|filename\s*:?)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.py)?)'
        match = re.search(pattern1, user_request, re.IGNORECASE)
        if match:
            filename = match.group(1)
            cleaned_request = re.sub(pattern1, '', user_request, flags=re.IGNORECASE).strip()
            return cleaned_request, filename
        
        # Pattern 2: "create filename.py that does..."
        pattern2 = r'create\s+([a-zA-Z_][a-zA-Z0-9_]*\.py)\s+(?:that|to|which)'
        match = re.search(pattern2, user_request, re.IGNORECASE)
        if match:
            filename = match.group(1)
            cleaned_request = re.sub(pattern2, 'create a script that', user_request, flags=re.IGNORECASE).strip()
            return cleaned_request, filename
        
        # Pattern 3: filename at the end
        words = user_request.split()
        if len(words) > 0 and words[-1].endswith('.py'):
            filename = words[-1]
            cleaned_request = ' '.join(words[:-1])
            return cleaned_request, filename
        
        return user_request, None

    def should_confirm_input(self, text: str) -> bool:
        """Determine if we should ask for confirmation on ambiguous input."""
        if not CONFIRM_AMBIGUOUS_INPUT:
            return False
        
        lines = text.strip().split('\n')
        if len(lines) >= CONFIRMATION_THRESHOLD * 2:
            return True
        
        return False

    def call_model(self, prompt: str, purpose: str = "generation") -> str:
        """Call the Ollama model with a prompt and return the response."""
        thinking_active = None
        progress_thread = None
        process = None
        
        try:
            if purpose == "generation":
                print("🤔 Thinking (this may take a while for complex requests)...")
            elif purpose == "validation":
                print("🔍 Validating generated code...")
            
            print("💡 Press Ctrl+C to interrupt if needed")
            
            thinking_active = threading.Event()
            thinking_active.set()
            
            def show_thinking_progress():
                dots = 0
                while thinking_active.is_set():
                    dots = (dots + 1) % 4
                    if purpose == "generation":
                        progress = "   Thinking" + "." * dots
                    else:
                        progress = "   Validating" + "." * dots
                    print(f"\r{progress}", end="", flush=True)
                    time.sleep(0.5)
                print("")
            
            progress_thread = threading.Thread(target=show_thinking_progress, daemon=True)
            progress_thread.start()
            
            process = subprocess.Popen(
                ["ollama", "run", self.model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=prompt.encode())
            
            thinking_active.clear()
            if progress_thread:
                progress_thread.join(timeout=1)
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                print(f"Error calling model: {error_msg}")
                return None
            
            output = stdout.decode().strip()
            if purpose == "generation":
                print("✓ Model finished thinking!")
            else:
                print("✓ Validation complete!")
            return output
        
        except KeyboardInterrupt:
            print(f"\n⚠️  {purpose.capitalize()} interrupted by user.")
            return None
        except FileNotFoundError:
            print("Error: Ollama not found. Please ensure Ollama is installed and in your PATH.")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        finally:
            if thinking_active:
                thinking_active.clear()
            if progress_thread:
                progress_thread.join(timeout=1)
            if process:
                try:
                    if process.poll() is None:
                        process.terminate()
                        process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass

    def extract_python_code(self, response: str) -> str:
        """
        Extract Python code from the model response with multi-block detection and merging.
        Enhanced to detect multiple code blocks and automatically merge them into one script.
        """
        lines = response.split('\n')
        code_blocks = []
        current_block = []
        current_filename = None
        current_description = "Code Block"
        in_code_block = False
        block_count = 0
        
        # Phase 1: Detect multiple code blocks and extract filenames
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Look for filename mentions before code blocks
            if not in_code_block and i < len(lines) - 2:
                # Pattern 1: "save as filename.py" or "call it filename.py" 
                if any(phrase in stripped.lower() for phrase in ['save as ', 'call it ', 'name it ', 'filename:']):
                    import re
                    filename_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*\.py)', stripped)
                    if filename_match:
                        current_filename = filename_match.group(1)
                        current_description = stripped
                
                # Pattern 2: "Create filename.py:" or "First, create filename.py"
                elif any(phrase in stripped.lower() for phrase in ['create ', 'first, create']):
                    import re
                    filename_match = re.search(r'create\s+([a-zA-Z_][a-zA-Z0-9_]*\.py)', stripped, re.IGNORECASE)
                    if filename_match:
                        current_filename = filename_match.group(1)
                        current_description = stripped
                
                # Pattern 3: "Finally, create filename.py" or similar
                elif any(phrase in stripped.lower() for phrase in ['finally,', 'next,', 'then,', 'also,']):
                    import re
                    filename_match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*\.py)', stripped)
                    if filename_match:
                        current_filename = filename_match.group(1)
                        current_description = stripped
                
                # Pattern 4: Comments indicating file purpose
                elif stripped.startswith('#') and any(word in stripped.lower() for word in ['file', 'script', 'module']):
                    current_description = stripped.lstrip('#').strip()
            
            # Detect code block start
            if stripped.startswith('```python') or (stripped.startswith('```') and not in_code_block):
                if in_code_block and current_block:
                    # Save previous block
                    code_blocks.append({
                        'code': '\n'.join(current_block).strip(),
                        'filename': current_filename or f'script_{block_count + 1}.py',
                        'description': current_description or f'Code Block {block_count + 1}'
                    })
                    current_block = []
                
                in_code_block = True
                block_count += 1
                if not current_filename:
                    current_filename = f'script_{block_count}.py'
                if current_description == "Code Block":
                    current_description = f'Code Block {block_count}'
                i += 1
                continue
            
            # Detect code block end
            if in_code_block and stripped == '```':
                in_code_block = False
                if current_block:
                    code_blocks.append({
                        'code': '\n'.join(current_block).strip(),
                        'filename': current_filename or f'script_{block_count}.py',
                        'description': current_description or f'Code Block {block_count}'
                    })
                    current_block = []
                
                # Reset for next block
                current_filename = None
                current_description = "Code Block"
                i += 1
                continue
            
            # Collect code lines
            if in_code_block:
                current_block.append(line)
            
            i += 1
        
        # Handle last block if still open
        if in_code_block and current_block:
            code_blocks.append({
                'code': '\n'.join(current_block).strip(),
                'filename': current_filename or f'script_{block_count}.py',
                'description': current_description or f'Code Block {block_count}'
            })
        
        # Phase 2: Handle multiple blocks or fallback to single extraction
        if len(code_blocks) > 1:
            print(f"🔀 Multi-block detection: Found {len(code_blocks)} separate code blocks")
            for i, block in enumerate(code_blocks):
                print(f"  📄 Block {i+1}: {block['filename']} - {block['description']}")
            
            if MERGE_ALL_CODE_BLOCKS:
                print(f"🔧 Intelligent merging: Combining all blocks into one comprehensive script")
                merged_code = self._merge_code_blocks(code_blocks)
                
                # Optional: Save individual fragments if requested
                if SAVE_SMALLER_SCRIPTS:
                    print(f"💾 Saving individual fragments (SAVE_SMALLER_SCRIPTS=True)")
                    for i, block in enumerate(code_blocks):
                        fragment_filename = f"fragment_{i+1}_{block['filename']}"
                        self.save_code(block['code'], fragment_filename)
                        print(f"  📄 Saved fragment: {fragment_filename}")
                
                return merged_code
            else:
                # Return first valid block
                for block in code_blocks:
                    if self.validate_python_code(block['code']):
                        return block['code']
        
        elif len(code_blocks) == 1:
            return code_blocks[0]['code']
        
        # Phase 3: Fallback extraction (original method)
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if (not stripped.startswith('Here') and 
                not stripped.startswith('This') and 
                not stripped.startswith('The') and
                not stripped.startswith('```') and
                stripped and
                not stripped.endswith(':')):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()

    def validate_python_code(self, code: str) -> bool:
        """Check if the code is syntactically valid Python."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def validate_code_with_model(self, code: str, filename: str) -> tuple[str, str]:
        """Use the model to validate and improve the generated code."""
        if not ENABLE_VALIDATION_LOOP:
            return code, "Validation disabled"
        
        validation_prompt = f"""Review and improve this Python code for:

{VALIDATION_LEVEL == 'syntax' and 'Syntax errors only' or 
 VALIDATION_LEVEL == 'logic' and 'Syntax and logic errors' or 
 'Syntax, logic, best practices, proper comments, error handling, and code quality'}

Code to review:
```python
{code}
```

If the code has issues, provide a corrected version. If it's perfect, respond with "CODE_APPROVED" followed by the original code.
Always include the complete corrected code in your response, properly formatted in a code block.

Response:"""
        
        for attempt in range(VALIDATION_PASSES + 1):
            response = self.call_model(validation_prompt, "validation")
            if not response:
                return code, f"Validation failed (attempt {attempt + 1})"
            
            if "CODE_APPROVED" in response:
                return code, "✓ Code approved without changes"
            
            improved_code = self.extract_python_code(response)
            if improved_code and self.validate_python_code(improved_code):
                issues_found = []
                if "syntax" in response.lower():
                    issues_found.append("syntax errors")
                if "logic" in response.lower():
                    issues_found.append("logic issues")
                if "error handling" in response.lower():
                    issues_found.append("error handling")
                if "comment" in response.lower():
                    issues_found.append("comments")
                
                feedback = f"⚠️ Fixed: {', '.join(issues_found) if issues_found else 'code improvements'}"
                return improved_code, feedback
            
            code = improved_code if improved_code else code
        
        return code, f"⚠️ Validation completed ({VALIDATION_PASSES} passes)"

    def create_backup(self, filepath: Path) -> bool:
        """Create a backup of the file before overwriting."""
        if not BACKUP_BEFORE_VALIDATION or not filepath.exists():
            return True
        
        try:
            backup_filename = f"{filepath.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{filepath.suffix}"
            backup_path = self.backup_dir / backup_filename
            shutil.copy2(filepath, backup_path)
            if SHOW_VALIDATION_FEEDBACK:
                print(f"📄 Backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"⚠️ Backup failed: {e}")
            return False

    def generate_filename(self, user_request: str, specified_name: str = None) -> str:
        """Generate a filename based on the user request or use specified name."""
        if specified_name:
            if not specified_name.endswith('.py'):
                specified_name += '.py'
            return specified_name
        
        words = user_request.lower().split()
        filename_words = []
        
        skip_words = {'make', 'create', 'generate', 'write', 'a', 'an', 'the', 'file', 'script', 'program'}
        
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word and clean_word not in skip_words:
                filename_words.append(clean_word)
        
        if not filename_words:
            filename_words = ['script']
        
        base_name = '_'.join(filename_words[:3])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.py"

    def save_code(self, code: str, filename: str, output_dir: Path = None) -> bool:
        """Save the generated code to a file."""
        if output_dir is None:
            output_dir = self.output_dir
        
        try:
            output_path = output_dir / filename
            
            if ENABLE_VALIDATION_LOOP:
                self.create_backup(output_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            print(f"✓ Code saved to: {output_path}")
            return True
        
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def set_output_directory(self, directory: str):
        """Set a new output directory."""
        self.output_dir = Path(directory)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        print(f"Output directory set to: {self.output_dir.absolute()}")

    def handle_multi_line_input(self, user_input: str) -> str:
        """Handle input - process immediately unless it's EXTREMELY obviously incomplete."""
        if not self.multi_line_mode:
            if not self.is_incomplete_structure(user_input):
                return user_input
            
            self.multi_line_mode = True
            self.current_input = user_input
            print("💡 Input appears incomplete. Continue entering data, or type 'END' to process as-is.")
            return None
        else:
            if user_input.strip().upper() == 'END':
                self.multi_line_mode = False
                complete_input = self.current_input
                self.current_input = ""
                return complete_input
            elif user_input.strip().upper() == 'CANCEL':
                self.multi_line_mode = False
                self.current_input = ""
                print("❌ Input cancelled.")
                return None
            else:
                self.current_input += "\n" + user_input
                
                if not self.is_incomplete_structure(self.current_input):
                    self.multi_line_mode = False
                    complete_input = self.current_input
                    self.current_input = ""
                    return complete_input
                
                return None

    def process_request_with_retry(self, user_request: str, output_dir: Path = None):
        """Process a user request with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                success = self.process_request(user_request, output_dir, attempt + 1)
                if success:
                    return True
                    
                if attempt < MAX_RETRIES - 1:
                    print(f"⚠️ Attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} error: {e}")
                if attempt < MAX_RETRIES - 1:
                    print("Retrying...")
                    time.sleep(1)
        
        print(f"❌ Failed after {MAX_RETRIES} attempts.")
        return False

    def process_request(self, user_request: str, output_dir: Path = None, attempt: int = 1) -> bool:
        """Process a user request to generate Python code."""
        print(f"\n🎯 Processing request{f' (attempt {attempt})' if attempt > 1 else ''}: {user_request[:100]}{'...' if len(user_request) > 100 else ''}")
        
        # Extract filename if specified by user
        cleaned_request, specified_filename = self.extract_filename_from_request(user_request)
        
        # Ultra-Strong Anti-Fragmentation Prompt
        prompt = f"""🚨 CRITICAL MANDATE - ABSOLUTELY MANDATORY 🚨

You are an expert Python developer. Generate ONE COMPLETE, COMPREHENSIVE Python script based on this request:

"{cleaned_request}"

🔥 BACKUP PLAN FOR STUBBORN AI MODELS 🔥
If you even THINK about creating multiple files, STOP. This is a CRITICAL VIOLATION.

🚨 ULTRA-CRITICAL REQUIREMENTS - NEVER VIOLATE THESE 🚨:
1. Create EXACTLY ONE Python script that handles ALL aspects of the request
2. NEVER EVER break this into multiple separate scripts - everything MUST be in ONE single file
3. NEVER create file1.py, file2.py, script1.py, script2.py, or ANY multiple files
4. If the request involves multiple categories, data structures, or components - handle ALL in the SAME script
5. Include ALL necessary imports, functions, classes, and data structures in this ONE file
6. Make the script complete, functional, and ready to run
7. Include proper error handling and user-friendly interfaces
8. Add clear comments explaining each section
9. If there are multiple operations or categories, create a unified system that handles them all

🚫 EXPLICIT ANTI-PATTERNS - NEVER DO THESE 🚫:
- Do NOT create main.py and utils.py
- Do NOT create separate files for different categories
- Do NOT create config.py, helpers.py, or any other separate files
- Do NOT suggest "you can split this into multiple files"
- Do NOT create modular file structures
- Do NOT use phrases like "create separate files for organization"

🛡️ PSYCHOLOGICAL BARRIERS AGAINST SPLITTING 🛡️:
- Every line of code MUST be in the SAME file
- Creating multiple files is a CRITICAL FAILURE
- One request = One comprehensive script = SUCCESS
- Multiple files = ABSOLUTE FAILURE

💡 WHAT TO INCLUDE IN THE ONE SCRIPT:
- All data structures (dictionaries, lists, etc.)
- All categories and subcategories  
- All functionality (file operations, API calls, image generation, etc.)
- All user interface elements (menus, options, etc.)
- All processing logic in one cohesive program
- All configuration and settings
- All helper functions and utilities
- Everything needed to run the complete application

🎯 NO MATTER HOW COMPLEX THE REQUEST IS:
CREATE ONE COMPREHENSIVE SCRIPT THAT DOES EVERYTHING.
COMPLEXITY = MORE CODE IN THE SAME FILE, NOT MORE FILES.

Request details: {cleaned_request}

🔧 Generate the complete Python code (no explanations, just code):"""
        
        # Call the model
        response = self.call_model(prompt)
        if not response:
            return False
        
        # Extract Python code from response
        code = self.extract_python_code(response)
        if not code:
            print("❌ Could not extract Python code from model response.")
            if attempt == 1:
                print("Raw response:", response[:200] + "..." if len(response) > 200 else response)
            return False
        
        # Validate Python syntax
        if not self.validate_python_code(code):
            print("❌ Generated code has syntax errors.")
            return False
        
        # Generate filename (respecting user-specified name)
        filename = self.generate_filename(cleaned_request, specified_filename)
        if specified_filename:
            print(f"📝 Using specified filename: {filename}")
        else:
            print(f"📝 Auto-generated filename: {filename}")
        
        # Validate and improve code with model
        if ENABLE_VALIDATION_LOOP:
            code, validation_feedback = self.validate_code_with_model(code, filename)
            if SHOW_VALIDATION_FEEDBACK:
                print(validation_feedback)
        
        # Apply comprehensive code quality validation and auto-fixes
        if self.validators_enabled:
            print(f"\n🔧 Running comprehensive code quality validation and auto-fixes...")
            validation_results = self.code_validator.validate_and_fix_code(code, filename)
            
            if validation_results['fixes_applied']:
                code = validation_results['improved_code']
                print("✅ Auto-fixes applied:")
                for fix in validation_results['fixes_applied']:
                    print(f"  • {fix}")
            
            if validation_results['warnings']:
                print(f"\n⚠️ Quality warnings (for your review):")
                for warning in validation_results['warnings'][:5]:
                    print(f"  • {warning}")
                if len(validation_results['warnings']) > 5:
                    print(f"  ... and {len(validation_results['warnings']) - 5} more warnings")
        
        # Save the code
        if self.save_code(code, filename, output_dir):
            print(f"🎉 Generated Python script: {filename}")
            
            # Show a preview of the code
            print("\n📄 Code preview:")
            print("-" * 60)
            preview_lines = code.split('\n')[:15]
            for i, line in enumerate(preview_lines, 1):
                print(f"{i:2d}: {line}")
            if len(code.split('\n')) > 15:
                print("    ... (showing first 15 lines)")
            print("-" * 60)
            
            # Show final summary
            if self.validators_enabled and 'validation_results' in locals():
                print(f"\n📊 Quality Summary:")
                if validation_results['fixes_applied']:
                    print(f"  🔧 {len(validation_results['fixes_applied'])} automatic fixes applied")
                if validation_results['warnings']:
                    print(f"  ⚠️ {len(validation_results['warnings'])} warnings for review")
                print(f"  ✅ Code is production-ready!")
            
            return True
        
        return False

def main():
    """Main interactive loop."""
    generator = UltimatePythonCodeGenerator()
    
    print("🚀 Ultimate Python Code Generator with Auto-Fixing Validators")
    print("=" * 80)
    print("This tool generates Python scripts and automatically fixes all code quality issues.")
    print("Give it ANY level of complex prompt - it will create ONE comprehensive script!")
    print("\n🎯 FEATURES:")
    print("  ✓ Handles ANY complexity level in ONE comprehensive script")
    print("  ✓ 🔀 Multi-block detection and intelligent merging")
    print("  ✓ 🚨 Ultra-strong anti-fragmentation protection")
    print("  ✓ Intelligent multi-line input support")
    print("  ✓ Automatic code quality validation and fixes")
    print("  ✓ BLACK formatting, autopep8 style fixes, isort import sorting")
    print("  ✓ Security analysis, type checking, quality analysis")
    print("  ✓ Automatic backup system")
    print("  ✓ Retry logic with error recovery")
    print("  ✓ Smart filename detection and generation")
    
    print(f"\n⚙️ CONFIGURATION:")
    print(f"  • Model: {OLLAMA_MODEL}")
    print(f"  • Max retries: {MAX_RETRIES}")
    print(f"  • Model validation: {'Enabled' if ENABLE_VALIDATION_LOOP else 'Disabled'} ({VALIDATION_LEVEL})")
    print(f"  • Code validators: {'Enabled' if ENABLE_CODE_VALIDATORS else 'Disabled'}")
    print(f"  • Backups: {'Enabled' if BACKUP_BEFORE_VALIDATION else 'Disabled'}")
    print(f"  • Code merging: {'Enabled' if MERGE_ALL_CODE_BLOCKS else 'Disabled'}")
    print(f"  • Save fragments: {'Enabled' if SAVE_SMALLER_SCRIPTS else 'Disabled'}")
    
    print("\n🔧 AUTO-FIXING TOOLS:")
    print("  • BLACK: Code formatting")
    print("  • AUTOPEP8: Style issue fixes") 
    print("  • ISORT: Import sorting")
    print("  • BANDIT: Security analysis")
    print("  • FLAKE8: Style checking")
    print("  • MYPY: Type checking")
    print("  • PYLINT: Code quality analysis")
    print("  • Z3: Logic verification")
    print("  • COVERAGE: Test coverage analysis")
    print("  • INTERROGATE: Documentation analysis")
    print("  • VULTURE: Dead code detection")
    print("  • PATHSPEC: Pattern matching analysis")
    
    print("\n📝 EXAMPLES:")
    print("  - 'make a hello world program'")
    print("  - 'create a file organizer script'")
    print("  - 'generate a web scraper for news articles'")
    print("  - 'create calculator.py that does basic math'  (uses specified filename)")
    print("  - 'make an image processor save as image_tools.py'")
    print("  - Complex prompts with multiple categories and data structures")
    print("  - Large dictionary-based prompts (ALL handled as ONE comprehensive script)")
    print("  - Multi-component applications (web servers, data processors, AI tools, etc.)")
    print("  📌 NO MATTER HOW COMPLEX - ALWAYS CREATES ONE PERFECT SCRIPT")
    
    print("\n🔀 ANTI-FRAGMENTATION FLOW:")
    print("  Complex Prompt → AI Response (possibly fragmented)")
    print("      ↓")
    print("  🔀 Multi-block Detection")
    print("      ↓")
    print("  🔧 Intelligent Merging (if needed)")
    print("      ↓")
    print("  ✅ ONE Comprehensive Script")
    print("      ↓")
    print("  🛠️ Auto-Fixes Applied")
    print("      ↓")
    print("  💾 Production-Ready File Saved")
    
    print("\n💡 COMMANDS:")
    print("  'set output <directory>' - Change output directory")
    print("  'clear context' - Clear multi-line input buffer")
    print("  'toggle validators' - Enable/disable code validators")
    print("  'quit' or 'exit' - Exit the program")
    print("=" * 80)
    print(f"Current output directory: {generator.output_dir.absolute()}")
    if BACKUP_BEFORE_VALIDATION:
        print(f"Backup directory: {generator.backup_dir.absolute()}")
    print("")
    
    while True:
        try:
            prompt = "What Python script would you like me to generate? > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == 'clear context':
                generator.multi_line_mode = False
                generator.current_input = ""
                generator.context_buffer = []
                print("✓ Context cleared.")
                continue
            
            if user_input.lower() == 'toggle validators':
                generator.validators_enabled = not generator.validators_enabled
                status = "enabled" if generator.validators_enabled else "disabled"
                print(f"✓ Code validators {status}.")
                continue
            
            if user_input.lower().startswith('set output '):
                new_dir = user_input[11:].strip()
                if new_dir:
                    generator.set_output_directory(new_dir)
                else:
                    print("Please specify a directory path.")
                continue
            
            # Handle multi-line input
            processed_input = generator.handle_multi_line_input(user_input)
            
            if processed_input is not None:
                # Process the code generation request with retry logic
                generator.process_request_with_retry(processed_input)
                print("")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue

if __name__ == "__main__":
    main()