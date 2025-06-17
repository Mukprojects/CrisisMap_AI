"""
Generate and load detailed volcanic eruption data for CrisisMap AI.

This script:
1. Creates a comprehensive dataset of major volcanic eruptions
2. Processes the data and generates embeddings
3. Loads the data into MongoDB
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

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import MONGODB_URI, DB_NAME, COLLECTION_NAME
from database.db_connection import get_db_connection
from database.db_operations import get_crisis_event_ops
from embedding.embedding_generator import get_embedding_generator
from data_ingestion.data_processor import process_crisis_events

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample volcanic eruption data
MAJOR_VOLCANIC_ERUPTIONS = [
    {
        "title": "Mount Vesuvius Eruption",
        "date": "79 CE",
        "location": "Pompeii and Herculaneum",
        "country": "Italy",
        "event_type": "Volcanic Eruption",
        "vei": 5,  # Volcanic Explosivity Index
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
        "vei": 7,  # Largest eruption in recorded history
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
    },
    {
        "title": "Eyjafjallajökull Eruption",
        "date": "April 14, 2010",
        "location": "Eyjafjallajökull, Southern Region",
        "country": "Iceland",
        "event_type": "Volcanic Eruption",
        "vei": 4,
        "casualties": "0 direct deaths",
        "text": "The eruption of the Eyjafjallajökull volcano in Iceland created an ash cloud that severely disrupted air travel across western and northern Europe for six days. While relatively modest in size, the eruption had a tremendous impact due to the ash plume being carried directly toward Europe, combined with the decision by aviation authorities to close airspace due to the potential danger to aircraft engines.",
        "impacts": "Over 100,000 flights were cancelled, affecting more than 10 million passengers. Economic losses were estimated at $1.7 billion for the airline industry alone. The eruption demonstrated the vulnerability of modern aviation systems to volcanic ash."
    },
    {
        "title": "Hunga Tonga–Hunga Haʻapai Eruption",
        "date": "January 15, 2022",
        "location": "Hunga Tonga–Hunga Haʻapai",
        "country": "Tonga",
        "event_type": "Volcanic Eruption",
        "vei": 5,
        "casualties": "4 people",
        "text": "The underwater eruption of Hunga Tonga–Hunga Haʻapai was one of the most explosive volcanic events of the modern era. It generated tsunamis up to 15 meters high in Tonga and tsunamis that affected the entire Pacific basin. The eruption cloud reached a height of 58 km, the highest ever recorded. The atmospheric shock wave traveled around the world multiple times and was detected by weather stations worldwide.",
        "impacts": "Devastating tsunami damage in Tonga. Underwater communication cables were severed, isolating Tonga from the rest of the world for weeks. The eruption injected an unprecedented amount of water vapor into the stratosphere, which may have climate effects for years."
    },
    {
        "title": "Nevado del Ruiz Eruption",
        "date": "November 13, 1985",
        "location": "Nevado del Ruiz, Andes",
        "country": "Colombia",
        "event_type": "Volcanic Eruption",
        "vei": 3,
        "casualties": "23,000 people",
        "text": "Despite its relatively small size, the 1985 eruption of Nevado del Ruiz became the second-deadliest volcanic disaster of the 20th century. The eruption melted the mountain's glaciers, creating massive lahars (volcanic mudflows) that swept down river valleys. The town of Armero was buried under 5 meters of mud and debris, killing about 20,000 of its 29,000 inhabitants.",
        "impacts": "The disaster highlighted the importance of early warning systems and proper disaster planning. Despite warning signs for months before the eruption, no adequate evacuation plans were implemented."
    },
    {
        "title": "Mount Unzen Eruption",
        "date": "June 3, 1991",
        "location": "Mount Unzen, Kyushu",
        "country": "Japan",
        "event_type": "Volcanic Eruption",
        "vei": 3,
        "casualties": "43 people",
        "text": "After 198 years of dormancy, Mount Unzen became active again in 1990. On June 3, 1991, a pyroclastic flow killed 43 people, including volcanologists Maurice and Katia Krafft and Harry Glicken, along with journalists who were documenting the volcano's activity. The eruption continued until 1995, making it the longest volcanic eruption in Japan's history.",
        "impacts": "Thousands of people were evacuated from nearby areas. The loss of prominent volcanologists impacted the field of volcanology and led to improved safety protocols for researchers."
    },
    {
        "title": "Kilauea Eruption",
        "date": "May 3, 2018",
        "location": "Kilauea, Hawaii",
        "country": "United States",
        "event_type": "Volcanic Eruption",
        "vei": 3,
        "casualties": "0 direct deaths",
        "text": "The 2018 lower Puna eruption of Kilauea volcano in Hawaii was the most destructive volcanic event in the United States since the 1980 eruption of Mount St. Helens. Over the course of several months, 24 fissures opened in the Lower East Rift Zone, with lava flows covering approximately 35.5 square kilometers of land. The Halema'uma'u crater at Kilauea's summit collapsed dramatically, deepening the crater by over 450 meters.",
        "impacts": "700 homes were destroyed and over 2,000 people were evacuated. Major highways were covered by lava, isolating communities. Lava entering the ocean created toxic gas plumes. Tourism, a major economic driver in Hawaii, was significantly affected."
    },
    {
        "title": "Laki Fissure Eruption",
        "date": "June 8, 1783",
        "location": "Laki, Eastern Volcanic Zone",
        "country": "Iceland",
        "event_type": "Volcanic Eruption",
        "vei": 4,
        "casualties": "9,350 in Iceland (20% of population), tens of thousands in Europe",
        "text": "The Laki eruption was not a single event but a series of eruptions lasting 8 months, producing one of the largest lava flows in recorded history. The eruption ejected an estimated 14 cubic kilometers of basalt lava and massive amounts of volcanic gases. These gases created a persistent haze across the Northern Hemisphere known as the 'Laki haze', causing a drop in global temperatures.",
        "impacts": "In Iceland, the eruption led to the death of 50% of livestock and subsequent famine. The sulfuric aerosol cloud spread across Europe, causing crop failures and thousands of deaths. Some historians link the resulting food shortages to the French Revolution in 1789."
    },
    {
        "title": "Mount Pelée Eruption",
        "date": "May 8, 1902",
        "location": "Mount Pelée, Martinique",
        "country": "France (Martinique)",
        "event_type": "Volcanic Eruption",
        "vei": 4,
        "casualties": "28,000-40,000 people",
        "text": "The eruption of Mount Pelée completely destroyed the city of Saint-Pierre, the 'Paris of the Caribbean,' in a matter of minutes. A nuée ardente (pyroclastic flow) rushed down the mountain at over 100 mph, with temperatures exceeding 1,000°C. Out of a population of 28,000, there were only two survivors. The disaster changed our understanding of volcanic hazards and introduced the concept of nuée ardente into volcanology.",
        "impacts": "The city of Saint-Pierre was never fully rebuilt to its former glory. The eruption demonstrated the extreme danger of pyroclastic flows and led to the development of modern volcanology."
    },
    {
        "title": "Soufrière Hills Volcano Eruption",
        "date": "July 18, 1995",
        "location": "Soufrière Hills, Montserrat",
        "country": "United Kingdom (Montserrat)",
        "event_type": "Volcanic Eruption",
        "vei": 3,
        "casualties": "19 people",
        "text": "After being dormant for centuries, the Soufrière Hills volcano began erupting in July 1995 and remained active for over 15 years. The eruption forced the evacuation of Plymouth, the capital city, which was later buried under 12 meters of mud and debris. The eruption led to a mass exodus from the island, with two-thirds of the population leaving Montserrat permanently.",
        "impacts": "The southern two-thirds of the island became uninhabitable. Plymouth became a modern-day Pompeii. The island's economy and infrastructure were devastated, requiring significant aid from the UK. The long-duration eruption provided valuable data for volcanologists."
    },
    {
        "title": "Paricutín Eruption",
        "date": "February 20, 1943",
        "location": "Paricutín, Michoacán",
        "country": "Mexico",
        "event_type": "Volcanic Eruption",
        "vei": 4,
        "casualties": "3-5 people (indirect)",
        "text": "Paricutín is famous for being the only volcano whose birth was witnessed from beginning to end. The volcano began as a fissure in a cornfield owned by Dionisio Pulido, who observed the initial eruption. Over the next 9 years, the volcano grew to a height of 424 meters, burying the villages of Paricutín and San Juan Parangaricutiro. The eruption allowed scientists to study the complete life cycle of a volcano.",
        "impacts": "Two villages were completely buried, though most inhabitants were evacuated in time. Agricultural land was destroyed by ash fall and lava flows. The area later became a tourist attraction, with the spire of San Juan Parangaricutiro's church still visible above the lava field."
    },
    {
        "title": "Novarupta Eruption",
        "date": "June 6, 1912",
        "location": "Novarupta, Katmai National Park, Alaska",
        "country": "United States",
        "event_type": "Volcanic Eruption",
        "vei": 6,
        "casualties": "0 direct deaths",
        "text": "The Novarupta eruption was the largest volcanic eruption of the 20th century. It ejected approximately 30 cubic kilometers of material in 60 hours, creating the Valley of Ten Thousand Smokes. Despite its size, the eruption occurred in a remote area, resulting in no direct casualties. The eruption was mistakenly attributed to nearby Mount Katmai for many years until research in the 1950s identified Novarupta as the source.",
        "impacts": "Ash fell over an area of 30,000 square kilometers. Several villages were abandoned due to ash damage. Global temperatures decreased by approximately 1.0°C for several years after the eruption."
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
        {"name": "Erta Ale", "location": "Afar Region", "country": "Ethiopia"},
        {"name": "Pacaya", "location": "Guatemala City (near)", "country": "Guatemala"},
        {"name": "Arenal", "location": "Alajuela Province", "country": "Costa Rica"},
        {"name": "Villarrica", "location": "Araucanía Region", "country": "Chile"},
        {"name": "Cotopaxi", "location": "Andes", "country": "Ecuador"}
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

def process_and_load_volcanic_data(data: List[Dict[str, Any]], batch_size: int = 50) -> None:
    """Process and load volcanic eruption data into MongoDB."""
    try:
        # Connect to MongoDB
        db_conn = get_db_connection()
        db_conn.connect()
        
        # Get crisis event operations
        crisis_ops = get_crisis_event_ops()
        
        # Process the data (clean and generate embeddings)
        processed_data = process_crisis_events(data)
        
        # Load data in batches
        total_batches = (len(processed_data) + batch_size - 1) // batch_size
        
        for i in range(0, len(processed_data), batch_size):
            batch = processed_data[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} records)")
            
            # Upload batch to MongoDB
            result = crisis_ops.insert_crisis_events(batch)
            
            logger.info(f"Uploaded {result} documents successfully")
            
        logger.info(f"Successfully uploaded {len(processed_data)} volcanic eruption records to MongoDB")
        
    except Exception as e:
        logger.error(f"Error processing and loading volcanic data: {e}")
        raise
    finally:
        # Close database connection
        if db_conn:
            db_conn.close()

def main(additional_count: int = 30):
    """Generate and load volcanic eruption data."""
    try:
        logger.info("Generating volcanic eruption dataset...")
        
        # Combine major historical eruptions with synthetic data
        all_volcanic_data = MAJOR_VOLCANIC_ERUPTIONS.copy()
        
        if additional_count > 0:
            logger.info(f"Generating {additional_count} additional synthetic volcanic events...")
            synthetic_data = generate_additional_volcanic_events(additional_count)
            all_volcanic_data.extend(synthetic_data)
        
        logger.info(f"Total volcanic eruption records: {len(all_volcanic_data)}")
        
        # Process and load data
        logger.info("Processing and loading data into MongoDB...")
        process_and_load_volcanic_data(all_volcanic_data)
        
        logger.info("Volcanic eruption data generation and loading complete!")
        
    except Exception as e:
        logger.error(f"Error in volcanic data generation: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate and load volcanic eruption data for CrisisMap AI")
    parser.add_argument("--count", type=int, default=30, help="Number of additional synthetic volcanic events to generate")
    
    args = parser.parse_args()
    
    main(args.count)