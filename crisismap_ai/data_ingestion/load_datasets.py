"""
Module for loading datasets for CrisisMap AI.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import csv
import json
import logging
import os

# Add parent directory to system path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    WHO_DATASET, EMDAT_DATASET, DISASTER_TWEETS,
    EARTHQUAKE_DATASET, EARTHQUAKE_DATA, 
    VOLCANO_DATASET, FLOODS_DATASET, TSUNAMI_DATASET, 
    FIRE_DATASET
)

# Debug print statements
print("Current working directory:", os.getcwd())
print("Dataset paths:")
print(f"WHO_DATASET: {WHO_DATASET}, exists: {WHO_DATASET.exists() if isinstance(WHO_DATASET, Path) else 'N/A'}")
print(f"EMDAT_DATASET: {EMDAT_DATASET}, exists: {EMDAT_DATASET.exists() if isinstance(EMDAT_DATASET, Path) else 'N/A'}")
print(f"DISASTER_TWEETS: {DISASTER_TWEETS}, exists: {DISASTER_TWEETS.exists() if isinstance(DISASTER_TWEETS, Path) else 'N/A'}")
print(f"EARTHQUAKE_DATASET: {EARTHQUAKE_DATASET}, exists: {EARTHQUAKE_DATASET.exists() if isinstance(EARTHQUAKE_DATASET, Path) else 'N/A'}")
print(f"VOLCANO_DATASET: {VOLCANO_DATASET}, exists: {VOLCANO_DATASET.exists() if isinstance(VOLCANO_DATASET, Path) else 'N/A'}")
print(f"FLOODS_DATASET: {FLOODS_DATASET}, exists: {FLOODS_DATASET.exists() if isinstance(FLOODS_DATASET, Path) else 'N/A'}")
print(f"TSUNAMI_DATASET: {TSUNAMI_DATASET}, exists: {TSUNAMI_DATASET.exists() if isinstance(TSUNAMI_DATASET, Path) else 'N/A'}")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_who_dataset(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load and parse WHO dataset.
    
    Args:
        filepath: Path to WHO dataset CSV file
        
    Returns:
        List of parsed WHO data entries
    """
    if filepath is None:
        filepath = WHO_DATASET
        
    logger.info(f"Loading WHO dataset from {filepath}")
    print(f"Attempting to load WHO dataset from: {filepath}")
    
    try:
        # Read CSV file
        df = pd.read_csv(filepath)
        
        # Convert to list of dictionaries
        who_data = []
        
        for _, row in df.iterrows():
            # Create a crisis event entry
            event = {
                'title': f"Health statistics for {row['Country']}",
                'summary': (
                    f"Country: {row['Country']}, Region: {row['Region']}, "
                    f"Population: {row['Population']}, "
                    f"Under 15: {row['Under15']}%, Over 60: {row['Over60']}%, "
                    f"Fertility Rate: {row['FertilityRate']}, "
                    f"Life Expectancy: {row['LifeExpectancy']} years, "
                    f"Child Mortality: {row['ChildMortality']} per 1000"
                ),
                'location': row['Country'],
                'region': row['Region'],
                'category': 'Health Statistics',
                'source': 'World Health Organization',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'data': {
                    'population': row['Population'],
                    'under15_percent': row['Under15'],
                    'over60_percent': row['Over60'],
                    'fertility_rate': row['FertilityRate'],
                    'life_expectancy': row['LifeExpectancy'],
                    'child_mortality': row['ChildMortality'],
                    'cellular_subscribers': row['CellularSubscribers'],
                    'literacy_rate': row['LiteracyRate'],
                    'gni': row['GNI'],
                    'primary_school_enrollment_male': row['PrimarySchoolEnrollmentMale'],
                    'primary_school_enrollment_female': row['PrimarySchoolEnrollmentFemale']
                }
            }
            
            who_data.append(event)
            
        logger.info(f"Loaded {len(who_data)} WHO dataset entries")
        return who_data
        
    except Exception as e:
        logger.error(f"Error loading WHO dataset: {e}")
        print(f"Exception loading WHO dataset: {e}")
        return []

def load_emdat_dataset(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load and parse EM-DAT dataset.
    
    Args:
        filepath: Path to EM-DAT dataset CSV file
        
    Returns:
        List of parsed EM-DAT data entries
    """
    if filepath is None:
        filepath = EMDAT_DATASET
        
    logger.info(f"Loading EM-DAT dataset from {filepath}")
    print(f"Attempting to load EM-DAT dataset from: {filepath}")
    
    try:
        # Read CSV file
        df = pd.read_csv(filepath)
        
        # Convert to list of dictionaries
        emdat_data = []
        
        for _, row in df.iterrows():
            # Parse date
            try:
                start_date = datetime.strptime(str(row['Begin Date']), '%Y%m%d').strftime('%Y-%m-%d')
            except:
                start_date = None
                
            try:
                end_date = datetime.strptime(str(row['End Date']), '%Y%m%d').strftime('%Y-%m-%d')
            except:
                end_date = None
                
            # Create a crisis event entry
            event = {
                'title': row['Name'],
                'summary': f"{row['Disaster']} event: {row['Name']}. Cost: ${row['CPI-Adjusted Cost']} million. Deaths: {row['Deaths']}.",
                'text': f"{row['Name']} was a {row['Disaster']} event that occurred from {start_date} to {end_date}. The estimated cost was ${row['CPI-Adjusted Cost']} million (CPI-adjusted), with {row['Deaths']} deaths reported.",
                'location': 'United States',
                'category': row['Disaster'],
                'source': 'EM-DAT Database',
                'date': start_date,
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'cost_adjusted': row['CPI-Adjusted Cost'],
                    'cost_unadjusted': row['Unadjusted Cost'],
                    'deaths': row['Deaths']
                }
            }
            
            emdat_data.append(event)
            
        logger.info(f"Loaded {len(emdat_data)} EM-DAT dataset entries")
        return emdat_data
        
    except Exception as e:
        logger.error(f"Error loading EM-DAT dataset: {e}")
        print(f"Exception loading EM-DAT dataset: {e}")
        return []

def load_disaster_tweets_dataset(filepath: Optional[Path] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Load and parse disaster tweets dataset.
    
    Args:
        filepath: Path to disaster tweets dataset CSV file
        limit: Maximum number of tweets to load
        
    Returns:
        List of parsed disaster tweets
    """
    if filepath is None:
        filepath = DISASTER_TWEETS
        
    logger.info(f"Loading disaster tweets dataset from {filepath}")
    print(f"Attempting to load disaster tweets dataset from: {filepath}")
    
    try:
        # Read CSV file
        df = pd.read_csv(filepath, nrows=limit)
        
        # Filter only real disaster tweets (target=1)
        df = df[df['target'] == 1]
        
        # Convert to list of dictionaries
        tweets_data = []
        
        for _, row in df.iterrows():
            # Create a crisis event entry
            event = {
                'title': f"Disaster Tweet: {row['keyword']}",
                'summary': row['text'],
                'text': row['text'],
                'location': row['location'] if pd.notna(row['location']) else None,
                'category': 'Social Media Alert',
                'source': 'Twitter',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'data': {
                    'keyword': row['keyword'],
                    'tweet_id': row['id']
                }
            }
            
            tweets_data.append(event)
            
        logger.info(f"Loaded {len(tweets_data)} disaster tweets")
        print(f"Successfully loaded {len(tweets_data)} disaster tweets")
        return tweets_data
        
    except Exception as e:
        logger.error(f"Error loading disaster tweets dataset: {e}")
        print(f"Exception loading disaster tweets dataset: {e}")
        return []

def load_earthquake_dataset(filepath: Optional[Path] = None, limit: int = None) -> List[Dict[str, Any]]:
    """
    Load and parse earthquake dataset.
    
    Args:
        filepath: Path to earthquake dataset CSV file
        limit: Maximum number of records to load
        
    Returns:
        List of parsed earthquake data entries
    """
    if filepath is None:
        filepath = EARTHQUAKE_DATASET
        
    logger.info(f"Loading earthquake dataset from {filepath}")
    print(f"Attempting to load earthquake dataset from: {filepath}")
    
    try:
        # Read CSV file
        df = pd.read_csv(filepath, nrows=limit)
        
        # Convert to list of dictionaries
        earthquake_data = []
        
        for _, row in df.iterrows():
            # Extract date and location information
            title = str(row['title']).replace('"', '')
            date_str = row['date_time'] if pd.notna(row['date_time']) else None
            location = row['location'] if pd.notna(row['location']) else "Unknown location"
            country = row['country'] if pd.notna(row['country']) else None
            continent = row['continent'] if pd.notna(row['continent']) else None
            
            # Create a crisis event entry
            event = {
                'title': title,
                'summary': f"Magnitude {row['magnitude']} earthquake near {location}.",
                'text': f"A magnitude {row['magnitude']} earthquake occurred near {location} on {date_str}. " +
                        f"Depth: {row['depth']} km. Coordinates: {row['latitude']}, {row['longitude']}.",
                'location': location,
                'category': 'Earthquake',
                'source': 'Earthquake Database',
                'date': date_str,
                'data': {
                    'magnitude': row['magnitude'],
                    'depth': row['depth'],
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'country': country,
                    'continent': continent,
                    'tsunami': row['tsunami'] if pd.notna(row['tsunami']) else 0,
                    'alert_level': row['alert'] if pd.notna(row['alert']) else 'none'
                }
            }
            
            earthquake_data.append(event)
            
        logger.info(f"Loaded {len(earthquake_data)} earthquake dataset entries")
        print(f"Successfully loaded {len(earthquake_data)} earthquake entries")
        return earthquake_data
        
    except Exception as e:
        logger.error(f"Error loading earthquake dataset: {e}")
        print(f"Exception loading earthquake dataset: {e}")
        return []

def load_volcano_dataset(filepath: Optional[Path] = None, limit: int = None) -> List[Dict[str, Any]]:
    """
    Load and parse volcano events dataset.
    
    Args:
        filepath: Path to volcano events dataset CSV file
        limit: Maximum number of records to load
        
    Returns:
        List of parsed volcano event entries
    """
    if filepath is None:
        filepath = VOLCANO_DATASET
        
    logger.info(f"Loading volcano dataset from {filepath}")
    print(f"Attempting to load volcano dataset from: {filepath}")
    
    try:
        # Read CSV file
        df = pd.read_csv(filepath, nrows=limit)
        
        # Skip empty rows
        df = df.dropna(how='all')
        
        # Convert to list of dictionaries
        volcano_data = []
        
        for _, row in df.iterrows():
            # Parse date
            year = int(row['Year']) if pd.notna(row['Year']) else None
            month = row['Month'] if pd.notna(row['Month']) else None
            day = row['Day'] if pd.notna(row['Day']) else None
            
            # Create date string
            date_str = None
            if year and year > 0:
                date_parts = []
                if day: date_parts.append(f"{int(day):02d}")
                if month: date_parts.append(f"{month}")
                if year: date_parts.append(f"{int(year)}")
                date_str = "-".join(date_parts) if date_parts else None
            
            # Get location and name
            volcano_name = row['Name'] if pd.notna(row['Name']) else "Unknown volcano"
            location = row['Location'] if pd.notna(row['Location']) else None
            country = row['Country'] if pd.notna(row['Country']) else None
            
            # Get deaths and damages
            deaths = row['Total Deaths'] if pd.notna(row['Total Deaths']) else 0
            
            # Create a crisis event entry
            event = {
                'title': f"Volcanic eruption: {volcano_name}",
                'summary': f"Volcanic eruption at {volcano_name}, {location}, {country}. VEI: {row['VEI'] if pd.notna(row['VEI']) else 'Unknown'}. Deaths: {deaths}",
                'text': f"A volcanic eruption occurred at {volcano_name} in {location}, {country}. " +
                        f"Volcano elevation: {row['Elevation (m)']} meters. VEI (Volcanic Explosivity Index): {row['VEI'] if pd.notna(row['VEI']) else 'Unknown'}. " +
                        f"Total deaths: {deaths}.",
                'location': f"{location}, {country}" if location and country else (location or country or "Unknown location"),
                'category': 'Volcanic Eruption',
                'source': 'Volcano Events Database',
                'date': date_str,
                'data': {
                    'volcano_name': volcano_name,
                    'location': location,
                    'country': country,
                    'latitude': row['Latitude'] if pd.notna(row['Latitude']) else None,
                    'longitude': row['Longitude'] if pd.notna(row['Longitude']) else None,
                    'elevation': row['Elevation (m)'] if pd.notna(row['Elevation (m)']) else None,
                    'vei': row['VEI'] if pd.notna(row['VEI']) else None,
                    'deaths': deaths,
                    'damage_millions': row['Total Damage ($Mil)'] if pd.notna(row['Total Damage ($Mil)']) else None,
                    'houses_destroyed': row['Total Houses Destroyed'] if pd.notna(row['Total Houses Destroyed']) else None
                }
            }
            
            volcano_data.append(event)
            
        logger.info(f"Loaded {len(volcano_data)} volcano dataset entries")
        print(f"Successfully loaded {len(volcano_data)} volcano entries")
        return volcano_data
        
    except Exception as e:
        logger.error(f"Error loading volcano dataset: {e}")
        print(f"Exception loading volcano dataset: {e}")
        return []

def load_floods_dataset(filepath: Optional[Path] = None, limit: int = None) -> List[Dict[str, Any]]:
    """
    Load and parse floods dataset.
    
    Args:
        filepath: Path to floods dataset CSV file
        limit: Maximum number of records to load
        
    Returns:
        List of parsed flood event entries
    """
    if filepath is None:
        filepath = FLOODS_DATASET
        
    logger.info(f"Loading floods dataset from {filepath}")
    print(f"Attempting to load floods dataset from: {filepath}")
    
    try:
        # Read CSV file
        df = pd.read_csv(filepath, nrows=limit)
        
        # Convert to list of dictionaries
        floods_data = []
        
        for _, row in df.iterrows():
            # Parse date
            year = row['year'] if pd.notna(row['year']) else None
            month = row['month'] if pd.notna(row['month']) else None
            day = row['date'] if pd.notna(row['date']) else None
            
            # Create date string
            date_str = None
            if year:
                date_parts = []
                if day: date_parts.append(f"{day}")
                if month: date_parts.append(f"{month}")
                if year: date_parts.append(f"{year}")
                date_str = "-".join(date_parts) if date_parts else None
            
            # Get location and causes
            location = row['location'] if pd.notna(row['location']) else "Unknown location"
            causes = row['cause'] if pd.notna(row['cause']) else "Unknown causes"
            deaths = row['deaths'] if pd.notna(row['deaths']) else "Unknown"
            damages = row['property damages'] if pd.notna(row['property damages']) else "Unknown"
            
            # Create a crisis event entry
            event = {
                'title': f"Flood: {location} ({year})",
                'summary': f"Flooding in {location} caused by {causes}. Deaths: {deaths}",
                'text': f"A flood occurred in {location} in {month} {year} caused by {causes}. " +
                        f"Deaths reported: {deaths}. Property damage: {damages}.",
                'location': location,
                'category': 'Flood',
                'source': 'Floods Database',
                'date': date_str,
                'data': {
                    'year': year,
                    'month': month,
                    'day': day,
                    'location': location,
                    'causes': causes,
                    'deaths': deaths,
                    'property_damages': damages
                }
            }
            
            floods_data.append(event)
            
        logger.info(f"Loaded {len(floods_data)} floods dataset entries")
        print(f"Successfully loaded {len(floods_data)} flood entries")
        return floods_data
        
    except Exception as e:
        logger.error(f"Error loading floods dataset: {e}")
        print(f"Exception loading floods dataset: {e}")
        return []

def load_tsunami_dataset(filepath: Optional[Path] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Load and parse tsunami dataset.
    
    Args:
        filepath: Path to tsunami dataset CSV file
        limit: Maximum number of records to load
        
    Returns:
        List of parsed tsunami event entries
    """
    if filepath is None:
        filepath = TSUNAMI_DATASET
        
    logger.info(f"Loading tsunami dataset from {filepath}")
    print(f"Attempting to load tsunami dataset from: {filepath}")
    
    try:
        # Read CSV file (limiting to prevent memory issues with large files)
        df = pd.read_csv(filepath, nrows=limit)
        
        # Convert to list of dictionaries
        tsunami_data = []
        
        # Sample a few columns to check structure
        sample_columns = list(df.columns[:10])
        print(f"Tsunami dataset columns (sample): {sample_columns}")
        
        # Process based on available columns
        for _, row in df.iterrows():
            # Try to extract basic information based on common column patterns
            # This is a generic approach since we don't know the exact column structure
            
            # Look for date/time columns
            date_str = None
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower() or 'year' in col.lower():
                    if pd.notna(row[col]):
                        date_str = str(row[col])
                        break
            
            # Look for location columns
            location = "Unknown location"
            for col in df.columns:
                if 'location' in col.lower() or 'country' in col.lower() or 'place' in col.lower():
                    if pd.notna(row[col]):
                        location = str(row[col])
                        break
            
            # Look for magnitude columns
            magnitude = None
            for col in df.columns:
                if 'magnitude' in col.lower() or 'height' in col.lower() or 'intensity' in col.lower():
                    if pd.notna(row[col]):
                        magnitude = row[col]
                        break
            
            # Look for casualties columns
            casualties = None
            for col in df.columns:
                if 'death' in col.lower() or 'casualt' in col.lower() or 'fatal' in col.lower():
                    if pd.notna(row[col]):
                        casualties = row[col]
                        break
            
            # Create a dictionary of all available data
            data_dict = {}
            for col in df.columns:
                if pd.notna(row[col]):
                    data_dict[col] = row[col]
            
            # Create a crisis event entry
            event = {
                'title': f"Tsunami event in {location}",
                'summary': f"Tsunami in {location}" + (f" with magnitude {magnitude}" if magnitude else ""),
                'text': f"A tsunami occurred in {location}" + (f" on {date_str}" if date_str else "") + 
                        (f". Magnitude/height: {magnitude}" if magnitude else "") +
                        (f". Casualties: {casualties}" if casualties else ""),
                'location': location,
                'category': 'Tsunami',
                'source': 'Tsunami Database',
                'date': date_str,
                'data': data_dict
            }
            
            tsunami_data.append(event)
            
        logger.info(f"Loaded {len(tsunami_data)} tsunami dataset entries")
        print(f"Successfully loaded {len(tsunami_data)} tsunami entries")
        return tsunami_data
        
    except Exception as e:
        logger.error(f"Error loading tsunami dataset: {e}")
        print(f"Exception loading tsunami dataset: {e}")
        return []

def load_all_datasets() -> List[Dict[str, Any]]:
    """
    Load all available datasets.
    
    Returns:
        Combined list of all dataset entries
    """
    logger.info("Loading all datasets...")
    
    # Load individual datasets
    who_data = load_who_dataset()
    emdat_data = load_emdat_dataset()
    tweets_data = load_disaster_tweets_dataset()
    earthquake_data = load_earthquake_dataset()
    volcano_data = load_volcano_dataset()
    floods_data = load_floods_dataset()
    tsunami_data = load_tsunami_dataset(limit=500)  # Limit tsunami data to avoid memory issues
    
    # Combine datasets
    all_data = who_data + emdat_data + tweets_data + earthquake_data + volcano_data + floods_data + tsunami_data
    
    logger.info(f"Loaded {len(all_data)} total dataset entries")
    return all_data 