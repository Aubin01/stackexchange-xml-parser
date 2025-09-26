#!/usr/bin/env python3
"""
Optimized Math Stack Exchange XML Parser
Efficiently extracts a specified number of posts from large XML dumps using streaming parsing.

Usage: python3 parser.py posts.xml 10
"""

import sys
import xml.etree.ElementTree as ET
import argparse
import re


def extract_year_from_date(date_string):
    """Extract year from ISO date string (e.g., '2015-07-14T19:35:44.557')"""
    try:
        # Date format is usually: 2015-07-14T19:35:44.557
        year_match = re.match(r'^(\d{4})', date_string)
        if year_match:
            return int(year_match.group(1))
    except (ValueError, AttributeError):
        pass
    return 0  # Default year if parsing fails


def should_include_post_by_year(post_attrs, min_year=None, max_year=None, specific_years=None):
    """Determine if a post should be included based on year criteria"""
    if min_year is None and max_year is None and not specific_years:
        return True  # No year filtering
    
    creation_date = post_attrs.get('CreationDate', '')
    if not creation_date:
        return True  # Include if no date available
    
    post_year = extract_year_from_date(creation_date)
    
    # Filter by specific years
    if specific_years and post_year not in specific_years:
        return False
    
    # Filter by year range
    if min_year is not None and post_year < min_year:
        return False
    if max_year is not None and post_year > max_year:
        return False
    
    return True


def extract_posts_streaming(input_file, num_posts, min_year=None, max_year=None, specific_years=None):
    """
    Extract posts using streaming XML parsing for memory efficiency
    
    Args:
        input_file: Path to the input XML file
        num_posts: Number of posts to extract
    
    Returns:
        List of post dictionaries
    """
    posts = []
    extracted_count = 0
    
    try:
        # Use iterparse for memory-efficient parsing
        context = ET.iterparse(input_file, events=('start', 'end'))
        context = iter(context)
        
        # Get the root element
        event, root = next(context)
        
        for event, elem in context:
            if event == 'end' and elem.tag == 'row':
                # This is a post record
                if extracted_count < num_posts:
                    # Check if post meets year criteria
                    post_data = dict(elem.attrib)
                    if should_include_post_by_year(post_data, min_year, max_year, specific_years):
                        posts.append(post_data)
                        extracted_count += 1
                        
                        # Print progress for large extractions
                        if extracted_count % 1000 == 0:
                            print(f"Extracted {extracted_count}/{num_posts} posts...", file=sys.stderr)
                        
                        # Stop parsing when we reach our target
                        if extracted_count >= num_posts:
                            break
                
                # Clear the element to free memory
                elem.clear()
                root.clear()
        
        return posts
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def create_output_xml(posts, output_file):
    """
    Create a new XML file with the extracted posts
    
    Args:
        posts: List of post dictionaries
        output_file: Path to the output XML file
    """
    try:
        # Create the root element
        root = ET.Element("posts")
        
        # Add each post as a row element
        for post in posts:
            row = ET.SubElement(root, "row")
            for key, value in post.items():
                row.set(key, str(value))
        
        # Add indentation for readable formatting
        indent(root)
        
        # Create the tree and write to file
        tree = ET.ElementTree(root)
        
        # Write with proper XML declaration and formatting
        with open(output_file, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
        
        print(f"Successfully extracted {len(posts)} posts to '{output_file}'")
        
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def indent(elem, level=0):
    """Add indentation to XML elements for pretty printing"""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Extract a specified number of posts from Math Stack Exchange XML dump",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 parser.py posts.xml 10                    # Extract 10 posts
  python3 parser.py posts.xml 100 --min-year 2015   # Extract 100 posts from 2015 onwards
  python3 parser.py posts.xml 50 --years 2013,2016  # Extract 50 posts from 2013 and 2016
  python3 parser.py posts.xml 200 --min-year 2012 --max-year 2018  # Extract from 2012-2018
        """
    )
    
    parser.add_argument('input_file', 
                       help='Path to the input XML file (Math Stack Exchange dump)')
    
    parser.add_argument('num_posts', 
                       type=int,
                       help='Number of posts to extract')
    
    parser.add_argument('-o', '--output',
                       help='Output XML file name (default: extracted_posts.xml)',
                       default='extracted_posts.xml')
    
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Enable verbose output')
    
    # Year filters
    parser.add_argument('--min-year',
                       type=int,
                       help='Minimum post year (e.g., 2015)')
    
    parser.add_argument('--max-year', 
                       type=int,
                       help='Maximum post year (e.g., 2023)')
    
    parser.add_argument('--years',
                       help='Specific years to include (comma-separated, e.g., 2015,2018,2023)')
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments"""
    if args.num_posts <= 0:
        print("Error: Number of posts must be greater than 0", file=sys.stderr)
        sys.exit(1)
    
    # Check if input file exists
    import os
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    # Validate year arguments
    current_year = 2025  # Update as needed
    if args.min_year and (args.min_year < 2008 or args.min_year > current_year):
        print(f"Error: --min-year must be between 2008 and {current_year}", file=sys.stderr)
        sys.exit(1)
        
    if args.max_year and (args.max_year < 2008 or args.max_year > current_year):
        print(f"Error: --max-year must be between 2008 and {current_year}", file=sys.stderr)
        sys.exit(1)
        
    if args.min_year and args.max_year and args.min_year > args.max_year:
        print("Error: --min-year cannot be greater than --max-year", file=sys.stderr)
        sys.exit(1)
        
    if args.years and (args.min_year or args.max_year):
        print("Error: Cannot use --years with --min-year or --max-year", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Validate arguments
    validate_arguments(args)
    
    # Parse specific years if provided
    specific_years = None
    if args.years:
        try:
            specific_years = set(int(year.strip()) for year in args.years.split(','))
        except ValueError:
            print("Error: Invalid year format in --years. Use integers like: 2015,2018,2023", file=sys.stderr)
            sys.exit(1)
    
    if args.verbose:
        print(f"Extracting {args.num_posts} posts from '{args.input_file}'...")
        if args.min_year or args.max_year:
            year_range = f"Years: {args.min_year or 'any'} to {args.max_year or 'any'}"
            print(f"Filter: {year_range}")
        elif specific_years:
            print(f"Filter: Years {sorted(specific_years)}")
    
    # Extract posts using streaming parser
    posts = extract_posts_streaming(args.input_file, args.num_posts, args.min_year, args.max_year, specific_years)
    
    if not posts:
        print("No posts were extracted. Check if the input file contains valid post data.", file=sys.stderr)
        sys.exit(1)
    
    if args.verbose:
        print(f"Successfully extracted {len(posts)} posts")
        
        # Show some statistics
        post_types = {}
        for post in posts:
            post_type = post.get('PostTypeId', 'Unknown')
            post_types[post_type] = post_types.get(post_type, 0) + 1
        
        print("Post type distribution:")
        for post_type, count in post_types.items():
            type_name = "Question" if post_type == "1" else "Answer" if post_type == "2" else f"Type {post_type}"
            print(f"  {type_name}: {count}")
    
    # Create output XML file
    create_output_xml(posts, args.output)
    
    if args.verbose:
        print(f"Output written to '{args.output}'")


if __name__ == "__main__":
    main()