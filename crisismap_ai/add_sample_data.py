#!/usr/bin/env python3
"""
Add sample crisis data to the database for testing.
"""
import sys
from pathlib import Path
import datetime

# Add parent directory to path
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from crisismap_ai.database.db_operations import get_crisis_event_ops

def add_sample_data():
    """Add sample crisis events to the database."""
    print("Adding sample crisis data...")
    
    # Get database operations
    crisis_ops = get_crisis_event_ops()
    
    # Sample crisis events
    sample_events = [
        {
            'title': 'India-Pakistan Border Tensions Escalate',
            'summary': 'Recent military activities along the Line of Control have raised concerns about escalating tensions between India and Pakistan. Both nations have increased troop deployments.',
            'category': 'Conflict',
            'location': 'Kashmir, India-Pakistan Border',
            'date': datetime.datetime.now(),
            'source': 'Sample Data',
            'severity': 'High',
            'affected_population': 50000,
            'description': 'Cross-border shelling and military buildup reported along the disputed Kashmir region.'
        },
        {
            'title': 'Current India-Pakistan Conflict Analysis',
            'summary': 'Analysis of ongoing tensions between India and Pakistan including recent diplomatic efforts and military posturing.',
            'category': 'Conflict',
            'location': 'India-Pakistan Border',
            'date': datetime.datetime.now(),
            'source': 'Sample Data',
            'severity': 'High',
            'affected_population': 75000,
            'description': 'Comprehensive analysis of current India-Pakistan relations and border situation.'
        },
        {
            'title': 'Earthquake Strikes Northern India',
            'summary': 'A magnitude 6.2 earthquake hit northern India, causing damage to buildings and infrastructure.',
            'category': 'Natural Disaster',
            'location': 'Himachal Pradesh, India',
            'date': datetime.datetime.now(),
            'source': 'Sample Data',
            'severity': 'Medium',
            'affected_population': 100000,
            'description': 'Earthquake caused structural damage in several districts with reports of casualties.'
        },
        {
            'title': 'Monsoon Floods in Pakistan',
            'summary': 'Heavy monsoon rains have caused severe flooding in southern Pakistan, displacing thousands.',
            'category': 'Natural Disaster',
            'location': 'Sindh Province, Pakistan',
            'date': datetime.datetime.now(),
            'source': 'Sample Data',
            'severity': 'High',
            'affected_population': 200000,
            'description': 'Widespread flooding has affected agricultural areas and urban centers.'
        },
        {
            'title': 'Hello World Crisis Event',
            'summary': 'A test crisis event to respond to hello queries.',
            'category': 'Test',
            'location': 'Global',
            'date': datetime.datetime.now(),
            'source': 'Sample Data',
            'severity': 'Low',
            'affected_population': 1,
            'description': 'This is a test event for hello queries.'
        }
    ]
    
    # Insert sample events
    inserted_count = 0
    for event in sample_events:
        try:
            result = crisis_ops.insert_crisis_event(event)
            print(f"✅ Inserted event: {event['title']}")
            inserted_count += 1
        except Exception as e:
            print(f"❌ Error inserting {event['title']}: {e}")
    
    print(f"\nSample data insertion completed! Inserted {inserted_count} events.")
    return inserted_count

if __name__ == "__main__":
    add_sample_data()