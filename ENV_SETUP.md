# Environment Variables Setup Guide

## Introduction

This project uses environment variables to manage sensitive configuration data like MongoDB connection strings. This approach protects your credentials when sharing code or pushing to public repositories.

## Setting Up Environment Variables

1. Create a file named `.env` in the `crisismap_ai` directory
2. Add the following variables to your `.env` file:

```
# MongoDB Configuration
MONGODB_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=crisismap
CRISIS_COLLECTION=crisis_events
VECTOR_INDEX_NAME=vector_index

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Hugging Face Model Settings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
SUMMARIZATION_MODEL=google-t5/t5-small
RESPONSE_MODEL=microsoft/Phi-3-mini-4k-instruct
```

3. Replace `your_username`, `your_password`, and `your_cluster.mongodb.net` with your actual MongoDB Atlas credentials.

## Security Notes

- **DO NOT** commit the `.env` file to version control. It's already added to `.gitignore`.
- The default values in the code are placeholders and will not work in production.
- If collaborating with others, share the env variable structure but not the actual values.
- For deployment, set these environment variables in your hosting platform's configuration.

## Verifying Setup

To verify your environment setup is working:

```bash
python crisismap_ai/test_mongo.py
```

This will test the MongoDB connection using your environment variables.

## Troubleshooting

If you encounter connection issues:

1. Ensure your MongoDB URI is correctly formatted
2. Check that your Atlas IP whitelist includes your current IP address
3. Verify that your username and password are correct
4. If using special characters in your password, ensure they are properly URL-encoded
   - `@` should be encoded as `%40`
   - Other special characters may need encoding as well 