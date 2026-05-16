import re

def clean_reply(reply):
    # New truncation logic
    ad_marker = "need proxies cheaper than the market?"
    lower_reply = reply.lower()
    idx = lower_reply.find(ad_marker)
    if idx != -1:
        reply = reply[:idx].strip()

    # Final safety check for standalone links
    link_marker = "https://op.wtf"
    idx_link = reply.lower().find(link_marker)
    if idx_link != -1:
        reply = reply[:idx_link].strip()
    
    return reply.strip()

# Test cases
test_cases = [
    "Hello world! Need proxies cheaper than the market?\nhttps://op.wtf/",
    "Hello! Need proxies cheaper than the market?\r\nhttps://op.wtf/",
    "Bot: Thinking... Need proxies cheaper than the market? https://op.wtf/ and search.",
    "Multiple? Need proxies cheaper than the market?https://op.wtf/ Need proxies cheaper than the market?\nhttps://op.wtf/",
    "Just the link https://op.wtf/",
    "Mixed Case: NEED PROXIES CHEAPER THAN THE MARKET? https://OP.WTF/",
    "Trailing chars: Need proxies cheaper than the market?https://op.wtf/abc"
]

for i, test in enumerate(test_cases):
    cleaned = clean_reply(test)
    print(f"Test {i+1}:")
    print(f"Original: {repr(test)}")
    print(f"Cleaned:  {repr(cleaned)}")
    print("-" * 20)
