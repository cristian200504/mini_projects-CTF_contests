import re

def clean_output(text):
    """Deep cleaning of AI meta-talk and filler."""
    # 1. Remove introductory filler patterns (start of message only)
    fillers = [
        r"(?i)^sure,?\s*(here's?|i can|i will)[\w\s\.]*(\:|\!|\.)\s*",
        r"(?i)^certainly,?\s*",
        r"(?i)^of course,?\s*",
        r"(?i)^okay,?\s*",
        r"(?i)^i understand,?\s*",
        r"(?i)^i'd be happy to\s*[\w\s]*(\:|\!|\.)\s*",
        r"(?i)^hello!?,?\s*",
        r"(?i)^hi there!?,?\s*",
    ]
    for pattern in fillers:
        text = re.sub(pattern, "", text, count=1).strip()
    
    # 2. Remove AI meta-signatures (surgical removal)
    ai_sigs = [
        r"(?i)as an ai (model|assistant),?\s*(i (can|will|cannot))?[\w\s,]*[\.\!]\s*",
        r"(?i)as a language model,?\s*[\w\s,]*[\.\!]\s*",
        r"(?i)let me know if you need.*$",
        r"(?i)hope this helps!?.*$",
    ]
    for pattern in ai_sigs:
        text = re.sub(pattern, "", text, flags=re.MULTILINE).strip()
        
    return text.strip()

# Test cases for "Rubbish" removal
test_cases = [
    ("Sure! Here is the code you asked for:\nprint('hello')", "print('hello')"),
    ("As an AI assistant, I can help with that. The answer is 42.", "The answer is 42."),
    ("I'd be happy to help. Here is your structured list:\n- Step 1", "- Step 1"),
    ("Hello! I am a language model. How can I help you today?", ""),
    ("Okay, let me analyze that. The logic is sound.", "The logic is sound."),
    ("Certainly! I will provide the proof now.\n1+1=2\nHope this helps!", "1+1=2"),
    ("Hi there! Analysis ready:\n# Result", "# Result")
]

print("=== Quality Filter Verification ===")
for i, (original, expected) in enumerate(test_cases):
    cleaned = clean_output(original)
    status = "PASS" if cleaned == expected else "FAIL"
    print(f"Test {i+1}: {status}")
    if status == "FAIL":
        print(f"  Input: {repr(original)}")
        print(f"  Output: {repr(cleaned)}")
        print(f"  Expected: {repr(expected)}")
print("====================================")
