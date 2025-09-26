#!/usr/bin/env python3
"""
Advanced Math Stack Exchange XML Parser with Filtering and Custom Formatting
Creates output in Topics_V2.0.xml format with filtering capabilities.

Usage: python3 parser2.py posts.xml 10 [options]
"""

import sys
import xml.etree.ElementTree as ET
import argparse
import html
import re
from typing import List, Dict, Set, Optional


class PostFilter:
    """Handle filtering of posts based on various criteria"""
    
    def __init__(self, min_score=None, max_score=None, post_types=None, 
                 tags_include=None, tags_exclude=None, min_answers=None,
                 has_accepted_answer=None, min_views=None, min_year=None, 
                 max_year=None, specific_years=None):
        self.min_score = min_score
        self.max_score = max_score  
        self.post_types = post_types or ['1', '2']  # Default: questions and answers
        self.tags_include = set(tags_include) if tags_include else set()
        self.tags_exclude = set(tags_exclude) if tags_exclude else set()
        self.min_answers = min_answers
        self.has_accepted_answer = has_accepted_answer
        self.min_views = min_views
        self.min_year = min_year
        self.max_year = max_year
        self.specific_years = set(specific_years) if specific_years else set()

    def should_include_post(self, post_attrs: Dict[str, str]) -> bool:
        """Determine if a post should be included based on filter criteria"""
        
        # Filter by post type
        post_type = post_attrs.get('PostTypeId', '1')
        if post_type not in self.post_types:
            return False
            
        # Filter by score
        score = int(post_attrs.get('Score', '0'))
        if self.min_score is not None and score < self.min_score:
            return False
        if self.max_score is not None and score > self.max_score:
            return False
            
        # Filter by view count (only for questions)
        if post_type == '1' and self.min_views is not None:
            views = int(post_attrs.get('ViewCount', '0'))
            if views < self.min_views:
                return False
                
        # Filter by answer count (only for questions)
        if post_type == '1' and self.min_answers is not None:
            answer_count = int(post_attrs.get('AnswerCount', '0'))
            if answer_count < self.min_answers:
                return False
                
        # Filter by accepted answer (only for questions)
        if post_type == '1' and self.has_accepted_answer is not None:
            has_accepted = 'AcceptedAnswerId' in post_attrs
            if self.has_accepted_answer and not has_accepted:
                return False
            if not self.has_accepted_answer and has_accepted:
                return False
                
        # Filter by tags (only for questions)
        if post_type == '1' and (self.tags_include or self.tags_exclude):
            tags_text = post_attrs.get('Tags', '')
            post_tags = self._extract_tags(tags_text)
            
            # Must include at least one of the required tags
            if self.tags_include and not self.tags_include.intersection(post_tags):
                return False
                
            # Must not include any excluded tags
            if self.tags_exclude and self.tags_exclude.intersection(post_tags):
                return False
        
        # Filter by year
        if self.min_year is not None or self.max_year is not None or self.specific_years:
            creation_date = post_attrs.get('CreationDate', '')
            if creation_date:
                post_year = self._extract_year_from_date(creation_date)
                
                # Filter by specific years
                if self.specific_years and post_year not in self.specific_years:
                    return False
                
                # Filter by year range
                if self.min_year is not None and post_year < self.min_year:
                    return False
                if self.max_year is not None and post_year > self.max_year:
                    return False
                
        return True
    
    def _extract_tags(self, tags_text: str) -> Set[str]:
        """Extract individual tags from the tags string"""
        if not tags_text:
            return set()
            
        # Tags are in format <tag1><tag2><tag3>
        tags = re.findall(r'<([^>]+)>', tags_text)
        return set(tags)
    
    def _extract_year_from_date(self, date_string: str) -> int:
        """Extract year from ISO date string (e.g., '2015-07-14T19:35:44.557')"""
        try:
            # Date format is usually: 2015-07-14T19:35:44.557
            year_match = re.match(r'^(\d{4})', date_string)
            if year_match:
                return int(year_match.group(1))
        except (ValueError, AttributeError):
            pass
        return 0  # Default year if parsing fails


class TopicsFormatter:
    """Format posts into Topics_V2.0.xml structure"""
    
    def __init__(self):
        self.topic_counter = 1
        
    def format_posts_to_topics_xml(self, posts: List[Dict[str, str]], 
                                  output_file: str) -> None:
        """Convert posts to Topics XML format and write to file"""
        
        # Create root element
        root = ET.Element("Topics")
        
        # Process only questions (PostTypeId=1) for topics format
        questions = [p for p in posts if p.get('PostTypeId', '1') == '1']
        
        for post in questions:
            topic = self._create_topic_element(post)
            root.append(topic)
            
        # Add proper XML formatting
        self._indent(root)
        
        # Write to file
        tree = ET.ElementTree(root)
        
        # Create XML declaration manually for better control
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" ?>\n')
            # Write the tree without XML declaration (we added our own)
            tree.write(f, encoding='unicode', xml_declaration=False)
            
    def _create_topic_element(self, post: Dict[str, str]) -> ET.Element:
        """Create a Topic element from a post"""
        
        topic = ET.Element("Topic", number=f"A.{self.topic_counter}")
        self.topic_counter += 1
        
        # Add Title element
        title_elem = ET.SubElement(topic, "Title")
        title_text = post.get('Title', 'Untitled Question')
        title_elem.text = self._process_html_content(title_text)
        
        # Add Question element  
        question_elem = ET.SubElement(topic, "Question")
        body_text = post.get('Body', '')
        question_elem.text = self._process_html_content(body_text)
        
        # Add Tags element
        tags_elem = ET.SubElement(topic, "Tags")
        tags_text = self._extract_clean_tags(post.get('Tags', ''))
        tags_elem.text = tags_text
        
        return topic
        
    def _process_html_content(self, content: str) -> str:
        """Process HTML content to match Topics format"""
        if not content:
            return ""
            
        # The content is already HTML-encoded in the original XML
        # We just need to clean it up a bit for the Topics format
        
        # Remove some excessive whitespace while preserving structure
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
        
    def _extract_clean_tags(self, tags_text: str) -> str:
        """Extract and clean tags for display"""
        if not tags_text:
            return ""
            
        # Extract tags from <tag1><tag2> format
        tags = re.findall(r'<([^>]+)>', tags_text)
        
        # Join with commas
        return ','.join(tags)
        
    def _indent(self, elem, level=0):
        """Add indentation for pretty printing"""
        i = "\n" + level * "   "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "   "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


class StreamingPostExtractor:
    """
    Advanced streaming XML parser with filtering capabilities
    """
    
    def __init__(self, target_count: int, post_filter: PostFilter):
        self.target_count = target_count
        self.post_filter = post_filter
        self.extracted_count = 0
        self.total_processed = 0
        self.posts = []
        
    def extract_from_file(self, input_file: str) -> List[Dict[str, str]]:
        """Extract filtered posts from XML file"""
        
        try:
            # Use iterparse for memory-efficient parsing
            context = ET.iterparse(input_file, events=('start', 'end'))
            context = iter(context)
            
            # Get the root element
            event, root = next(context)
            
            for event, elem in context:
                if event == 'end' and elem.tag == 'row':
                    self.total_processed += 1
                    
                    # Check if this post matches our filter criteria
                    if self.post_filter.should_include_post(elem.attrib):
                        # Convert element to dictionary
                        post_data = dict(elem.attrib)
                        self.posts.append(post_data)
                        self.extracted_count += 1
                        
                        # Check if we've reached our target
                        if self.extracted_count >= self.target_count:
                            print(f"Target of {self.target_count} posts reached!", file=sys.stderr)
                            break
                    
                    # Clear the element to free memory
                    elem.clear()
                    root.clear()
                    
                    # Progress reporting for large files
                    if self.total_processed % 5000 == 0:
                        print(f"Processed {self.total_processed} records, "
                              f"extracted {self.extracted_count}", file=sys.stderr)
            
            return self.posts
            
        except ET.ParseError as e:
            print(f"XML parsing error: {e}", file=sys.stderr)
            raise
        except FileNotFoundError:
            print(f"File not found: {input_file}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Unexpected error during extraction: {e}", file=sys.stderr)
            raise


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Extract and filter Math Stack Exchange posts with Topics XML formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 parser2.py posts.xml 10
    Extract 10 posts (any type) in Topics format

  python3 parser2.py posts.xml 20 --questions-only --min-score 5
    Extract 20 questions with score >= 5

  python3 parser2.py posts.xml 15 --include-tags calculus,algebra --min-answers 2
    Extract 15 posts tagged with calculus OR algebra, with at least 2 answers

  python3 parser2.py posts.xml 25 --exclude-tags homework --min-views 1000
    Extract 25 posts excluding homework questions, with 1000+ views

  python3 parser2.py posts.xml 30 --min-year 2020 --max-year 2023
    Extract 30 posts from years 2020-2023

  python3 parser2.py posts.xml 15 --years 2015,2018,2022 --questions-only
    Extract 15 questions from specific years (2015, 2018, 2022)

Filtering Options:
  --questions-only     Extract only questions (PostTypeId=1)
  --answers-only      Extract only answers (PostTypeId=2)
  --min-score N       Minimum score threshold
  --max-score N       Maximum score threshold  
  --min-answers N     Minimum number of answers (questions only)
  --min-views N       Minimum view count (questions only)
  --has-accepted      Only questions with accepted answers
  --no-accepted       Only questions without accepted answers
  --include-tags T1,T2 Include posts with these tags (OR logic)
  --exclude-tags T1,T2 Exclude posts with these tags
  --min-year YYYY     Minimum post year (e.g., 2015)
  --max-year YYYY     Maximum post year (e.g., 2023)
  --years Y1,Y2,Y3    Specific years only (e.g., 2015,2018,2022)
        """
    )
    
    parser.add_argument('input_file',
                       help='Path to input XML file (Stack Exchange dump)')
    
    parser.add_argument('num_posts',
                       type=int,
                       help='Number of posts to extract')
    
    parser.add_argument('-o', '--output',
                       default='extracted_topics.xml',
                       help='Output XML file (default: extracted_topics.xml)')
    
    # Post type filters
    parser.add_argument('--questions-only',
                       action='store_true',
                       help='Extract only questions (PostTypeId=1)')
    
    parser.add_argument('--answers-only',
                       action='store_true',
                       help='Extract only answers (PostTypeId=2)')
    
    # Score filters
    parser.add_argument('--min-score',
                       type=int,
                       help='Minimum score threshold')
    
    parser.add_argument('--max-score',
                       type=int,
                       help='Maximum score threshold')
    
    # Question-specific filters
    parser.add_argument('--min-answers',
                       type=int,
                       help='Minimum number of answers (questions only)')
    
    parser.add_argument('--min-views',
                       type=int,
                       help='Minimum view count (questions only)')
    
    parser.add_argument('--has-accepted',
                       action='store_true',
                       help='Only questions with accepted answers')
    
    parser.add_argument('--no-accepted',
                       action='store_true',
                       help='Only questions without accepted answers')
    
    # Tag filters
    parser.add_argument('--include-tags',
                       help='Include posts with these tags (comma-separated, OR logic)')
    
    parser.add_argument('--exclude-tags',
                       help='Exclude posts with these tags (comma-separated)')
    
    # Year filters
    parser.add_argument('--min-year',
                       type=int,
                       help='Minimum post year (e.g., 2015)')
    
    parser.add_argument('--max-year', 
                       type=int,
                       help='Maximum post year (e.g., 2023)')
    
    parser.add_argument('--years',
                       help='Specific years to include (comma-separated, e.g., 2015,2018,2023)')
    
    # Output options
    parser.add_argument('-v', '--verbose',
                       action='store_true',
                       help='Enable verbose output')
    
    return parser


def validate_arguments(args) -> None:
    """Validate command line arguments"""
    if args.num_posts <= 0:
        raise ValueError("Number of posts must be greater than 0")
    
    import os
    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"Input file '{args.input_file}' not found")
    
    if args.questions_only and args.answers_only:
        raise ValueError("Cannot specify both --questions-only and --answers-only")
        
    if args.has_accepted and args.no_accepted:
        raise ValueError("Cannot specify both --has-accepted and --no-accepted")
    
    # Validate year arguments
    current_year = 2025  # Update as needed
    if args.min_year and (args.min_year < 2008 or args.min_year > current_year):
        raise ValueError(f"--min-year must be between 2008 and {current_year}")
        
    if args.max_year and (args.max_year < 2008 or args.max_year > current_year):
        raise ValueError(f"--max-year must be between 2008 and {current_year}")
        
    if args.min_year and args.max_year and args.min_year > args.max_year:
        raise ValueError("--min-year cannot be greater than --max-year")
        
    if args.years and (args.min_year or args.max_year):
        raise ValueError("Cannot use --years with --min-year or --max-year")


def create_post_filter(args) -> PostFilter:
    """Create PostFilter from command line arguments"""
    
    # Determine post types
    if args.questions_only:
        post_types = ['1']
    elif args.answers_only:
        post_types = ['2']
    else:
        post_types = ['1', '2']
    
    # Parse tag filters
    tags_include = None
    if args.include_tags:
        tags_include = [tag.strip() for tag in args.include_tags.split(',')]
        
    tags_exclude = None
    if args.exclude_tags:
        tags_exclude = [tag.strip() for tag in args.exclude_tags.split(',')]
    
    # Handle accepted answer filter
    has_accepted_answer = None
    if args.has_accepted:
        has_accepted_answer = True
    elif args.no_accepted:
        has_accepted_answer = False
    
    # Parse specific years
    specific_years = None
    if args.years:
        try:
            specific_years = [int(year.strip()) for year in args.years.split(',')]
        except ValueError:
            raise ValueError("Invalid year format in --years. Use integers like: 2015,2018,2023")
    
    return PostFilter(
        min_score=args.min_score,
        max_score=args.max_score,
        post_types=post_types,
        tags_include=tags_include,
        tags_exclude=tags_exclude,
        min_answers=args.min_answers,
        has_accepted_answer=has_accepted_answer,
        min_views=args.min_views,
        min_year=args.min_year,
        max_year=args.max_year,
        specific_years=specific_years
    )


def main():
    """Main execution function"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Validate arguments
        validate_arguments(args)
        
        # Show configuration if verbose
        if args.verbose:
            print(f"Input file: {args.input_file}")
            print(f"Extracting {args.num_posts} posts...")
            if args.questions_only:
                print("Filter: Questions only")
            elif args.answers_only:
                print("Filter: Answers only")
            if args.min_score:
                print(f"Filter: Minimum score >= {args.min_score}")
            if args.max_score:
                print(f"Filter: Maximum score <= {args.max_score}")
            if args.include_tags:
                print(f"Filter: Include tags: {args.include_tags}")
            if args.exclude_tags:
                print(f"Filter: Exclude tags: {args.exclude_tags}")
        
        # Create filter
        post_filter = create_post_filter(args)
        
        # Extract posts
        extractor = StreamingPostExtractor(args.num_posts, post_filter)
        posts = extractor.extract_from_file(args.input_file)
        
        if not posts:
            print("No posts matched the filter criteria.", file=sys.stderr)
            sys.exit(1)
        
        # Show extraction summary
        if args.verbose:
            print(f"\nExtraction Summary:")
            print(f"  Total records processed: {extractor.total_processed}")
            print(f"  Posts extracted: {len(posts)}")
            
            if len(posts) > 0:
                # Show post type distribution
                post_types = {}
                for post in posts:
                    ptype = post.get('PostTypeId', 'Unknown')
                    post_types[ptype] = post_types.get(ptype, 0) + 1
                
                print(f"  Post type breakdown:")
                for ptype, count in sorted(post_types.items()):
                    type_name = "Questions" if ptype == "1" else "Answers" if ptype == "2" else f"Type {ptype}"
                    print(f"    {type_name}: {count}")
        
        # Format and write output XML
        formatter = TopicsFormatter()
        formatter.format_posts_to_topics_xml(posts, args.output)
        
        print(f"Successfully created Topics XML with {len(posts)} posts in '{args.output}'")
        
        if args.verbose:
            import os
            output_size = os.path.getsize(args.output) / 1024
            print(f"Output file size: {output_size:.1f} KB")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()