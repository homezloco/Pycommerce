#!/bin/bash

# File paths
file="web_server.py"

# Find lines with template responses that don't already have tinymce_api_key
grep -n "templates.TemplateResponse" $file | while read -r line; do
    line_num=$(echo $line | cut -d':' -f1)
    context=$(tail -n +$line_num $file | head -n 15)
    
    # Check if this template response already has tinymce_api_key
    if ! echo "$context" | grep -q "tinymce_api_key"; then
        # Get line number of closing brace
        close_line=$(echo "$context" | grep -n "}" | head -1 | cut -d':' -f1)
        close_line=$((line_num + close_line - 1))
        
        # Insert tinymce_api_key before the closing brace
        sed -i "${close_line}i\ \ \ \ \ \ \ \ \ \ \ \ \"tinymce_api_key\": tinymce_api_key," $file
    fi
done
