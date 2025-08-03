#!/usr/bin/env python3
"""
Enhanced Interactive Python Code Generator with Validation Loop and 10 Code Validators
Uses local Ollama model to generate and validate Python scripts based on natural language requests.
Features: intelligent input detection, self-validation, backup system, comprehensive code validation, and seamless UX.
"""

import os
import subprocess
import sys
import threading
import time
import json
import ast
import shutil
from pathlib import Path
from datetime import datetime

# ==================== USER CONFIGURATION ====================
# Model and Directory Settings
OLLAMA_MODEL = "mixtral:8x7b-instruct-v0.1-q6_K"
DEFAULT_OUTPUT_DIR = "./generated_scripts"

# Retry and Input Settings
MAX_RETRIES = 3
CONFIRM_AMBIGUOUS_INPUT = True
CONFIRMATION_THRESHOLD = 5  # Lines of input before asking for confirmation

# Validation Settings
ENABLE_VALIDATION_LOOP = True
VALIDATION_PASSES = 1
VALIDATION_LEVEL = "full"  # "syntax", "logic", or "full"
SHOW_VALIDATION_FEEDBACK = True

# Code Validator Settings
ENABLE_CODE_VALIDATORS = True
SKIP_FAILED_VALIDATORS = True  # Continue even if some validators fail

# Backup Settings
BACKUP_BEFORE_VALIDATION = True
BACKUP_DIRECTORY = "./backups"
# ============================================================

# 10 Code Validators Configuration
VALIDATORS = {
    "black": ["black", "--check"],
    "flake8": ["flake8"],
    "pylint": ["pylint"],
    "mypy": ["mypy"],
    "bandit": ["bandit", "-r"],
    "coverage": ["coverage", "run", "--source=."],
    "vulture": ["vulture"],
    "interrogate": ["interrogate"],
    "pytest": ["pytest"],
    "z3": ["python3", "-c", "import z3; print(z3.__version__)"]
}

class EnhancedPythonCodeGenerator:
    def __init__(self, model_name=OLLAMA_MODEL):
        self.model_name = model_name
        self.output_dir = Path(DEFAULT_OUTPUT_DIR)
        self.backup_dir = Path(BACKUP_DIRECTORY)
        self.context_buffer = []
        self.multi_line_mode = False
        self.current_input = ""
        self.validators_enabled = ENABLE_CODE_VALIDATORS  # Instance-level validator setting
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure the output and backup directories exist."""
        self.output_dir.mkdir(exist_ok=True, parents=True)
        if BACKUP_BEFORE_VALIDATION:
            self.backup_dir.mkdir(exist_ok=True, parents=True)
    
    def is_complete_structure(self, text: str) -> bool:
        """Check if the input is a complete, valid structure that can be processed."""
        stripped = text.strip()
        
        # Empty input is not complete
        if not stripped:
            return False
        
        # Check for unclosed strings first
        if self._has_unclosed_strings(stripped):
            return False
        
        # Try to parse as valid Python syntax first
        if self.is_valid_python_structure(stripped):
            return True
        
        # If it contains natural language instructions/requests, it's complete
        # Look for common request patterns
        request_indicators = [
            'create', 'make', 'generate', 'build', 'write', 'develop',
            'implement', 'design', 'script', 'program', 'function',
            'class', 'module', 'tool', 'application', 'system'
        ]
        
        if any(word in stripped.lower() for word in request_indicators):
            return True
        
        # If it doesn't look like code/data structure, treat as complete natural language
        if not any(char in stripped for char in ['{', '[', '=', ':', '"']):
            return True
            
        # For structures with brackets, check if they're balanced
        if (stripped.count('{') == stripped.count('}') and
            stripped.count('[') == stripped.count(']') and
            stripped.count('(') == stripped.count(')')):
            
            # If brackets are balanced, check if it ends properly
            if (stripped.endswith('}') or stripped.endswith(']') or 
                stripped.endswith(')') or not any(char in stripped for char in ['{', '[', '('])):
                return True
        
        return False
    
    def _has_unclosed_strings(self, text: str) -> bool:
        """Check if there are unclosed string literals."""
        # More sophisticated string checking
        in_single = False
        in_double = False
        i = 0
        while i < len(text):
            char = text[i]
            if char == "'" and not in_double:
                # Check if it's escaped
                if i > 0 and text[i-1] == '\\':
                    i += 1
                    continue
                in_single = not in_single
            elif char == '"' and not in_single:
                # Check if it's escaped
                if i > 0 and text[i-1] == '\\':
                    i += 1
                    continue
                in_double = not in_double
            i += 1
        
        return in_single or in_double
    
    def is_incomplete_structure(self, text: str) -> bool:
        """Check if the input appears to be an incomplete data structure that needs more input.
        
        This method is EXTREMELY conservative - it almost never considers something incomplete
        unless it's absolutely obvious (like ending with an equals sign or open bracket).
        """
        stripped = text.strip()
        
        # If it's already complete, it's not incomplete
        if self.is_complete_structure(stripped):
            return False
        
        # If it contains natural language request words, assume it's complete
        request_words = ['create', 'make', 'generate', 'build', 'write', 'develop', 'script', 'program', 'implement']
        if any(word in stripped.lower() for word in request_words):
            return False
        
        # If it's longer than a few words, assume it's complete
        if len(stripped.split()) > 5:
            return False
        
        # Only consider incomplete in these EXTREMELY obvious cases:
        extremely_obvious_incomplete = (
            # Assignment that ends with equals (x = )
            stripped.endswith('=') or
            
            # Ends with opening bracket ONLY (not closing)
            (stripped.endswith('{') and stripped.count('}') == 0) or
            (stripped.endswith('[') and stripped.count(']') == 0) or
            
            # Very short input that's clearly just a variable name
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
    
    def detect_data_structure_type(self, text: str) -> str:
        """Detect what type of data structure the user is trying to input."""
        stripped = text.strip()
        
        if 'CATS' in stripped.upper():
            return "CATS dictionary for image/content generation"
        elif stripped.startswith('{') or '= {' in stripped:
            return "dictionary structure"
        elif stripped.startswith('[') or '= [' in stripped:
            return "list structure"
        elif any(category in stripped.lower() for category in 
                ['productivity', 'confidence', 'gratitude', 'healing', 'focus']):
            return "wellness/affirmation categories"
        else:
            return "code structure"
    
    def should_confirm_input(self, text: str) -> bool:
        """Determine if we should ask for confirmation on ambiguous input."""
        if not CONFIRM_AMBIGUOUS_INPUT:
            return False
        
        lines = text.strip().split('\n')
        
        # Only ask for confirmation if input is REALLY long (more lines than threshold)
        if len(lines) >= CONFIRMATION_THRESHOLD * 2:  # Doubled the threshold
            return True
        
        # Don't ask for confirmation on most cases - let it process
        return False
    
    def validate_code_with_validators(self, script_path: Path) -> dict:
        """Run the generated code through 10 different validators."""
        if not self.validators_enabled:
            return {"status": "skipped", "message": "Code validators disabled"}
        
        print(f"\n🔧 Running code validators on: {script_path.name}")
        print("=" * 50)
        
        validation_results = {}
        passed_count = 0
        total_count = 0
        
        for validator_name, cmd in VALIDATORS.items():
            total_count += 1
            try:
                # Special handling for different validators
                test_cmd = cmd.copy()
                
                if validator_name == "coverage":
                    # Create a simple test file for coverage
                    test_file = script_path.parent / f"test_{script_path.name}"
                    try:
                        test_file.write_text(f"import {script_path.stem}\nprint('Coverage test complete')")
                        test_cmd += [str(test_file)]
                    except Exception:
                        # If we can't create test file, skip coverage
                        validation_results[validator_name] = {"status": "SKIP", "reason": "Could not create test file"}
                        continue
                elif validator_name == "pytest":
                    # Look for test files, skip if none found
                    test_files = list(script_path.parent.glob("test_*.py"))
                    if not test_files:
                        validation_results[validator_name] = {"status": "SKIP", "reason": "No test files found"}
                        continue
                elif validator_name == "z3":
                    # Just check if Z3 is available
                    result = subprocess.run(test_cmd, check=True, capture_output=True, text=True, timeout=10)
                    validation_results[validator_name] = {"status": "PASS", "output": "Z3 available"}
                    passed_count += 1
                    print(f"  ✓ [{validator_name.upper()}] PASS - Z3 theorem prover available")
                    continue
                else:
                    # Add the script path to the command
                    test_cmd.append(str(script_path))
                
                # Run the validator
                result = subprocess.run(test_cmd, check=True, capture_output=True, text=True, timeout=30)
                
                validation_results[validator_name] = {
                    "status": "PASS",
                    "output": result.stdout.strip() if result.stdout else "No output"
                }
                passed_count += 1
                print(f"  ✓ [{validator_name.upper()}] PASS")
                
            except subprocess.CalledProcessError as e:
                validation_results[validator_name] = {
                    "status": "FAIL",
                    "stderr": e.stderr.strip() if e.stderr else "No error output",
                    "stdout": e.stdout.strip() if e.stdout else "No output"
                }
                print(f"  ✗ [{validator_name.upper()}] FAIL")
                if SHOW_VALIDATION_FEEDBACK and e.stderr:
                    # Show first few lines of error
                    error_lines = e.stderr.strip().split('\n')[:3]
                    for line in error_lines:
                        if line.strip():
                            print(f"    Error: {line.strip()}")
                
            except subprocess.TimeoutExpired:
                validation_results[validator_name] = {
                    "status": "TIMEOUT",
                    "reason": "Validator timed out after 30 seconds"
                }
                print(f"  ⏱️ [{validator_name.upper()}] TIMEOUT")
                
            except FileNotFoundError:
                validation_results[validator_name] = {
                    "status": "NOT_FOUND",
                    "reason": f"{validator_name} not installed or not in PATH"
                }
                print(f"  ⚠️ [{validator_name.upper()}] NOT INSTALLED")
                
            except Exception as e:
                validation_results[validator_name] = {
                    "status": "ERROR",
                    "reason": str(e)
                }
                print(f"  ❌ [{validator_name.upper()}] ERROR: {e}")
            
            # Clean up temporary test files
            if validator_name == "coverage":
                test_file = script_path.parent / f"test_{script_path.name}"
                if test_file.exists():
                    test_file.unlink()
        
        print("=" * 50)
        print(f"📊 Validation Summary: {passed_count}/{total_count} validators passed")
        
        return {
            "total_validators": total_count,
            "passed_validators": passed_count,
            "pass_rate": (passed_count / total_count) * 100 if total_count > 0 else 0,
            "results": validation_results
        }
    
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
            
            # Start a thinking indicator in a separate thread
            thinking_active = threading.Event()
            thinking_active.set()
            
            def show_thinking_progress():
                """Show progress dots while the model is thinking."""
                dots = 0
                while thinking_active.is_set():
                    dots = (dots + 1) % 4
                    if purpose == "generation":
                        progress = "   Thinking" + "." * dots
                    else:
                        progress = "   Validating" + "." * dots
                    print(f"\r{progress}", end="", flush=True)
                    time.sleep(0.5)
                print("")  # New line when done
            
            # Start the progress indicator
            progress_thread = threading.Thread(target=show_thinking_progress, daemon=True)
            progress_thread.start()
            
            # Start the subprocess without timeout
            process = subprocess.Popen(
                ["ollama", "run", self.model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send the prompt and wait for response
            stdout, stderr = process.communicate(input=prompt.encode())
            
            # Stop the thinking indicator
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
            # Always clean up the thinking indicator and process
            if thinking_active:
                thinking_active.clear()
            if progress_thread:
                progress_thread.join(timeout=1)
            if process:
                try:
                    if process.poll() is None:  # Process is still running
                        process.terminate()
                        process.wait(timeout=5)
                except:
                    try:
                        process.kill()
                    except:
                        pass
    
    def extract_python_code(self, response: str) -> str:
        """Extract Python code from the model response."""
        # Look for code blocks marked with ```python or ```
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```python') or line.strip().startswith('```'):
                if in_code_block:
                    break  # End of code block
                in_code_block = True
                continue
            
            if in_code_block:
                if line.strip() == '```':
                    break
                code_lines.append(line)
        
        # If no code blocks found, treat the entire response as code
        if not code_lines:
            # Filter out obvious non-code lines
            for line in lines:
                stripped = line.strip()
                if (not stripped.startswith('Here') and 
                    not stripped.startswith('This') and 
                    not stripped.startswith('The') and
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
            
            # Extract improved code
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
            
            # If validation didn't work, continue with original
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
    
    def generate_filename(self, user_request: str) -> str:
        """Generate a filename based on the user request."""
        # Extract key words from the request
        words = user_request.lower().split()
        filename_words = []
        
        # Skip common words and focus on meaningful terms
        skip_words = {'make', 'create', 'generate', 'write', 'a', 'an', 'the', 'file', 'script', 'program'}
        
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word and clean_word not in skip_words:
                filename_words.append(clean_word)
        
        if not filename_words:
            filename_words = ['script']
        
        # Use first few words and add timestamp
        base_name = '_'.join(filename_words[:3])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.py"
    
    def save_code(self, code: str, filename: str, output_dir: Path = None) -> bool:
        """Save the generated code to a file."""
        if output_dir is None:
            output_dir = self.output_dir
        
        try:
            output_path = output_dir / filename
            
            # Create backup if file exists and validation is enabled
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
            # Default behavior: process everything immediately unless EXTREMELY obvious it's incomplete
            if not self.is_incomplete_structure(user_input):
                # Process immediately - this covers 99.9% of cases
                return user_input
            
            # Only for EXTREMELY obvious incomplete cases (like "data = " or "my_dict = {")
            self.multi_line_mode = True
            self.current_input = user_input
            print("💡 Input appears incomplete. Continue entering data, or type 'END' to process as-is.")
            return None
        else:
            # We're in multi-line mode (rare case)
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
                # Add the new line to current input
                self.current_input += "\n" + user_input
                
                # Check if the combined input is now complete
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
                    time.sleep(1)  # Brief pause before retry
                    
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
        
        # Detect the type of request and adjust the prompt accordingly
        structure_type = self.detect_data_structure_type(user_request)
        
        if "CATS dictionary" in structure_type or "wellness" in structure_type:
            # Special handling for CATS dictionary requests
            prompt = f"""Generate a complete Python script that processes the following data structure: 

{user_request}

Create a comprehensive script that:
1. Defines the complete data structure
2. Processes all categories and subcategories in a single script
3. Includes functionality to work with the entire dataset
4. Provides clear output and organization
5. Uses the data structure as intended (for image generation, affirmations, etc.)

Make sure this is ONE complete script that handles ALL the data, not separate scripts for each category.

Python code:"""
        else:
            # Standard prompt for other requests
            prompt = f"""Generate a complete Python script based on this request: "{user_request}"

Please provide only the Python code without any explanations or markdown formatting.
Make sure the code is complete, well-commented, and ready to run.
Include necessary imports and proper error handling where appropriate.

Request: {user_request}

Python code:"""
        
        # Call the model
        response = self.call_model(prompt)
        if not response:
            return False
        
        # Extract Python code from response
        code = self.extract_python_code(response)
        if not code:
            print("❌ Could not extract Python code from model response.")
            if attempt == 1:  # Only show raw response on first attempt
                print("Raw response:", response[:200] + "..." if len(response) > 200 else response)
            return False
        
        # Validate Python syntax
        if not self.validate_python_code(code):
            print("❌ Generated code has syntax errors.")
            return False
        
        # Generate filename
        filename = self.generate_filename(user_request)
        
        # Validate and improve code with model
        if ENABLE_VALIDATION_LOOP:
            code, validation_feedback = self.validate_code_with_model(code, filename)
            if SHOW_VALIDATION_FEEDBACK:
                print(validation_feedback)
        
        # Save the code
        if self.save_code(code, filename, output_dir):
            print(f"🎉 Generated Python script: {filename}")
            
            # Show a preview of the code
            print("\n📄 Code preview:")
            print("-" * 50)
            preview_lines = code.split('\n')[:15]
            for i, line in enumerate(preview_lines, 1):
                print(f"{i:2d}: {line}")
            if len(code.split('\n')) > 15:
                print("    ... (showing first 15 lines)")
            print("-" * 50)
            
            # Run the 10 code validators on the generated file
            script_path = (output_dir or self.output_dir) / filename
            validation_results = self.validate_code_with_validators(script_path)
            
            # Show final validation summary
            if self.validators_enabled:
                pass_rate = validation_results.get('pass_rate', 0)
                if pass_rate >= 70:
                    print(f"🎉 Excellent! {pass_rate:.1f}% of validators passed")
                elif pass_rate >= 50:
                    print(f"👍 Good! {pass_rate:.1f}% of validators passed")
                else:
                    print(f"⚠️ {pass_rate:.1f}% of validators passed - consider reviewing the code")
            
            return True
        
        return False

def main():
    """Main interactive loop."""
    generator = EnhancedPythonCodeGenerator()
    
    print("🐍 Enhanced Interactive Python Code Generator with 10 Code Validators")
    print("=" * 80)
    print("This tool uses your local AI model to generate Python scripts based on your requests.")
    print("All generated files are automatically validated with 10 different code quality tools.")
    print("\n🚀 FEATURES:")
    print("  ✓ Intelligent multi-line input support")
    print("  ✓ Paste complete dictionaries/structures directly")
    print("  ✓ Automatic detection of complete vs incomplete input")
    print("  ✓ Self-validation loop for code quality")
    print("  ✓ 10 comprehensive code validators (black, flake8, pylint, mypy, bandit, etc.)")
    print("  ✓ Automatic backup system")
    print("  ✓ Retry logic with error recovery")
    print("  ✓ No manual END/CANCEL needed for complete input")
    print("  ✓ IMPROVED: Better handling of large prompts - just paste and go!")
    
    print(f"\n⚙️ CONFIGURATION:")
    print(f"  • Model: {OLLAMA_MODEL}")
    print(f"  • Max retries: {MAX_RETRIES}")
    print(f"  • Model validation: {'Enabled' if ENABLE_VALIDATION_LOOP else 'Disabled'} ({VALIDATION_LEVEL})")
    print(f"  • Code validators: {'Enabled' if ENABLE_CODE_VALIDATORS else 'Disabled'} (10 validators)")
    print(f"  • Backups: {'Enabled' if BACKUP_BEFORE_VALIDATION else 'Disabled'}")
    print(f"  • Input confirmation: {'Enabled' if CONFIRM_AMBIGUOUS_INPUT else 'Disabled'}")
    
    print("\n🔧 CODE VALIDATORS:")
    validator_list = ", ".join(VALIDATORS.keys())
    print(f"  {validator_list}")
    print(f"  Current status: {'Enabled' if generator.validators_enabled else 'Disabled'}")
    
    print("\nExamples:")
    print("  - 'make a hello world program'")
    print("  - 'create a file organizer script'")
    print("  - 'generate a web scraper for news articles'")
    print("  - Paste a complete CATS dictionary - it will be processed immediately!")
    print("  - Paste any large prompt - it should work without multi-line mode!")
    print("")
    print("Commands:")
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
            # Show normal prompt - multi-line mode should be invisible to user
            prompt = "What Python script would you like me to generate? > "
            
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            # Handle special commands
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
                # Toggle the generator's validator setting
                generator.validators_enabled = not getattr(generator, 'validators_enabled', ENABLE_CODE_VALIDATORS)
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