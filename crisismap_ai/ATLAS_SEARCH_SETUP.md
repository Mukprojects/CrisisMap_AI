# Setting Up MongoDB Atlas Search for CrisisMap AI

This guide will help you enable Atlas Search and create the vector index required for CrisisMap AI to work properly.

## Step 1: Log in to MongoDB Atlas

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Sign in with your credentials

## Step 2: Enable Atlas Search

1. In your Atlas dashboard, select your project
2. Click on your cluster (Cluster0)
3. Go to the "Search" tab
4. Click "Enable Search" if it's not already enabled

## Step 3: Create the Vector Search Index

1. In the Search tab, click "Create Search Index"
2. Choose "JSON Editor" from the creation method options
3. Enter the following JSON configuration:

```json
{
  "mappings": {
    "dynamic": true,
    "fields": {
      "embedding": {
        "dimensions": 384,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```

4. Name your index `vector_index` (must match exactly what's in the code)
5. Set the Database to `crisismap` and Collection to `crisis_events`
6. Click "Create Search Index"
7. Wait for the index to be built (this may take a few minutes)

## Step 4: Verify the Index

1. In the Search tab, you should see your `vector_index` listed
2. The status should eventually change to "Active"

## Step 5: Run the CrisisMap AI Application

Once the index is created and active, you can run:

1. Load data: `python run.py load`
2. Start the server: `python run.py server`

## Troubleshooting

If you encounter issues:

1. Make sure your MongoDB Atlas cluster is M0 (free) or higher
2. Verify that Atlas Search is enabled for your cluster
3. Check that the index name matches exactly (`vector_index`)
4. Ensure your database is named `crisismap` and collection is `crisis_events`
5. Make sure your IP address is whitelisted in MongoDB Atlas
6. Try running `python create_vector_index.py` to create the index programmatically

For more information, see:
[MongoDB Atlas Search Documentation](https://www.mongodb.com/docs/atlas/atlas-search/) 