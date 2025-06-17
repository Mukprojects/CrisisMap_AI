# Volcanic Eruption Data for CrisisMap AI

This guide explains how to load comprehensive volcanic eruption data into your CrisisMap AI database.

## Available Volcanic Data

The volcanic eruption dataset includes:

1. **Major Historical Eruptions**: Detailed information about significant volcanic events throughout history, including:
   - Mount Vesuvius (79 CE)
   - Tambora (1815)
   - Krakatoa (1883)
   - Mount St. Helens (1980)
   - Mount Pinatubo (1991)
   - And more

2. **Synthetic Volcanic Events**: Generated data for various active volcanoes worldwide, with realistic:
   - Eruption types (Strombolian, pyroclastic flows, lava domes, etc.)
   - Volcanic Explosivity Index (VEI) ratings
   - Casualty estimates
   - Impact descriptions
   - Dates spanning the last 50 years

## How to Load Volcanic Data

### Method 1: Using the Standalone Script

The simplest way to load volcanic data is to use the standalone script `volcano_data_loader.py` located in the project root directory:

```bash
# From the project root directory
python volcano_data_loader.py --count 15
```

Parameters:
- `--count`: Number of additional synthetic volcanic events to generate (default: 15)

This script will:
1. Load predefined major historical eruptions
2. Generate the specified number of synthetic volcanic events
3. Process all data and create embeddings
4. Upload everything to MongoDB

### Method 2: From Within the Application

You can also load volcanic data from within the application by using the API server's built-in data loading functionality:

```bash
# From the crisismap_ai directory
python run.py load --dataset volcano
```

## Querying Volcanic Data

Once loaded, you can query volcanic eruption data through the API:

1. **Web Interface**: Visit http://localhost:8000/ and enter queries like:
   - "Tell me about volcanic eruptions"
   - "What was the Krakatoa eruption?"
   - "What are the dangers of pyroclastic flows?"

2. **API Endpoint**: Make POST requests to the LLM response endpoint:
   ```
   POST http://localhost:8000/api/llm-response
   Content-Type: application/json
   
   {
     "query": "Tell me about volcanic eruptions"
   }
   ```

## Example Response

The system will provide concise, well-summarized information about volcanic eruptions, drawing from both the historical and synthetic data in the database:

```
Volcanic eruptions occur when magma from the Earth's interior rises to the surface. These natural events range from gentle lava flows to catastrophic explosions that can transform landscapes and affect global climate. Major eruptions like Tambora (1815) and Krakatoa (1883) had worldwide impacts, causing temperature drops and spectacular sunsets for years. The immediate dangers include lava flows, pyroclastic flows (fast-moving currents of hot gas and volcanic matter), ashfall, and toxic gases. Secondary hazards often include mudflows, landslides, and tsunamis for coastal volcanoes.

Notable Volcanic Events in Our Database:
1. Mount Vesuvius Eruption (79 CE) in Pompeii and Herculaneum - One of the most catastrophic volcanic eruptions in European history. The eruption buried the Roman cities of Pompeii and Herculaneum under meters of ash and pumice, preserving them in remarkable detail. Casualties: Approximately 16,000 people.

2. Tambora Eruption (April 10, 1815) in Mount Tambora, Sumbawa Island - The 1815 eruption of Mount Tambora was the most powerful volcanic eruption in recorded human history. The explosion was heard 2,000 km away and ash fell at least 1,300 km away. Casualties: Over 100,000 people.

3. Krakatoa Eruption (August 27, 1883) in Krakatoa (Krakatau), Sunda Strait - The 1883 eruption of Krakatoa began on August 26 and peaked the following day with four massive explosions. The final explosion was heard nearly 3,000 miles away in Perth, Australia. Casualties: Over 36,000 people.

Volcanic eruptions have shaped Earth's history and continue to remind us of our planet's dynamic nature. While they pose significant threats to nearby populations, they also create new land, provide fertile soil, and offer insights into Earth's geological processes.
```

## Troubleshooting

If you encounter any issues loading the volcanic data:

1. Check your MongoDB connection in the `config.py` file
2. Ensure you have the required dependencies installed (sentence-transformers, pymongo)
3. Try loading fewer records if you hit MongoDB storage limits
4. Check the MongoDB Atlas dashboard to ensure your database is properly configured