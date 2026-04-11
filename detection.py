import collections
import difflib

def calculate_similarity(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, str(a), str(b)).ratio()

def detect_loop(events, window_size=3):
    """
    Detects repeating sequences of actions and similar inputs.
    """
    if len(events) < window_size * 2:
        return False
    
    # Extract action sequence
    actions = [e.action for e in events]
    inputs = [e.input_data for e in events]
    
    # Check for repeating patterns of length 'window_size'
    for i in range(len(actions) - window_size * 2 + 1):
        window1_actions = actions[i : i + window_size]
        window2_actions = actions[i + window_size : i + window_size * 2]
        
        if window1_actions == window2_actions:
            # Actions match, now check input similarity
            similarities = [
                calculate_similarity(inputs[i + j], inputs[i + window_size + j])
                for j in range(window_size)
            ]
            # If inputs are mostly similar, it's a loop
            if sum(similarities) / window_size > 0.7:
                return True
                
    return False

def detect_drift(events):
    """
    Detects if the agent's intent or action pattern has shifted significantly.
    """
    if len(events) < 10:
        return False
        
    mid = len(events) // 2
    first_half = events[:mid]
    second_half = events[mid:]
    
    def get_dist(evs):
        counts = collections.Counter([e.action for e in evs])
        total = len(evs)
        return {k: v/total for k, v in counts.items()}
    
    dist1 = get_dist(first_half)
    dist2 = get_dist(second_half)
    
    # Calculate drift as sum of absolute differences in probabilities
    all_keys = set(dist1.keys()) | set(dist2.keys())
    drift_score = sum(abs(dist1.get(k, 0) - dist2.get(k, 0)) for k in all_keys)
    
    # Threshold for drift
    return drift_score > 0.8

def detect_failure(events, threshold=0.4, consecutive_limit=3):
    """
    Detects consecutive failures or high failure rate.
    """
    if not events:
        return False
        
    failures = 0
    consecutive_failures = 0
    max_consecutive = 0
    
    for e in events:
        import json
        meta = json.loads(e.metadata_json) if e.metadata_json else {}
        if meta.get('status') == 'failure':
            failures += 1
            consecutive_failures += 1
            max_consecutive = max(max_consecutive, consecutive_failures)
        else:
            consecutive_failures = 0
            
    failure_rate = failures / len(events)
    
    return max_consecutive >= consecutive_limit or failure_rate >= threshold

def analyze_session(session_events):
    """
    Runs all detection logic and returns a status.
    """
    # Sort events by step/timestamp to be robust against out-of-order ingestion
    sorted_events = sorted(session_events, key=lambda x: (x.step, x.timestamp))
    
    if detect_failure(sorted_events):
        return 'failing'
    if detect_loop(sorted_events):
        return 'looping'
    if detect_drift(sorted_events):
        return 'drifting'
    
    return 'healthy'
