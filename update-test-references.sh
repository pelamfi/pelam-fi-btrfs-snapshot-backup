#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFERENCES_DIR="$SCRIPT_DIR/tests/references"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
Update Test References Script

This script helps update reference files for integration tests.

Usage:
    $(basename "$0") [OPTIONS] [PATTERN]

Options:
    -h, --help     Show this help message
    -l, --list     List all .actual.txt files without updating
    -d, --diff     Show diff between .actual.txt and .txt files
    -y, --yes      Auto-approve all updates (no prompts)

Arguments:
    PATTERN        Optional glob pattern to match specific test files
                   (e.g., "backup_*" or "snapshot_single_pair")

Examples:
    $(basename "$0")                    # Interactive update of all .actual.txt files
    $(basename "$0") -l                 # List all .actual.txt files
    $(basename "$0") -d                 # Show diffs for all files
    $(basename "$0") backup_*           # Update only backup-related tests
    $(basename "$0") -y                 # Update all files without prompting

EOF
}

list_actual_files() {
    local pattern="${1:-*}"
    local found=false
    
    echo -e "${BLUE}📋 Found .actual.txt files:${NC}"
    
    for actual_file in "$REFERENCES_DIR"/${pattern}.actual.txt; do
        if [[ -f "$actual_file" ]]; then
            found=true
            local basename=$(basename "$actual_file" .actual.txt)
            local ref_file="$REFERENCES_DIR/${basename}.txt"
            
            if [[ -f "$ref_file" ]]; then
                echo -e "  ${YELLOW}UPDATE${NC} $basename"
            else
                echo -e "  ${GREEN}NEW${NC}    $basename"
            fi
        fi
    done
    
    if [[ "$found" == false ]]; then
        echo -e "  ${RED}No .actual.txt files found${NC}"
        if [[ "${1:-}" != "*" ]]; then
            echo -e "  ${YELLOW}Pattern: ${1}${NC}"
        fi
    fi
}

show_diff() {
    local actual_file="$1"
    local basename=$(basename "$actual_file" .actual.txt)
    local ref_file="$REFERENCES_DIR/${basename}.txt"
    
    echo -e "\n${BLUE}📄 Diff for ${basename}:${NC}"
    
    if [[ -f "$ref_file" ]]; then
        if diff -u "$ref_file" "$actual_file" | head -20; then
            echo -e "${GREEN}  ✓ Files are identical${NC}"
        fi
    else
        echo -e "${YELLOW}  📝 New reference file (no existing .txt file)${NC}"
        echo -e "${BLUE}  Content preview:${NC}"
        head -10 "$actual_file" | sed 's/^/    /'
        if [[ $(wc -l < "$actual_file") -gt 10 ]]; then
            echo "    ..."
        fi
    fi
}

update_reference() {
    local actual_file="$1"
    local auto_approve="${2:-false}"
    local basename=$(basename "$actual_file" .actual.txt)
    local ref_file="$REFERENCES_DIR/${basename}.txt"
    
    if [[ "$auto_approve" == false ]]; then
        echo -e "\n${YELLOW}Update reference for ${basename}?${NC}"
        if [[ -f "$ref_file" ]]; then
            echo -e "  This will ${RED}overwrite${NC} the existing reference file."
        else
            echo -e "  This will ${GREEN}create${NC} a new reference file."
        fi
        
        read -p "Continue? [y/N] " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "  ${YELLOW}Skipped${NC}"
            return
        fi
    fi
    
    cp "$actual_file" "$ref_file"
    rm "$actual_file"
    echo -e "  ${GREEN}✓ Updated${NC} $basename"
}

main() {
    local auto_approve=false
    local show_diffs=false
    local list_only=false
    local pattern="*"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -l|--list)
                list_only=true
                shift
                ;;
            -d|--diff)
                show_diffs=true
                shift
                ;;
            -y|--yes)
                auto_approve=true
                shift
                ;;
            -*)
                echo -e "${RED}Unknown option: $1${NC}" >&2
                echo "Use --help for usage information."
                exit 1
                ;;
            *)
                pattern="$1"
                shift
                ;;
        esac
    done
    
    # Check if references directory exists
    if [[ ! -d "$REFERENCES_DIR" ]]; then
        echo -e "${RED}❌ References directory not found: $REFERENCES_DIR${NC}" >&2
        exit 1
    fi
    
    cd "$REFERENCES_DIR"
    
    # List mode
    if [[ "$list_only" == true ]]; then
        list_actual_files "$pattern"
        exit 0
    fi
    
    # Check for .actual.txt files
    local found_files=()
    
    # Use proper globbing to find files
    shopt -s nullglob  # Don't include non-matching patterns
    for file in ${pattern}.actual.txt; do
        if [[ -f "$file" ]]; then
            found_files+=("$file")
        fi
    done
    shopt -u nullglob
    
    if [[ ${#found_files[@]} -eq 0 ]]; then
        echo -e "${GREEN}✅ No .actual.txt files found to update${NC}"
        if [[ "$pattern" != "*" ]]; then
            echo -e "   Pattern: ${pattern}"
        fi
        exit 0
    fi
    
    echo -e "${BLUE}🔄 Found ${#found_files[@]} reference file(s) to update${NC}"
    
    # Show diffs if requested
    if [[ "$show_diffs" == true ]]; then
        for actual_file in "${found_files[@]}"; do
            show_diff "$actual_file"
        done
        
        if [[ "$auto_approve" == false ]]; then
            echo -e "\n${YELLOW}Proceed with updates?${NC}"
            read -p "Continue? [y/N] " -n 1 -r
            echo
            
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}Cancelled${NC}"
                exit 0
            fi
        fi
    fi
    
    # Update files
    for actual_file in "${found_files[@]}"; do
        update_reference "$actual_file" "$auto_approve"
    done
    
    echo -e "\n${GREEN}✅ Reference files updated successfully!${NC}"
    if [[ ${#found_files[@]} -gt 0 ]]; then
        echo -e "${BLUE}📝 Don't forget to commit the updated reference files${NC}"
    fi
}

main "$@"
