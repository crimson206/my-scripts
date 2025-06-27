import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any
from click.utils import strip_ansi as remove_ansi_codes

def parse_jupyter_notebook(notebook_path: str) -> List[Dict[str, str]]:
    """
    Parse Jupyter notebook file and extract title and output from each cell.
    
    Args:
        notebook_path (str): Path to .ipynb file
        
    Returns:
        List[Dict[str, str]]: List of [{"title": "...", "output": "..."}, ...]
    """
    
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    results = []
    
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') != 'code':
            continue
            
        # Extract title from docstring
        source = cell.get('source', [])
        if not source:
            continue
            
        # Join source lines and extract title
        source_text = ''.join(source) if isinstance(source, list) else source
        title = extract_title_from_source(source_text)
        
        # Extract output
        outputs = cell.get('outputs', [])
        output_text = extract_output_from_outputs(outputs)
        
        # Only add if we have both title and output
        if title and output_text:
            results.append({
                "title": title,
                "output": output_text
            })
    
    return results

def extract_title_from_source(source_text: str) -> str:
    """
    Extract title from docstring in source code.
    
    Args:
        source_text (str): Cell source code
        
    Returns:
        str: Extracted title or empty string
    """
    # Find docstring pattern: """title\ndescription\n"""
    docstring_pattern = r'"""([^\n]+)\n'
    match = re.search(docstring_pattern, source_text)
    
    if match:
        return match.group(1).strip()
    
    return ""

def extract_output_from_outputs(outputs: List[Dict[str, Any]]) -> str:
    """
    Extract text output from cell outputs.
    
    Args:
        outputs (List[Dict]): Cell outputs array
        
    Returns:
        str: Extracted output text (ANSI codes removed)
    """
    output_texts = []
    
    for output in outputs:
        output_type = output.get('output_type', '')
        
        if output_type == 'stream':
            # stdout, stderr stream outputs
            text = output.get('text', [])
            if isinstance(text, list):
                output_texts.extend(text)
            else:
                output_texts.append(text)
                
        elif output_type == 'execute_result':
            # Execution results (pprint, etc.)
            data = output.get('data', {})
            text_plain = data.get('text/plain', [])
            if isinstance(text_plain, list):
                output_texts.extend(text_plain)
            else:
                output_texts.append(text_plain)
                
        elif output_type == 'error':
            # Error outputs
            traceback = output.get('traceback', [])
            if traceback:
                output_texts.append('\n'.join(traceback))
    
    # Remove ANSI codes and return
    raw_output = ''.join(output_texts).strip()
    return remove_ansi_codes(raw_output)

def save_parsed_results(notebook_path: str, output_path: str = None, remove_source: bool = False) -> str:
    """
    Parse Jupyter notebook and save results to JSON file.
    
    Args:
        notebook_path (str): Path to .ipynb file
        output_path (str, optional): Output JSON file path. Auto-generated if None
        remove_source (bool): Whether to remove the source .ipynb file after parsing
        
    Returns:
        str: Path to saved file
    """
    if output_path is None:
        output_path = notebook_path.replace('.ipynb', '_parsed.json')
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = parse_jupyter_notebook(notebook_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Parsing results saved to {output_path}")
    print(f"Total {len(results)} cells parsed")
    
    # Remove source file if requested
    if remove_source:
        try:
            os.remove(notebook_path)
            print(f"Source file {notebook_path} removed")
        except Exception as e:
            print(f"Warning: Could not remove source file {notebook_path}: {e}")
    
    return output_path

# Usage example
if __name__ == "__main__":
    # Example usage
    title = "example_publish"
    notebook_file = f"examples/{title}.ipynb"
    
    # 1. Parse only
    results = parse_jupyter_notebook(notebook_file)
    for result in results:
        print(f"Title: {result['title']}")
        print(f"Output: {result['output'][:100]}...")  # First 100 chars only
        print("-" * 50)
    
    # 2. Save to JSON file with auto directory creation and source removal
    output_file = save_parsed_results(
        notebook_file, 
        f"examples/results/{title}.json",
        remove_source=True  # Set to True to remove .ipynb file after parsing
    )
