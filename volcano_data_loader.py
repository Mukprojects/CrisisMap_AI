"""
Standalone script to load detailed volcanic eruption data into MongoDB.

This script:
1. Connects to MongoDB directly
2. Loads predefined major volcanic eruptions
3. Generates additional synthetic volcanic events
4. Processes the data with embeddings
5. Uploads all data to MongoDB

Usage:
    python volcano_data_loader.py [--count COUNT]
    
Options:
    --count COUNT    Number of additional synthetic events to generate (default: 15)
"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import argparse
import pymongo
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

# Add the project directory to the system path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import configuration from project
from crisismap_ai.config import MONGODB_URI, DB_NAME, CRISIS_COLLECTION, EMBEDDING_MODEL

# MongoDB connection settings
COLLECTION_NAME = CRISIS_COLLECTION

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Major volcanic eruption data (copied from the generator for standalone use)
MAJOR_VOLCANIC_ERUPTIONS = [
    {
        "title": "Mount Vesuvius Eruption",
        "date": "79 CE",
        "location": "Pompeii and Herculaneum",
        "country": "Italy",
        "event_type": "Volcanic Eruption",
        "vei": 5,
        "casualties": "Approximately 16,000 people",
        "text": "One of the most catastrophic volcanic eruptions in European history. The eruption buried the Roman cities of Pompeii and Herculaneum under meters of ash and pumice, preserving them in remarkable detail. The eruption was described by Pliny the Younger in letters to Tacitus, providing one of the earliest detailed accounts of a volcanic eruption. The pyroclastic flows were the main cause of death, with temperatures exceeding 300°C.",
        "impacts": "Complete destruction of Pompeii and Herculaneum. Preserved archaeological sites that provide unique insights into Roman life."
    },
    {
        "title": "Tambora Eruption",
        "date": "April 10, 1815",
        "location": "Mount Tambora, Sumbawa Island",
        "country": "Indonesia",
        "event_type": "Volcanic Eruption",
        "vei": 7,
        "casualties": "Over 100,000 people",
        "text": "The 1815 eruption of Mount Tambora was the most powerful volcanic eruption in recorded human history. The explosion was heard 2,000 km away and ash fell at least 1,300 km away. The eruption column reached a height of about 43 km. The eruption ejected an estimated 150 cubic kilometers of material. In the aftermath, a 'volcanic winter' occurred, with 1816 known as the 'Year Without a Summer' in the Northern Hemisphere.",
        "impacts": "Worldwide climate effects including global temperature decrease of 0.4-0.7°C. Crop failures across the Northern Hemisphere led to the worst famine of the 19th century."
    },
    {
        "title": "Krakatoa Eruption",
        "date": "August 27, 1883",
        "location": "Krakatoa (Krakatau), Sunda Strait",
        "country": "Indonesia",
        "event_type": "Volcanic Eruption",
        "vei": 6,
        "casualties": "Over 36,000 people",
        "text": "The 1883 eruption of Krakatoa began on August 26 and peaked the following day with four massive explosions. The final explosion was heard nearly 3,000 miles away in Perth, Australia and on Rodriguez Island, 3,000 miles to the west. The sound wave circled the Earth seven times. About 70% of the island of Krakatoa and its surrounding archipelago were destroyed. Tsunamis with waves up to 37 meters high were generated, devastating hundreds of coastal settlements.",
        "impacts": "Massive tsunamis killed the majority of victims. Global temperatures dropped by about 1.2°C in the year following the eruption. Spectacular sunsets were reported worldwide for years due to atmospheric ash."
    },
    {
        "title": "Mount St. Helens Eruption",
        "date": "May 18, 1980",
        "location": "Mount St. Helens, Washington",
        "country": "United States",
        "event_type": "Volcanic Eruption",
        "vei": 5,
        "casualties": "57 people",
        "text": "After two months of earthquakes and small eruptions, Mount St. Helens experienced a major lateral blast when the north face of the mountain collapsed. This triggered the largest landslide in recorded history and a massive eruption that reduced the mountain's height by 1,314 feet. The eruption blew down or scorched 230 square miles of forest, and released about 1.5 million metric tons of sulfur dioxide into the atmosphere.",
        "impacts": "Extensive destruction of forests, wildlife habitats, and infrastructure. Ash fell over 11 states. Total economic damage was estimated at $1.1 billion ($3.9 billion in 2023 dollars)."
    },
    {
        "title": "Mount Pinatubo Eruption",
        "date": "June 15, 1991",
        "location": "Mount Pinatubo, Luzon",
        "country": "Philippines",
        "event_type": "Volcanic Eruption",
        "vei": 6,
        "casualties": "847 people",
        "text": "After lying dormant for 500 years, Mount Pinatubo awoke with a series of major eruptions. The climactic eruption on June 15 produced the second-largest terrestrial eruption of the 20th century. The eruption ejected more than 5 cubic kilometers of material and created an ash cloud that rose 35 kilometers into the atmosphere. The eruption coincided with Typhoon Yunya, which caused ash fall to be distributed over a wider area and created massive lahars (volcanic mudflows).",
        "impacts": "Global temperatures dropped by about 0.5°C over the next two years due to the 20 million tons of sulfur dioxide released into the stratosphere. The U.S. evacuated and eventually closed Clark Air Base due to damage. Total economic impact exceeded $500 million."
    }
]

def generate_additional_volcanic_events(count: int = 10) -> List[Dict[str, Any]]:
    """Generate additional synthetic volcanic eruption events based on real data patterns."""
    volcanic_events = []
    
    # List of active volcanoes for synthetic data
    volcanoes = [
        {"name": "Mount Etna", "location": "Sicily", "country": "Italy"},
        {"name": "Stromboli", "location": "Aeolian Islands", "country": "Italy"},
        {"name": "Popocatépetl", "location": "Mexico City (near)", "country": "Mexico"},
        {"name": "Kilauea", "location": "Hawaii", "country": "United States"},
        {"name": "Mount Merapi", "location": "Java", "country": "Indonesia"},
        {"name": "Sakurajima", "location": "Kyushu", "country": "Japan"},
        {"name": "Tungurahua", "location": "Andes", "country": "Ecuador"},
        {"name": "Fuego", "location": "Antigua", "country": "Guatemala"},
        {"name": "Mount Yasur", "location": "Tanna Island", "country": "Vanuatu"},
        {"name": "Erta Ale", "location": "Afar Region", "country": "Ethiopia"}
    ]
    
    # Types of volcanic activity
    activity_types = [
        "Strombolian eruption",
        "Phreatic eruption",
        "Lava dome collapse",
        "Pyroclastic flow",
        "Lava flow",
        "Ash emission",
        "Volcanic gas release",
        "Phreatomagmatic eruption",
        "Lava fountain",
        "Lahars (volcanic mudflows)"
    ]
    
    # Impacts of volcanic eruptions
    impacts = [
        "Evacuation of nearby communities",
        "Air traffic disruptions due to ash clouds",
        "Destruction of agricultural land",
        "Road closures due to ash fall",
        "Tourism industry affected",
        "Respiratory health issues reported in nearby communities",
        "Structural damage to buildings from ash accumulation",
        "Water supply contamination",
        "Power outages from damaged infrastructure",
        "Forest fires ignited by hot volcanic material"
    ]
    
    # Generate synthetic eruption events
    for i in range(count):
        # Select a random volcano
        volcano = random.choice(volcanoes)
        
        # Generate a random date in the past 50 years
        years_back = random.randint(0, 50)
        months_back = random.randint(0, 11)
        days_back = random.randint(0, 28)
        eruption_date = (datetime.now() - timedelta(days=years_back*365 + months_back*30 + days_back)).strftime("%Y-%m-%d")
        
        # Generate a random VEI (Volcanic Explosivity Index)
        vei = random.choices([1, 2, 3, 4, 5], weights=[0.35, 0.3, 0.2, 0.1, 0.05])[0]
        
        # Generate random activity type
        activity = random.choice(activity_types)
        
        # Generate title
        title = f"{volcano['name']} Volcanic Activity - {activity}"
        
        # Generate casualty information based on VEI
        if vei <= 2:
            casualties = "0 reported casualties"
        elif vei == 3:
            casualties = f"{random.randint(0, 10)} casualties reported"
        elif vei == 4:
            casualties = f"{random.randint(10, 100)} casualties reported"
        else:
            casualties = f"{random.randint(100, 1000)} casualties reported"
        
        # Select random impacts based on VEI
        num_impacts = min(vei + 1, len(impacts))
        selected_impacts = random.sample(impacts, num_impacts)
        impacts_text = "; ".join(selected_impacts)
        
        # Generate description text
        description = f"The {volcano['name']} volcano in {volcano['location']}, {volcano['country']} experienced a {activity.lower()} on {eruption_date}. "
        description += f"The event registered as a VEI {vei} eruption on the Volcanic Explosivity Index. "
        
        if vei <= 2:
            description += "This was a relatively minor eruption with limited local impacts. "
        elif vei == 3:
            description += "This moderate eruption caused significant local disruption. "
        elif vei == 4:
            description += "This was a major eruption with regional impacts and international attention. "
        else:
            description += "This was a severe eruption with widespread devastation and potential global climate effects. "
        
        description += f"Local authorities responded with appropriate measures based on the volcano's activity level. {casualties}."
        
        # Create the event
        event = {
            "title": title,
            "date": eruption_date,
            "location": volcano["location"],
            "country": volcano["country"],
            "event_type": "Volcanic Eruption",
            "vei": vei,
            "casualties": casualties,
            "text": description,
            "impacts": impacts_text
        }
        
        volcanic_events.append(event)
    
    return volcanic_events

def generate_embeddings(texts: List[str], model_name: str = EMBEDDING_MODEL) -> List[List[float]]:
    """Generate embeddings for a list of texts using a sentence transformer model."""
    try:
        logger.info(f"Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        
        # Generate embeddings in batches
        embeddings = []
        batch_size = 32
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings.tolist())
            
        logger.info(f"Generated {len(embeddings)} embeddings successfully")
        return embeddings
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Return empty embeddings as fallback
        return [[] for _ in range(len(texts))]

def process_volcanic_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process volcanic eruption data and add embeddings."""
    try:
        logger.info(f"Processing {len(data)} volcanic eruption records...")
        
        # Extract text for embeddings
        texts = []
        for event in data:
            # Combine title, text, and other fields for a richer embedding
            text_parts = []
            if "title" in event and event["title"]:
                text_parts.append(event["title"])
            if "text" in event and event["text"]:
                text_parts.append(event["text"])
            if "impacts" in event and event["impacts"]:
                text_parts.append(event["impacts"])
                
            combined_text = " ".join(text_parts)
            texts.append(combined_text)
        
        # Generate embeddings
        embeddings = generate_embeddings(texts)
        
        # Add embeddings to data
        for i, event in enumerate(data):
            event["embedding"] = embeddings[i]
            
            # Clean up date formats if needed
            if "date" in event:
                try:
                    # If it's already a proper date format, keep it
                    if not isinstance(event["date"], str) or any(c.isalpha() for c in event["date"]):
                        pass
                    else:
                        # Try to parse and standardize date format
                        date_obj = datetime.strptime(event["date"], "%Y-%m-%d")
                        event["date"] = date_obj.strftime("%Y-%m-%d")
                except:
                    # If date parsing fails, leave it as is
                    pass
            
            # Make sure event_type is always "Volcanic Eruption"
            event["event_type"] = "Volcanic Eruption"
            
            # Add any missing fields
            if "summary" not in event and "text" in event:
                # Create a simple summary (first sentence or first 100 chars)
                text = event["text"]
                if "." in text:
                    summary = text.split(".")[0] + "."
                else:
                    summary = text[:min(100, len(text))]
                event["summary"] = summary
        
        logger.info(f"Processed {len(data)} volcanic eruption records successfully")
        return data
    
    except Exception as e:
        logger.error(f"Error processing volcanic data: {e}")
        return data

def upload_to_mongodb(data: List[Dict[str, Any]]) -> None:
    """Upload processed volcanic eruption data to MongoDB."""
    try:
        logger.info(f"Connecting to MongoDB at {MONGODB_URI}")
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        logger.info(f"Connected to MongoDB database '{DB_NAME}', collection '{COLLECTION_NAME}'")
        
        # Upload data in batches
        batch_size = 20
        total_uploaded = 0
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            result = collection.insert_many(batch)
            total_uploaded += len(result.inserted_ids)
            logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(data) + batch_size - 1)//batch_size} ({len(batch)} records)")
        
        logger.info(f"Successfully uploaded {total_uploaded} volcanic eruption records to MongoDB")
        
    except Exception as e:
        logger.error(f"Error uploading data to MongoDB: {e}")
        raise
    finally:
        if 'client' in locals():
            client.close()
            logger.info("MongoDB connection closed")

def main(additional_count: int = 15):
    """Generate, process, and upload volcanic eruption data."""
    try:
        logger.info("Starting volcanic eruption dataset generation...")
        
        # Combine major historical eruptions with synthetic data
        all_volcanic_data = MAJOR_VOLCANIC_ERUPTIONS.copy()
        
        if additional_count > 0:
            logger.info(f"Generating {additional_count} additional synthetic volcanic events...")
            synthetic_data = generate_additional_volcanic_events(additional_count)
            all_volcanic_data.extend(synthetic_data)
        
        logger.info(f"Total volcanic eruption records: {len(all_volcanic_data)}")
        
        # Process data (add embeddings, clean up, etc.)
        processed_data = process_volcanic_data(all_volcanic_data)
        
        # Upload to MongoDB
        upload_to_mongodb(processed_data)
        
        logger.info("Volcanic eruption data generation and upload complete!")
        
    except Exception as e:
        logger.error(f"Error in volcanic data generation process: {e}")
        logger.error("Try running the script again with fewer records or check MongoDB connection")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and load volcanic eruption data to MongoDB")
    parser.add_argument("--count", type=int, default=15, help="Number of additional synthetic volcanic events to generate")
    
    args = parser.parse_args()
    
    print(f"Starting volcanic data loader with {args.count} synthetic records...")
    main(args.count)
    print("Volcanic data loading complete!")