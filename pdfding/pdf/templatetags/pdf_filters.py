from django import template

register = template.Library()

@register.filter
def find_substring(value, substring):
    """Find the position of a substring in a string, returns -1 if not found"""
    if not value or not substring:
        return -1
    try:
        return value.find(substring)
    except:
        return -1

@register.filter
def extract_selected_text(value):
    """Extract selected text from combined question format"""
    if not value:
        return ""
    
    try:
        # Look for the pattern where selected text ends and question begins
        # Handle various line ending formats
        selected_start_marker = 'Selected text: "'
        if selected_start_marker not in value:
            return ""
            
        selected_start = value.find(selected_start_marker) + len(selected_start_marker)
        
        # Look for any of the possible endings (handle both quoted and unquoted formats)
        possible_endings = ['"\r\nQuestion:', '"\nQuestion:', '" Question:', '"\r\nQuestion', '"\nQuestion', '" Question']
        
        selected_end = -1
        for ending in possible_endings:
            pos = value.find(ending, selected_start)
            if pos > selected_start:
                selected_end = pos
                break
        
        if selected_end > selected_start:
            return value[selected_start:selected_end]
    except:
        pass
    
    return ""

@register.filter
def extract_actual_question(value):
    """Extract actual question from combined question format"""
    if not value:
        return value
    
    try:
        # Look for where question starts (after the selected text part)
        # Handle various question markers
        question_start_positions = []
        
        # Find all possible question start positions
        # Handle quoted format: "...\r\nQuestion:
        quoted_markers = ['"\r\nQuestion:', '"\nQuestion:', '" Question:']
        for marker in quoted_markers:
            pos = value.find(marker)
            if pos >= 0:
                # Position after the marker
                question_start = pos + len(marker)
                question_start_positions.append((question_start, pos))
        
        # Handle unquoted format: ...\r\nQuestion:
        unquoted_markers = ['\r\nQuestion:', '\nQuestion:', ' Question:']
        for marker in unquoted_markers:
            # Look for Selected text: " first
            selected_pos = value.find('Selected text: "')
            if selected_pos >= 0:
                # Look for the marker after Selected text
                pos = value.find(marker, selected_pos)
                if pos >= 0:
                    question_start = pos + len(marker)
                    question_start_positions.append((question_start, pos))
        
        if question_start_positions:
            # Use the first valid position
            question_start_positions.sort()
            question_start = question_start_positions[0][0]
            
            # Look for where answer starts (handle various formats)
            answer_markers = ['\nA:', '\r\nA:', ' A:', 'A:']
            answer_start = -1
            
            for marker in answer_markers:
                pos = value.find(marker, question_start)
                if pos > question_start:
                    answer_start = pos
                    break
            
            if answer_start > question_start:
                result = value[question_start:answer_start].strip()
                # Remove any leading colon if present
                if result.startswith(':'):
                    result = result[1:].strip()
                return result
            else:
                result = value[question_start:].strip()
                # Remove any leading colon if present
                if result.startswith(':'):
                    result = result[1:].strip()
                return result
    except:
        pass
    
    return value

@register.filter
def has_selected_text(value):
    """Check if the question contains selected text"""
    if not value:
        return False
    
    # Check if it contains the pattern indicating combined format
    selected_start_marker = 'Selected text: "'
    question_markers = ['"\r\nQuestion:', '"\nQuestion:', '" Question:', '"\r\nQuestion', '"\nQuestion', '" Question']
    
    if selected_start_marker not in value:
        return False
    
    # Check if any question marker exists after the selected text start
    for marker in question_markers:
        if marker in value:
            return True
    
    # Also check for unquoted format
    unquoted_markers = ['\r\nQuestion:', '\nQuestion:', ' Question:']
    for marker in unquoted_markers:
        if marker in value:
            # Make sure there's "Selected text: " before this marker
            selected_pos = value.find('Selected text: ')
            marker_pos = value.find(marker)
            if selected_pos >= 0 and marker_pos > selected_pos:
                return True
    
    return False
