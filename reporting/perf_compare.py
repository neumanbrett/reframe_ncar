#!/usr/bin/env python3
"""
Quick performance comparison script.
Compares two performance values and calculates speedup/slowdown.
"""

import argparse
import sys

def compare_performance(name1, value1, name2, value2, metric_type='time'):
    """
    Compare two performance values and print results.
    
    Args:
        name1: Name of first configuration
        value1: Performance value for first configuration
        name2: Name of second configuration  
        value2: Performance value for second configuration
        metric_type: 'time' (lower is better) or 'throughput' (higher is better)
    """
    
    print(f"\n{'='*60}")
    print(f"Performance Comparison")
    print(f"{'='*60}")
    print(f"{name1:30s}: {value1:12.4f}")
    print(f"{name2:30s}: {value2:12.4f}")
    print(f"{'-'*60}")
    
    # Calculate difference
    diff = value2 - value1
    pct_diff = (diff / value1) * 100
    
    # Calculate speedup based on metric type
    if metric_type.lower() == 'time':
        # For time: speedup = baseline_time / new_time
        speedup = value1 / value2
        faster_slower = "faster" if value2 < value1 else "slower"
        baseline = name1
        comparison = name2
    else:
        # For throughput: speedup = new_throughput / baseline_throughput
        speedup = value2 / value1
        faster_slower = "faster" if value2 > value1 else "slower"
        baseline = name1
        comparison = name2
    
    print(f"Difference: {diff:+12.4f} ({pct_diff:+.2f}%)")
    print(f"Speedup: {speedup:.2f}x")
    
    if speedup > 1.0:
        print(f"\n✓ {comparison} is {speedup:.2f}x {faster_slower} than {baseline}")
    elif speedup < 1.0:
        slowdown = 1.0 / speedup
        print(f"\n✗ {comparison} is {slowdown:.2f}x slower than {baseline}")
    else:
        print(f"\n= Performance is identical")
    
    print(f"{'='*60}\n")
    
    return speedup

def main():
    parser = argparse.ArgumentParser(
        description='Compare two performance measurements',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare execution times (lower is better)
  python perf_compare.py --name1 "nvgpu" --value1 123.8 --name2 "rez" --value2 126.8
  
  # Compare throughput (higher is better)
  python perf_compare.py --name1 "Config A" --value1 50000 --name2 "Config B" --value2 75000 --type throughput
  
  # Short form
  python perf_compare.py -n1 baseline -v1 100 -n2 optimized -v2 75
        """
    )
    
    parser.add_argument('-n1', '--name1', required=True,
                        help='Name of first configuration/test')
    parser.add_argument('-v1', '--value1', type=float, required=True,
                        help='Performance value for first configuration')
    parser.add_argument('-n2', '--name2', required=True,
                        help='Name of second configuration/test')
    parser.add_argument('-v2', '--value2', type=float, required=True,
                        help='Performance value for second configuration')
    parser.add_argument('-t', '--type', choices=['time', 'throughput'],
                        default='time',
                        help='Metric type: "time" (lower is better) or "throughput" (higher is better). Default: time')
    parser.add_argument('-u', '--unit', default='',
                        help='Optional unit to display (e.g., "seconds", "MB/s")')
    
    args = parser.parse_args()
    
    # Add unit to display if provided
    if args.unit:
        name1_display = f"{args.name1} ({args.unit})"
        name2_display = f"{args.name2} ({args.unit})"
    else:
        name1_display = args.name1
        name2_display = args.name2
    
    try:
        speedup = compare_performance(
            name1_display, args.value1,
            name2_display, args.value2,
            args.type
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())