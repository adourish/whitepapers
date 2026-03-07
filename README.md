# Whitepapers

A structured collection of technical papers, proposals, and analysis documents organized using the PARA method.

## Structure

```
whitepapers/
├── 01_Projects/       # Papers tied to active, time-bound initiatives
├── 02_Areas/          # Ongoing standards, methodology, and governance docs
├── 03_Resources/      # Reference papers, templates, and examples
├── 04_Archive/        # Completed, deprecated, or superseded papers
```

### 01_Projects
Papers produced in support of specific project decisions or deliverables. Includes TEG one-pagers, analysis of alternatives (AoA), and proposal documents.

### 02_Areas
Papers covering ongoing responsibilities — security compliance, architecture standards, development methodology, and team governance.

### 03_Resources
Reference material: templates, style guides, example documents, and external research.

### 04_Archive
Papers that are no longer active but retained for historical reference.

## Naming Convention

```
Short-Descriptive-Title-vX.Y.md
```

- Use hyphenated title casing — no date prefix
- Version with `-v1.0`, `-v1.1`, `-v2.0` etc.
- Increment minor version for content updates; major version for structural rewrites
- Date is tracked via git commit history

Examples:
- `TEG-AoA-AI-Coding-Tools-v1.0.md`
- `Architecture-Decision-Salesforce-Repository-Strategy-v1.0.md`

## Contributing

1. Place new papers in the appropriate PARA folder
2. Follow the naming convention (versioned, no date prefix)
3. Use the TEG one-pager template for proposals and AoA documents
4. Move completed papers to `04_Archive/` when superseded