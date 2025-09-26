# Math Stack Exchange XML Parser

Efficient parsers for extracting posts from large Math Stack Exchange XML dumps using memory-efficient streaming techniques.

## Parsers

- **`parser.py`** - Simple extraction with year filtering and standard XML output
- **`parser2.py`** - Advanced filtering with Topics XML format for ML/research

## Quick Start

### Basic Parser (`parser.py`)

Extract posts with optional year filtering:

```bash
# Extract 100 posts
python3 parser.py Posts.xml 100

# Extract 50 posts from 2015-2020
python3 parser.py Posts.xml 50 --min-year 2015 --max-year 2020 -v

# Extract 25 posts from specific years
python3 parser.py Posts.xml 25 --years 2013,2016,2019 -v
```

**Options:**
- `-o, --output` - Output file name (default: extracted_posts.xml)
- `-v, --verbose` - Enable progress reporting
- `--min-year YYYY` - Filter from year onwards
- `--max-year YYYY` - Filter up to year
- `--years Y1,Y2` - Filter specific years only

### Advanced Parser (`parser2.py`)

Extract with comprehensive filtering and Topics XML format:

```bash
# Extract 100 questions with community approval
python3 parser2.py Posts.xml 100 --questions-only --min-score 10 -v

# Extract high-quality calculus posts from recent years
python3 parser2.py Posts.xml 50 --include-tags calculus --min-score 20 --min-year 2018 -v

# Extract diverse ML training dataset
python3 parser2.py Posts.xml 200 --questions-only --min-score 8 --min-answers 1 --exclude-tags homework -v
```

**Key Filtering Options:**
- `--questions-only / --answers-only` - Filter by post type
- `--min-score N` - Minimum community score
- `--min-answers N` - Minimum number of answers (questions only)
- `--include-tags tag1,tag2` - Include specific mathematical topics
- `--exclude-tags tag1,tag2` - Exclude unwanted content
- `--min-year / --max-year` - Year range filtering
- `--years Y1,Y2` - Specific years only

## Output Formats

### Standard Format (`parser.py`)
```xml
<posts>
  <row Id="1" PostTypeId="1" Title="Question Title" Tags="&lt;calculus&gt;" Score="25" ... />
</posts>
```

### Topics Format (`parser2.py`) 
```xml
<Topics>
  <Topic number="A.1">
    <Title>Question Title</Title>
    <Question>
      <Body>Question content...</Body>
      <Score>25</Score>
      <Tags>calculus</Tags>
    </Question>
  </Topic>
</Topics>
```

## Use Cases

**`parser.py` - Best for:**
- Simple data extraction
- When you need standard XML format
- Basic year-based filtering
- Quick analysis tasks

**`parser2.py` - Best for:**
- ML training datasets
- Research with quality filtering
- Topic-specific extraction
- Human-readable XML format

## Examples

### Research Dataset
```bash
python3 parser2.py Posts.xml 1000 --questions-only --min-score 8 --min-year 2011 --max-year 2024 --min-answers 1 --exclude-tags homework -v -o research_dataset.xml
```

### Subject-Specific Collection
```bash
python3 parser2.py Posts.xml 150 --include-tags linear-algebra,calculus --min-score 15 --questions-only -v
```

### Temporal Analysis
```bash
python3 parser.py Posts.xml 200 --years 2012,2015,2018,2021 -v -o temporal_sample.xml
```

## Requirements

- Python 3.6+
- No external dependencies (uses standard library)

## Performance

- **Memory efficient**: Processes large files without loading into memory
- **Fast extraction**: Stops once target count reached
- **Progress reporting**: Shows extraction progress for large datasets

Both parsers are optimized for handling multi-GB XML dumps efficiently.