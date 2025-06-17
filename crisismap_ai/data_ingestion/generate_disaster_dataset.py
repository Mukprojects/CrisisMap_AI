"""
Generate and load a comprehensive disaster dataset for CrisisMap AI.

This script:
1. Loads data from existing datasets 
2. Generates additional synthetic disaster data
3. Augments with research information about historic disasters
4. Loads all data into MongoDB
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import time
import pymongo
import requests
from bs4 import BeautifulSoup

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    MONGODB_URI, DB_NAME, CRISIS_COLLECTION, VECTOR_INDEX_NAME, VECTOR_DIMENSION,
    WHO_DATASET, EMDAT_DATASET, DISASTER_TWEETS, EARTHQUAKE_DATASET, EARTHQUAKE_DATA, 
    VOLCANO_DATASET, FLOODS_DATASET, TSUNAMI_DATASET, FIRE_DATASET
)
from data_ingestion.load_datasets import (
    load_who_dataset, load_emdat_dataset, load_earthquake_dataset, 
    load_volcano_dataset, load_floods_dataset, load_tsunami_dataset
)
from data_ingestion.data_processor import process_crisis_data
from embedding.embedding_generator import get_embedding_generator, generate_embedding

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define disaster types and regions for synthetic data generation
DISASTER_TYPES = [
    "Drought", "Earthquake", "Epidemic", "Extreme Temperature", "Flood", 
    "Landslide", "Storm", "Volcanic Activity", "Wildfire", "Tsunami", 
    "Hurricane", "Typhoon", "Cyclone", "Tornado", "Avalanche",
    "Blizzard", "Hailstorm", "Heat Wave", "Cold Wave", "Ice Storm"
]

REGIONS = [
    "North America", "South America", "Europe", "Africa", "Asia", 
    "Oceania", "Caribbean", "Central America", "Middle East", 
    "Southeast Asia", "Eastern Europe", "Western Europe", "Southern Europe",
    "Northern Europe", "Northern Africa", "Southern Africa", "Eastern Africa",
    "Western Africa", "Central Africa", "Central Asia", "South Asia", 
    "Eastern Asia", "Western Asia"
]

COUNTRIES = [
    "United States", "Canada", "Mexico", "Brazil", "Argentina", "Chile", 
    "Peru", "Colombia", "United Kingdom", "France", "Germany", "Italy", 
    "Spain", "Russia", "China", "Japan", "India", "Australia", "Indonesia",
    "Philippines", "Thailand", "Vietnam", "South Africa", "Nigeria", "Egypt",
    "Kenya", "Ethiopia", "Pakistan", "Bangladesh", "South Korea", "North Korea",
    "Iran", "Iraq", "Saudi Arabia", "Turkey", "Greece", "Ukraine", "Poland",
    "Sweden", "Norway", "Finland", "New Zealand", "Malaysia", "Singapore"
]

# Major historical disasters with detailed information
HISTORICAL_DISASTERS = [
    {
        "title": "2004 Indian Ocean Tsunami",
        "disaster_type": "Tsunami",
        "date": "2004-12-26",
        "location": "Indian Ocean",
        "countries_affected": ["Indonesia", "Sri Lanka", "India", "Thailand", "Malaysia", "Maldives"],
        "casualties": 227898,
        "damages_usd": 10000000000,
        "description": "One of the deadliest natural disasters in recorded history. The earthquake that caused the tsunami had a magnitude of 9.1-9.3, making it the third-largest earthquake ever recorded on a seismograph. The tsunami waves reached heights of up to 30 meters (100 ft) in some locations. The disaster prompted a worldwide humanitarian response with over $14 billion in humanitarian aid. The energy released by the earthquake was estimated to be equivalent to 23,000 atomic bombs. The long-term impacts included advancements in tsunami detection and warning systems worldwide.",
        "future_risk": "Similar tsunamis could happen again in the Indian Ocean region due to continuing subduction of the Indian Plate beneath the Burma Plate. Improved early warning systems have reduced risk but densely populated coastal regions remain highly vulnerable."
    },
    {
        "title": "Hurricane Katrina",
        "disaster_type": "Hurricane",
        "date": "2005-08-29",
        "location": "Gulf Coast of the United States",
        "countries_affected": ["United States"],
        "casualties": 1833,
        "damages_usd": 125000000000,
        "description": "Hurricane Katrina was one of the deadliest hurricanes in US history and the most destructive, causing catastrophic flooding in New Orleans when the levee system failed. At its peak, it was a Category 5 hurricane with winds up to 175 mph. The storm surge was 20-30 feet high in some areas. Over 80% of New Orleans was flooded, with some parts under 15 feet of water. The disaster exposed significant failures in disaster preparedness and response. The hurricane displaced over 1 million people from the central Gulf coast, creating one of the largest diasporas in US history.",
        "future_risk": "Climate change is likely to increase the intensity of hurricanes in the Gulf region. New Orleans remains vulnerable despite improvements to the levee system. Similar disasters could occur within the next few decades if warming trends continue."
    },
    {
        "title": "2010 Haiti Earthquake",
        "disaster_type": "Earthquake",
        "date": "2010-01-12",
        "location": "Haiti",
        "countries_affected": ["Haiti"],
        "casualties": 316000,
        "damages_usd": 8000000000,
        "description": "The earthquake had a magnitude of 7.0 Mw and its epicenter was near the town of Léogâne, approximately 25 km west of Port-au-Prince. The earthquake affected about 3 million people. More than 250,000 residences and 30,000 commercial buildings collapsed or were severely damaged. The earthquake caused major damage to Port-au-Prince, Jacmel and other settlements in the region. The country had not fully recovered from this disaster when it was hit by another major earthquake in 2021.",
        "future_risk": "Haiti lies along the Enriquillo-Plantain Garden fault system and remains at high risk for future earthquakes. Poor building standards and limited disaster preparedness infrastructure make the population extremely vulnerable to future seismic events."
    },
    {
        "title": "2011 Tōhoku Earthquake and Tsunami",
        "disaster_type": "Earthquake and Tsunami",
        "date": "2011-03-11",
        "location": "Japan",
        "countries_affected": ["Japan"],
        "casualties": 19729,
        "damages_usd": 360000000000,
        "description": "The magnitude 9.0–9.1 underwater megathrust earthquake occurred with the epicenter 72 km east of the Oshika Peninsula. It was the most powerful earthquake ever recorded in Japan, and the fourth most powerful earthquake in the world since modern record-keeping began in 1900. The tsunami waves reached heights of up to 40.5 meters (133 ft) and traveled up to 10 km (6 mi) inland. The earthquake moved Honshu (the main island of Japan) 2.4 m (8 ft) east and shifted the Earth on its axis by estimates of between 10 cm (4 in) and 25 cm (10 in). The disaster also triggered the Fukushima Daiichi nuclear disaster.",
        "future_risk": "Japan's position along the Pacific Ring of Fire means similar events could occur again. While Japan has some of the world's best earthquake preparedness systems, the combination of major seismic events with tsunamis remains a significant threat, especially to nuclear infrastructure."
    },
    {
        "title": "1931 China Floods",
        "disaster_type": "Flood",
        "date": "1931-07-01",
        "location": "China",
        "countries_affected": ["China"],
        "casualties": 4000000,
        "damages_usd": 50000000000,
        "description": "The 1931 China floods were a series of floods that occurred from June to August 1931 in China, hitting major cities such as Wuhan, Nanjing and beyond. The floods were caused by unusually high snowmelt, extraordinarily high rainfall, and several cyclones. It is generally considered the deadliest natural disaster ever recorded, and almost certainly the deadliest of the 20th century. The human suffering was immense, with diseases such as typhoid and dysentery spreading in the aftermath.",
        "future_risk": "China's major river systems including the Yangtze remain vulnerable to catastrophic flooding. Climate change is increasing the risk of extreme precipitation events. While modern flood control systems have reduced risk, unprecedented rain events could still cause disasters of significant scale."
    },
    {
        "title": "2020 Australian Bushfires",
        "disaster_type": "Wildfire",
        "date": "2019-09-01",
        "location": "Australia",
        "countries_affected": ["Australia"],
        "casualties": 34,
        "damages_usd": 103000000000,
        "description": "The 2019–20 Australian bushfire season, colloquially known as the Black Summer, was a period of bushfires in many parts of Australia, which peaked during December 2019 and January 2020. The fires burnt an estimated 18.6 million hectares (46 million acres), destroyed over 5,900 buildings (including 2,779 homes) and killed at least 34 people. Nearly 3 billion terrestrial vertebrates alone – the vast majority being reptiles – were affected and some endangered species were believed to be driven to extinction.",
        "future_risk": "Climate change is increasing the frequency and severity of bushfire conditions in Australia. Similar or worse fire seasons are likely to occur with increasing frequency in the coming decades as temperatures rise and rainfall patterns shift."
    },
    {
        "title": "COVID-19 Pandemic",
        "disaster_type": "Epidemic",
        "date": "2019-12-01",
        "location": "Global",
        "countries_affected": ["Global"],
        "casualties": 6000000,
        "damages_usd": 12700000000000,
        "description": "The COVID-19 pandemic, also known as the coronavirus pandemic, is a global pandemic of coronavirus disease 2019 (COVID-19) caused by severe acute respiratory syndrome coronavirus 2 (SARS-CoV-2). The novel virus was first identified from an outbreak in Wuhan, China, in December 2019. Attempts to contain it there failed, allowing the virus to spread worldwide. The World Health Organization (WHO) declared a Public Health Emergency of International Concern on 30 January 2020 and a pandemic on 11 March 2020. As of mid-2023, the pandemic had caused more than 760 million cases and 6.8 million confirmed deaths, making it one of the deadliest in history.",
        "future_risk": "Pandemic risk remains high globally due to factors including increased global travel, urbanization, deforestation, and climate change. Similar events could occur within the next decade, though improved surveillance systems and vaccine technologies may help mitigate impacts."
    },
    {
        "title": "2010 Pakistan Floods",
        "disaster_type": "Flood",
        "date": "2010-07-01",
        "location": "Pakistan",
        "countries_affected": ["Pakistan"],
        "casualties": 2000,
        "damages_usd": 43000000000,
        "description": "The floods began in late July 2010, resulting from heavy monsoon rains. The Indus River, which flows through Pakistan from the Himalayas to the Arabian Sea, flooded much of the country. Approximately one-fifth of Pakistan's total land area was underwater, affecting about 20 million people. The UN Secretary-General Ban Ki-moon described the floods as a 'slow-moving tsunami'. Pakistan received aid from numerous countries and international organizations.",
        "future_risk": "Climate change is increasing the intensity of monsoon rainfall in South Asia. Pakistan's geography makes it particularly vulnerable to catastrophic flooding, and similar events could occur with increasing frequency in the coming decades."
    },
    {
        "title": "2005 Kashmir Earthquake",
        "disaster_type": "Earthquake",
        "date": "2005-10-08",
        "location": "Kashmir region",
        "countries_affected": ["Pakistan", "India"],
        "casualties": 87351,
        "damages_usd": 5000000000,
        "description": "The earthquake had a magnitude of 7.6 and occurred in Pakistan-administered Azad Kashmir, near the city of Muzaffarabad. The earthquake also affected northern Pakistan and parts of India. The severe earthquake caused widespread destruction in a region that was not prepared for such a disaster. Many buildings were poorly constructed and collapsed during the earthquake. The disaster occurred in a politically sensitive region, which complicated relief efforts.",
        "future_risk": "The Kashmir region sits on active fault lines and remains at high risk for future major earthquakes. Ongoing political tensions and poor building standards in remote areas increase vulnerability to future seismic events."
    },
    {
        "title": "1970 Bhola Cyclone",
        "disaster_type": "Cyclone",
        "date": "1970-11-12",
        "location": "East Pakistan (now Bangladesh)",
        "countries_affected": ["Bangladesh", "India"],
        "casualties": 500000,
        "damages_usd": 86400000,
        "description": "The 1970 Bhola cyclone was a devastating tropical cyclone that struck East Pakistan (now Bangladesh) and India's West Bengal on November 12, 1970. It remains the deadliest tropical cyclone ever recorded and one of the deadliest natural disasters. The cyclone formed over the Bay of Bengal and made landfall with winds of up to 115 mph. The storm surge, which may have been as high as 10.4 meters (34 ft) in some areas, caused widespread flooding across the low-lying region. The disaster was a major factor in the Bangladesh Liberation War and the independence of Bangladesh from Pakistan.",
        "future_risk": "Bangladesh remains one of the most vulnerable countries to tropical cyclones and climate change is expected to increase storm intensity. Rising sea levels compound the risk, though improved early warning systems have significantly reduced fatality rates in recent decades."
    }
]

def load_existing_datasets(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load data from all existing datasets.
    
    Args:
        limit: Optional limit for each dataset
        
    Returns:
        Combined list of data from all datasets
    """
    logger.info("Loading data from existing datasets...")
    
    all_data = []
    
    try:
        # Load data from various sources
        who_data = load_who_dataset()
        logger.info(f"Loaded {len(who_data)} WHO dataset entries")
        all_data.extend(who_data)
        
        emdat_data = load_emdat_dataset()
        logger.info(f"Loaded {len(emdat_data)} EM-DAT dataset entries")
        all_data.extend(emdat_data)
        
        earthquake_data = load_earthquake_dataset(limit=limit)
        logger.info(f"Loaded {len(earthquake_data)} earthquake dataset entries")
        all_data.extend(earthquake_data)
        
        volcano_data = load_volcano_dataset(limit=limit)
        logger.info(f"Loaded {len(volcano_data)} volcano dataset entries")
        all_data.extend(volcano_data)
        
        floods_data = load_floods_dataset(limit=limit)
        logger.info(f"Loaded {len(floods_data)} floods dataset entries")
        all_data.extend(floods_data)
        
        tsunami_data = load_tsunami_dataset(limit=limit)
        logger.info(f"Loaded {len(tsunami_data)} tsunami dataset entries")
        all_data.extend(tsunami_data)
        
        logger.info(f"Loaded {len(all_data)} total entries from existing datasets")
        return all_data
        
    except Exception as e:
        logger.error(f"Error loading existing datasets: {e}")
        return []

def generate_synthetic_data(count: int = 1000) -> List[Dict[str, Any]]:
    """
    Generate synthetic disaster data.
    
    Args:
        count: Number of synthetic records to generate
        
    Returns:
        List of synthetic disaster data records
    """
    logger.info(f"Generating {count} synthetic disaster records...")
    
    synthetic_data = []
    current_year = datetime.now().year
    
    # Generate random data
    for _ in tqdm(range(count), desc="Generating synthetic data"):
        # Select random disaster type and location
        disaster_type = random.choice(DISASTER_TYPES)
        region = random.choice(REGIONS)
        country = random.choice(COUNTRIES)
        
        # Generate random date within the last 100 years
        year = random.randint(current_year - 100, current_year)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Using 28 to avoid issues with February
        date_str = f"{year}-{month:02d}-{day:02d}"
        
        # Generate random impact metrics
        casualties = random.randint(0, 10000)
        affected = random.randint(casualties, casualties * 100)
        damages_usd = random.randint(100000, 10000000000)
        
        # Generate synthetic event title
        title = f"{year} {disaster_type} in {country}"
        
        # Generate description using template
        description = f"A {disaster_type.lower()} occurred in {country} on {date_str}, affecting the {region} region. "
        
        if casualties > 0:
            description += f"The disaster resulted in {casualties} casualties and affected approximately {affected} people. "
        else:
            description += f"The disaster affected approximately {affected} people. "
            
        if damages_usd > 0:
            description += f"Economic damages were estimated at ${damages_usd:,}. "
            
        # Add random details based on disaster type
        if disaster_type == "Earthquake":
            magnitude = round(random.uniform(4.0, 9.0), 1)
            depth = random.randint(5, 50)
            description += f"The earthquake had a magnitude of {magnitude} and occurred at a depth of {depth} km. "
            
        elif disaster_type in ["Hurricane", "Typhoon", "Cyclone"]:
            wind_speed = random.randint(120, 350)
            category = random.randint(1, 5)
            description += f"The {disaster_type.lower()} reached wind speeds of {wind_speed} km/h (Category {category}). "
            
        elif disaster_type == "Flood":
            rainfall = random.randint(100, 1000)
            duration = random.randint(1, 30)
            description += f"The flooding was caused by {rainfall} mm of rainfall over {duration} days. "
            
        elif disaster_type == "Wildfire":
            area_burned = random.randint(1000, 1000000)
            description += f"The wildfire burned approximately {area_burned:,} hectares of land. "
            
        # Add random response information
        response_types = ["international aid", "emergency response", "evacuation", "relief efforts", "humanitarian assistance"]
        response = random.choice(response_types)
        description += f"The disaster prompted {response} from various organizations and governments."
        
        # Add future risk assessment
        future_risk = f"Similar {disaster_type.lower()} events could occur again in the {region} region, particularly in {country}. "
        if disaster_type in ["Hurricane", "Typhoon", "Cyclone", "Flood", "Drought", "Wildfire", "Extreme Temperature"]:
            future_risk += "Climate change is expected to increase the frequency and intensity of such events in the coming decades. "
        elif disaster_type in ["Earthquake", "Tsunami", "Volcanic Activity"]:
            future_risk += "The region remains geologically active and at risk for similar events in the future. "
        
        # Generate a detailed synthetic record
        record = {
            "title": title,
            "disaster_type": disaster_type,
            "date": date_str,
            "location": country,
            "region": region,
            "casualties": casualties,
            "affected": affected,
            "damages_usd": damages_usd,
            "description": description,
            "future_risk": future_risk,
            "source": "CrisisMap AI Synthetic Data",
            "is_synthetic": True
        }
        
        synthetic_data.append(record)
    
    logger.info(f"Generated {len(synthetic_data)} synthetic disaster records")
    return synthetic_data

def process_dataset(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process the dataset to standardize fields and add embeddings.
    
    Args:
        dataset: List of disaster data records
        
    Returns:
        Processed dataset with standardized fields and embeddings
    """
    logger.info(f"Processing {len(dataset)} dataset records...")
    
    # Get embedding generator
    embedding_generator = get_embedding_generator()
    
    processed_data = []
    for item in tqdm(dataset, desc="Processing dataset"):
        try:
            # Create standardized record
            record = {
                "title": item.get("title", "Unknown Event"),
                "disaster_type": item.get("disaster_type", item.get("event_type", item.get("type", "Unknown"))),
                "date": item.get("date", "Unknown Date"),
                "location": item.get("location", item.get("country", "Unknown Location")),
                "region": item.get("region", "Unknown Region"),
                "casualties": item.get("casualties", item.get("deaths", 0)),
                "affected": item.get("affected", 0),
                "damages_usd": item.get("damages_usd", item.get("damages", 0)),
                "description": item.get("description", "No description available."),
                "future_risk": item.get("future_risk", "No future risk assessment available."),
                "source": item.get("source", "Unknown Source"),
                "is_synthetic": item.get("is_synthetic", False),
                "timestamp": datetime.now().isoformat()
            }
            
            # Generate text for embedding
            text_for_embedding = f"{record['title']} {record['disaster_type']} {record['location']} {record['description']}"
            
            # Generate embedding
            embedding = generate_embedding(text_for_embedding, embedding_generator)
            if embedding is not None:
                record["embedding"] = embedding
                processed_data.append(record)
                
        except Exception as e:
            logger.error(f"Error processing record: {e}")
    
    logger.info(f"Successfully processed {len(processed_data)} dataset records")
    return processed_data

def upload_to_mongodb(data: List[Dict[str, Any]]) -> bool:
    """
    Upload the dataset to MongoDB.
    
    Args:
        data: List of processed disaster data records
        
    Returns:
        True if upload was successful, False otherwise
    """
    logger.info(f"Uploading {len(data)} records to MongoDB...")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        collection = db[CRISIS_COLLECTION]
        
        # Insert data in batches to avoid overwhelming the server
        batch_size = 100
        for i in tqdm(range(0, len(data), batch_size), desc="Uploading to MongoDB"):
            batch = data[i:i+batch_size]
            collection.insert_many(batch)
            time.sleep(0.1)  # Small delay to avoid overwhelming the server
        
        logger.info(f"Successfully uploaded {len(data)} records to MongoDB")
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"Error uploading to MongoDB: {e}")
        return False

def main(synthetic_count: int = 5000):
    """
    Main function to generate and load disaster dataset.
    
    Args:
        synthetic_count: Number of synthetic records to generate
    """
    logger.info("Starting comprehensive disaster dataset generation and loading...")
    
    # 1. Load existing datasets
    existing_data = load_existing_datasets()
    
    # 2. Add historical disaster data
    logger.info(f"Adding {len(HISTORICAL_DISASTERS)} historical disaster records...")
    all_data = existing_data + HISTORICAL_DISASTERS
    
    # 3. Generate synthetic data
    synthetic_data = generate_synthetic_data(count=synthetic_count)
    all_data.extend(synthetic_data)
    
    # 4. Process the complete dataset
    processed_data = process_dataset(all_data)
    
    # 5. Upload to MongoDB
    success = upload_to_mongodb(processed_data)
    
    if success:
        logger.info(f"Successfully loaded {len(processed_data)} disaster records to MongoDB")
        return True
    else:
        logger.error("Failed to load disaster dataset to MongoDB")
        return False

if __name__ == "__main__":
    # Generate and load 5000 synthetic disaster records
    main(synthetic_count=5000) 