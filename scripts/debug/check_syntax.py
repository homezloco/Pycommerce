import re
import sys

def check_syntax(filename):
    with open(filename, 'r') as file:
        content = file.read()
    
    # Count opening and closing parentheses
    open_paren = content.count('(')
    close_paren = content.count(')')
    
    # Count opening and closing curly braces
    open_brace = content.count('{')
    close_brace = content.count('}')
    
    # Count opening and closing square brackets
    open_bracket = content.count('[')
    close_bracket = content.count(']')
    
    print(f"File: {filename}")
    print(f"Parentheses: {open_paren} open, {close_paren} close, {'balanced' if open_paren == close_paren else 'UNBALANCED'}")
    print(f"Curly Braces: {open_brace} open, {close_brace} close, {'balanced' if open_brace == close_brace else 'UNBALANCED'}")
    print(f"Square Brackets: {open_bracket} open, {close_bracket} close, {'balanced' if open_bracket == close_bracket else 'UNBALANCED'}")
    
    # Check line by line in case there's an error in a line
    lines = content.split('\n')
    
    # Check template responses for missing template names
    for i, line in enumerate(lines, 1):
        if 'return templates.TemplateResponse(' in line:
            response_line = line.strip()
            next_line = lines[i].strip() if i < len(lines) else ""
            
            # Also check for unbalanced brackets in this area
            open_p = line.count('(')
            close_p = line.count(')')
            if open_p != close_p:
                print(f"Line {i} has unbalanced parentheses: {line}")
                
                # Get the second line (potential template name)
                second_line = lines[i].strip() if i < len(lines) else ""
                if second_line:
                    print(f"  Template name line: {second_line}")
                
                # Let's see if there's an imbalance within the next 10 lines
                pending_close = open_p - close_p
                line_check = i
                while pending_close > 0 and line_check < len(lines) and line_check < i + 10:
                    line_check += 1
                    pending_close -= lines[line_check].count(')')
                if pending_close > 0:
                    print(f"  ISSUE: Still missing {pending_close} closing parentheses after 10 lines")
                
                # Check next few lines to see context
                for j in range(1, 6):
                    if i+j < len(lines):
                        print(f"  Line {i+j}: {lines[i+j]}")

if __name__ == "__main__":
    check_syntax("web_server.py")