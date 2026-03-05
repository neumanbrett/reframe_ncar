import re
import argparse
import sys

def parse_reframe_output(text, metric_name='total_time', metric_unit='s'):
    """
    Parse ReFrame output and return a dictionary of results.
    
    Args:
        text: The raw ReFrame output text
        metric_name: Name of the performance metric to extract (e.g., 'total_time', 'columns_per_second')
        metric_unit: Unit of the metric (e.g., 's', 'columns/s')
    
    Returns:
        Dictionary with test parameters as keys and metric values as values
    """
    results = {}
    
    # Pattern to match test name and parameters
    # Captures scale if present and compiler
    test_pattern = r'(\w+Test)(?:\s+%scale=(\d+))?\s+/[\w]+\s+@[\w:]+\+(\w+)'
    # Pattern to match the metric
    metric_pattern = rf'{metric_name}:\s+([\d.]+)\s+{re.escape(metric_unit)}'
    
    lines = text.strip().split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        test_match = re.search(test_pattern, line)
        if test_match:
            test_name = test_match.group(1)
            scale = int(test_match.group(2)) if test_match.group(2) else None
            compiler = test_match.group(3)
            
            # Look for metric in next line
            if i + 1 < len(lines):
                metric_match = re.search(metric_pattern, lines[i + 1])
                if metric_match:
                    value = float(metric_match.group(1))
                    
                    # Create key based on whether scale exists
                    if scale is not None:
                        key = (scale, compiler)
                    else:
                        key = compiler
                    
                    results[key] = value
                    i += 1  # Skip the metric line
        i += 1
    
    return results

def create_scaling_table(r1878379_results, htc_results, metric_name='total_time', metric_unit='s'):
    """Create a Slack-compatible markdown table for scaling tests."""
    
    # Get all unique keys and sort them
    keys = sorted(set(r1878379_results.keys()) | set(htc_results.keys()))
    
    # Check if keys are tuples (scaling test) or strings (single test)
    is_scaling = isinstance(keys[0], tuple) if keys else False
    
    # Build table
    table = []
    if is_scaling:
        table.append(f"| Scale | Compiler | R1878379 ({metric_unit}) | HTC ({metric_unit}) | Speedup (HTC vs R1878379) |")
        table.append("|-------|----------|--------------------------|---------------------|---------------------------|")
    else:
        table.append(f"| Compiler | R1878379 ({metric_unit}) | HTC ({metric_unit}) | Speedup (HTC vs R1878379) |")
        table.append("|----------|--------------------------|---------------------|---------------------------|")
    
    for key in keys:
        r_value = r1878379_results.get(key, 0)
        h_value = htc_results.get(key, 0)
        
        if r_value > 0 and h_value > 0:
            # For metrics where higher is better (like columns/s), speedup is HTC/R1878379
            # For metrics where lower is better (like time), speedup is R1878379/HTC
            if 'time' in metric_name.lower():
                speedup = r_value / h_value