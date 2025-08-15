"""
Advanced RAG (Retrieval-Augmented Generation) Enhancement System.

This module implements state-of-the-art RAG techniques with vector search optimization,
response accuracy improvements, and intelligent knowledge retrieval.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS, Chroma
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.schema import Document
import openai
import anthropic
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
import re
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """Different retrieval strategies."""
    DENSE_ONLY = "dense_only"
    SPARSE_ONLY = "sparse_only"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"
    MULTI_STAGE = "multi_stage"


class RetrievalMode(Enum):
    """Retrieval modes for different use cases."""
    FAST = "fast"           # Speed optimized
    ACCURATE = "accurate"   # Accuracy optimized
    BALANCED = "balanced"   # Speed/accuracy balanced
    COMPREHENSIVE = "comprehensive"  # Maximum recall


@dataclass
class RAGConfig:
    """Configuration for RAG system."""
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 20
    top_k_rerank: int = 5
    similarity_threshold: float = 0.7
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    retrieval_mode: RetrievalMode = RetrievalMode.ACCURATE
    enable_reranking: bool = True
    enable_query_expansion: bool = True
    enable_context_compression: bool = True
    max_context_length: int = 4000
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-12-v2"


@dataclass
class RetrievalResult:
    """Result from knowledge retrieval."""
    documents: List[Document]
    scores: List[float]
    retrieval_time: float
    total_documents: int
    strategy_used: str
    confidence_score: float
    sources: List[str]
    metadata: Dict[str, Any]


@dataclass
class RAGResponse:
    """Enhanced response with RAG information."""
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]
    retrieval_info: RetrievalResult
    processing_time: float
    model_used: str
    context_length: int
    accuracy_indicators: Dict[str, float]


class AdvancedVectorStore:
    """Advanced vector store with multiple backends and optimizations."""
    
    def __init__(self, config: RAGConfig):
        """Initialize advanced vector store."""
        self.config = config
        self.embedding_model = SentenceTransformer(config.embedding_model)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize multiple vector stores
        self.faiss_index = None
        self.chroma_client = None
        self.documents = []
        self.document_embeddings = []
        self.metadata_store = {}
        
        # Initialize stores
        self._initialize_stores()
        
        logger.info(f"🧠 Advanced Vector Store initialized with {config.embedding_model}")
    
    def _initialize_stores(self):
        """Initialize vector storage backends."""
        try:
            # FAISS for high-performance similarity search
            self.faiss_index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            
            # Create HNSW index for better performance
            self.faiss_hnsw = faiss.IndexHNSWFlat(self.dimension, 32)
            self.faiss_hnsw.hnsw.efConstruction = 200
            self.faiss_hnsw.hnsw.efSearch = 50
            
            logger.info("✅ FAISS vector store initialized")
        except Exception as e:
            logger.warning(f"FAISS initialization failed: {e}")
        
        try:
            # ChromaDB for persistent storage and metadata
            self.chroma_client = chromadb.Client()
            self.chroma_collection = self.chroma_client.create_collection(
                name="crisis_knowledge",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("✅ ChromaDB vector store initialized")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}")
    
    async def add_documents(self, documents: List[Document]):
        """Add documents to vector store with advanced processing."""
        logger.info(f"📚 Adding {len(documents)} documents to vector store")
        
        # Generate embeddings in batches for efficiency
        batch_size = 32
        embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_texts = [doc.page_content for doc in batch_docs]
            
            # Generate embeddings
            batch_embeddings = self.embedding_model.encode(
                batch_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            embeddings.extend(batch_embeddings)
        
        embeddings = np.array(embeddings).astype('float32')
        
        # Store in FAISS
        if self.faiss_index is not None:
            self.faiss_index.add(embeddings)
            self.faiss_hnsw.add(embeddings)
        
        # Store in ChromaDB
        if self.chroma_client is not None:
            self.chroma_collection.add(
                embeddings=embeddings.tolist(),
                documents=[doc.page_content for doc in documents],
                metadatas=[doc.metadata for doc in documents],
                ids=[f"doc_{i}" for i in range(len(self.documents), len(self.documents) + len(documents))]
            )
        
        # Store documents and metadata
        self.documents.extend(documents)
        self.document_embeddings.extend(embeddings)
        
        for i, doc in enumerate(documents):
            doc_id = len(self.metadata_store) + i
            self.metadata_store[doc_id] = {
                'content': doc.page_content,
                'metadata': doc.metadata,
                'embedding_id': len(self.document_embeddings) - len(documents) + i
            }
        
        logger.info(f"✅ Added {len(documents)} documents. Total: {len(self.documents)}")
    
    async def similarity_search(
        self,
        query: str,
        k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[Document, float]]:
        """Perform similarity search with multiple strategies."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        query_embedding = query_embedding.astype('float32')
        
        results = []
        
        # FAISS search (fastest)
        if self.faiss_hnsw is not None and len(self.documents) > 0:
            scores, indices = self.faiss_hnsw.search(query_embedding, k)
            
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and score >= threshold:
                    doc = self.documents[idx]
                    results.append((doc, float(score)))
        
        # ChromaDB search (with metadata filtering)
        elif self.chroma_client is not None:
            chroma_results = self.chroma_collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=k
            )
            
            for i, (doc_text, score) in enumerate(zip(
                chroma_results['documents'][0],
                chroma_results['distances'][0]
            )):
                if score >= threshold:
                    doc = Document(
                        page_content=doc_text,
                        metadata=chroma_results['metadatas'][0][i]
                    )
                    results.append((doc, 1.0 - score))  # Convert distance to similarity
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]


class HybridRetriever:
    """Advanced hybrid retriever combining dense and sparse methods."""
    
    def __init__(self, config: RAGConfig, vector_store: AdvancedVectorStore):
        """Initialize hybrid retriever."""
        self.config = config
        self.vector_store = vector_store
        self.bm25_retriever = None
        self.tfidf_vectorizer = None
        self.reranker = None
        
        # Initialize components
        self._initialize_sparse_retrieval()
        self._initialize_reranker()
        
        logger.info("🔍 Hybrid Retriever initialized")
    
    def _initialize_sparse_retrieval(self):
        """Initialize sparse retrieval methods (BM25, TF-IDF)."""
        try:
            if self.vector_store.documents:
                # BM25 for keyword-based retrieval
                corpus = [doc.page_content for doc in self.vector_store.documents]
                tokenized_corpus = [doc.split() for doc in corpus]
                self.bm25_retriever = BM25Okapi(tokenized_corpus)
                
                # TF-IDF for term frequency analysis
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=10000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus)
                
                logger.info("✅ Sparse retrieval methods initialized")
        except Exception as e:
            logger.warning(f"Sparse retrieval initialization failed: {e}")
    
    def _initialize_reranker(self):
        """Initialize cross-encoder reranker."""
        try:
            if self.config.enable_reranking:
                self.reranker = CrossEncoder(self.config.reranker_model)
                logger.info("✅ Cross-encoder reranker initialized")
        except Exception as e:
            logger.warning(f"Reranker initialization failed: {e}")
    
    async def retrieve(
        self,
        query: str,
        mode: RetrievalMode = None
    ) -> RetrievalResult:
        """Perform advanced hybrid retrieval."""
        start_time = time.time()
        mode = mode or self.config.retrieval_mode
        
        # Expand query if enabled
        if self.config.enable_query_expansion:
            expanded_queries = await self._expand_query(query)
        else:
            expanded_queries = [query]
        
        all_results = []
        
        for expanded_query in expanded_queries:
            # Dense retrieval (vector similarity)
            dense_results = await self._dense_retrieval(expanded_query)
            
            # Sparse retrieval (BM25, TF-IDF)
            sparse_results = await self._sparse_retrieval(expanded_query)
            
            # Combine results based on strategy
            combined_results = await self._combine_results(
                dense_results, sparse_results, expanded_query
            )
            
            all_results.extend(combined_results)
        
        # Remove duplicates and merge scores
        unique_results = self._deduplicate_results(all_results)
        
        # Rerank if enabled
        if self.config.enable_reranking and self.reranker is not None:
            reranked_results = await self._rerank_results(query, unique_results)
        else:
            reranked_results = unique_results
        
        # Select top-k results
        final_results = reranked_results[:self.config.top_k_rerank]
        
        retrieval_time = time.time() - start_time
        
        return RetrievalResult(
            documents=[result[0] for result in final_results],
            scores=[result[1] for result in final_results],
            retrieval_time=retrieval_time,
            total_documents=len(unique_results),
            strategy_used=self.config.retrieval_strategy.value,
            confidence_score=self._calculate_confidence(final_results),
            sources=self._extract_sources(final_results),
            metadata={
                'query_expansion_count': len(expanded_queries),
                'dense_results': len(dense_results) if dense_results else 0,
                'sparse_results': len(sparse_results) if sparse_results else 0,
                'reranked': self.config.enable_reranking
            }
        )
    
    async def _dense_retrieval(self, query: str) -> List[Tuple[Document, float]]:
        """Perform dense vector retrieval."""
        return await self.vector_store.similarity_search(
            query,
            k=self.config.top_k_retrieval,
            threshold=self.config.similarity_threshold
        )
    
    async def _sparse_retrieval(self, query: str) -> List[Tuple[Document, float]]:
        """Perform sparse (keyword-based) retrieval."""
        if self.bm25_retriever is None:
            return []
        
        try:
            # BM25 retrieval
            tokenized_query = query.split()
            bm25_scores = self.bm25_retriever.get_scores(tokenized_query)
            
            # Get top results
            top_indices = np.argsort(bm25_scores)[::-1][:self.config.top_k_retrieval]
            
            results = []
            for idx in top_indices:
                if idx < len(self.vector_store.documents):
                    doc = self.vector_store.documents[idx]
                    score = float(bm25_scores[idx])
                    if score > 0:  # Only include relevant results
                        results.append((doc, score))
            
            return results
        except Exception as e:
            logger.warning(f"Sparse retrieval error: {e}")
            return []
    
    async def _combine_results(
        self,
        dense_results: List[Tuple[Document, float]],
        sparse_results: List[Tuple[Document, float]],
        query: str
    ) -> List[Tuple[Document, float]]:
        """Combine dense and sparse retrieval results."""
        if self.config.retrieval_strategy == RetrievalStrategy.DENSE_ONLY:
            return dense_results
        elif self.config.retrieval_strategy == RetrievalStrategy.SPARSE_ONLY:
            return sparse_results
        
        # Hybrid combination
        combined = {}
        
        # Add dense results with weight
        for doc, score in dense_results:
            doc_key = doc.page_content[:100]  # Use first 100 chars as key
            combined[doc_key] = {
                'document': doc,
                'dense_score': score,
                'sparse_score': 0.0
            }
        
        # Add sparse results with weight
        for doc, score in sparse_results:
            doc_key = doc.page_content[:100]
            if doc_key in combined:
                combined[doc_key]['sparse_score'] = score
            else:
                combined[doc_key] = {
                    'document': doc,
                    'dense_score': 0.0,
                    'sparse_score': score
                }
        
        # Calculate combined scores
        results = []
        for item in combined.values():
            # Weighted combination (can be tuned)
            combined_score = (0.7 * item['dense_score'] + 0.3 * item['sparse_score'])
            results.append((item['document'], combined_score))
        
        # Sort by combined score
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _deduplicate_results(
        self,
        results: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """Remove duplicate documents and merge scores."""
        seen = {}
        
        for doc, score in results:
            doc_hash = hashlib.md5(doc.page_content.encode()).hexdigest()
            
            if doc_hash in seen:
                # Merge scores (take maximum)
                seen[doc_hash] = (doc, max(seen[doc_hash][1], score))
            else:
                seen[doc_hash] = (doc, score)
        
        return list(seen.values())
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """Rerank results using cross-encoder."""
        if not results or self.reranker is None:
            return results
        
        try:
            # Prepare query-document pairs
            query_doc_pairs = [(query, doc.page_content) for doc, _ in results]
            
            # Get reranking scores
            rerank_scores = self.reranker.predict(query_doc_pairs)
            
            # Combine with original scores
            reranked_results = []
            for i, (doc, original_score) in enumerate(results):
                # Weighted combination of original and rerank scores
                combined_score = 0.3 * original_score + 0.7 * rerank_scores[i]
                reranked_results.append((doc, combined_score))
            
            # Sort by combined score
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            return reranked_results
            
        except Exception as e:
            logger.warning(f"Reranking error: {e}")
            return results
    
    async def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms and related terms."""
        expanded_queries = [query]
        
        try:
            # Simple query expansion (could be enhanced with word embeddings)
            # Add synonyms, handle typos, etc.
            
            # Crisis-specific expansions
            crisis_expansions = {
                'earthquake': ['seismic activity', 'tremor', 'quake'],
                'hurricane': ['typhoon', 'cyclone', 'tropical storm'],
                'flood': ['flooding', 'inundation', 'overflow'],
                'fire': ['wildfire', 'blaze', 'conflagration'],
                'pandemic': ['epidemic', 'outbreak', 'contagion']
            }
            
            query_lower = query.lower()
            for term, expansions in crisis_expansions.items():
                if term in query_lower:
                    for expansion in expansions:
                        expanded_query = query_lower.replace(term, expansion)
                        expanded_queries.append(expanded_query)
            
            return expanded_queries[:3]  # Limit to 3 expansions
            
        except Exception as e:
            logger.warning(f"Query expansion error: {e}")
            return [query]
    
    def _calculate_confidence(self, results: List[Tuple[Document, float]]) -> float:
        """Calculate overall confidence in retrieval results."""
        if not results:
            return 0.0
        
        scores = [score for _, score in results]
        
        # Confidence based on score distribution
        avg_score = np.mean(scores)
        score_variance = np.var(scores)
        
        # Higher confidence for higher average scores and lower variance
        confidence = avg_score * (1 / (1 + score_variance))
        return min(confidence, 1.0)
    
    def _extract_sources(self, results: List[Tuple[Document, float]]) -> List[str]:
        """Extract unique sources from results."""
        sources = set()
        
        for doc, _ in results:
            source = doc.metadata.get('source', 'Unknown')
            sources.add(source)
        
        return list(sources)


class ContextCompressor:
    """Advanced context compression for optimal LLM input."""
    
    def __init__(self, config: RAGConfig):
        """Initialize context compressor."""
        self.config = config
        self.summarizer = None
        self._initialize_summarizer()
    
    def _initialize_summarizer(self):
        """Initialize summarization model."""
        try:
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                max_length=150,
                min_length=50,
                do_sample=False
            )
            logger.info("✅ Context summarizer initialized")
        except Exception as e:
            logger.warning(f"Summarizer initialization failed: {e}")
    
    async def compress_context(
        self,
        documents: List[Document],
        query: str,
        max_length: int = None
    ) -> str:
        """Compress context while preserving relevant information."""
        max_length = max_length or self.config.max_context_length
        
        if not documents:
            return ""
        
        # Combine all document content
        full_context = "\n\n".join([doc.page_content for doc in documents])
        
        # If already within limit, return as is
        if len(full_context) <= max_length:
            return full_context
        
        # Apply compression strategies
        compressed_context = await self._apply_compression_strategies(
            full_context, query, max_length
        )
        
        return compressed_context
    
    async def _apply_compression_strategies(
        self,
        context: str,
        query: str,
        max_length: int
    ) -> str:
        """Apply various compression strategies."""
        # Strategy 1: Extract most relevant sentences
        relevant_context = self._extract_relevant_sentences(context, query, max_length)
        
        if len(relevant_context) <= max_length:
            return relevant_context
        
        # Strategy 2: Summarization
        if self.summarizer is not None:
            try:
                # Split into chunks for summarization
                chunks = self._split_text_for_summarization(relevant_context)
                summaries = []
                
                for chunk in chunks:
                    if len(chunk) > 100:  # Only summarize substantial chunks
                        summary = self.summarizer(chunk, max_length=150, min_length=50)
                        summaries.append(summary[0]['summary_text'])
                    else:
                        summaries.append(chunk)
                
                summarized_context = "\n\n".join(summaries)
                
                if len(summarized_context) <= max_length:
                    return summarized_context
                
            except Exception as e:
                logger.warning(f"Summarization error: {e}")
        
        # Strategy 3: Truncate with priority
        return self._intelligent_truncation(relevant_context, max_length)
    
    def _extract_relevant_sentences(self, context: str, query: str, max_length: int) -> str:
        """Extract most relevant sentences based on query."""
        sentences = re.split(r'[.!?]+', context)
        query_words = set(query.lower().split())
        
        # Score sentences by relevance
        sentence_scores = []
        for sentence in sentences:
            if len(sentence.strip()) < 20:  # Skip very short sentences
                continue
            
            sentence_words = set(sentence.lower().split())
            overlap_score = len(query_words.intersection(sentence_words)) / len(query_words)
            sentence_scores.append((sentence.strip(), overlap_score))
        
        # Sort by relevance score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select sentences up to max_length
        selected_sentences = []
        current_length = 0
        
        for sentence, score in sentence_scores:
            if current_length + len(sentence) <= max_length:
                selected_sentences.append(sentence)
                current_length += len(sentence) + 2  # +2 for spacing
            else:
                break
        
        return ". ".join(selected_sentences)
    
    def _split_text_for_summarization(self, text: str) -> List[str]:
        """Split text into chunks suitable for summarization."""
        # Split into paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > 1000:  # Max chunk size for summarizer
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = paragraph
                else:
                    chunks.append(paragraph)
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _intelligent_truncation(self, context: str, max_length: int) -> str:
        """Intelligently truncate context preserving important information."""
        if len(context) <= max_length:
            return context
        
        # Try to end at sentence boundary
        truncated = context[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.8:  # If we can end reasonably close to limit
            return truncated[:last_period + 1]
        else:
            return truncated + "..."


class AccuracyEnhancer:
    """System to enhance response accuracy through various techniques."""
    
    def __init__(self, config: RAGConfig):
        """Initialize accuracy enhancer."""
        self.config = config
        self.fact_checker = None
        self.consistency_checker = None
        self._initialize_checkers()
    
    def _initialize_checkers(self):
        """Initialize fact and consistency checkers."""
        try:
            # Initialize fact checking pipeline
            self.fact_checker = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",  # Placeholder
                return_all_scores=True
            )
            logger.info("✅ Fact checker initialized")
        except Exception as e:
            logger.warning(f"Fact checker initialization failed: {e}")
    
    async def enhance_accuracy(
        self,
        response: str,
        context: str,
        query: str
    ) -> Dict[str, Any]:
        """Enhance response accuracy and provide accuracy indicators."""
        accuracy_indicators = {}
        
        # Check factual consistency
        consistency_score = await self._check_consistency(response, context)
        accuracy_indicators['consistency_score'] = consistency_score
        
        # Check completeness
        completeness_score = await self._check_completeness(response, query)
        accuracy_indicators['completeness_score'] = completeness_score
        
        # Check relevance
        relevance_score = await self._check_relevance(response, query)
        accuracy_indicators['relevance_score'] = relevance_score
        
        # Check specificity
        specificity_score = await self._check_specificity(response)
        accuracy_indicators['specificity_score'] = specificity_score
        
        # Calculate overall accuracy score
        overall_accuracy = np.mean(list(accuracy_indicators.values()))
        accuracy_indicators['overall_accuracy'] = overall_accuracy
        
        return accuracy_indicators
    
    async def _check_consistency(self, response: str, context: str) -> float:
        """Check if response is consistent with provided context."""
        if not context or not response:
            return 0.0
        
        try:
            # Simple consistency check based on overlapping concepts
            response_words = set(response.lower().split())
            context_words = set(context.lower().split())
            
            # Calculate overlap
            overlap = len(response_words.intersection(context_words))
            total_response_words = len(response_words)
            
            if total_response_words == 0:
                return 0.0
            
            consistency_score = overlap / total_response_words
            return min(consistency_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Consistency check error: {e}")
            return 0.5
    
    async def _check_completeness(self, response: str, query: str) -> float:
        """Check if response completely addresses the query."""
        try:
            # Extract key components from query
            query_components = self._extract_query_components(query)
            
            # Check if response addresses each component
            addressed_components = 0
            for component in query_components:
                if component.lower() in response.lower():
                    addressed_components += 1
            
            if len(query_components) == 0:
                return 1.0
            
            completeness_score = addressed_components / len(query_components)
            return completeness_score
            
        except Exception as e:
            logger.warning(f"Completeness check error: {e}")
            return 0.5
    
    async def _check_relevance(self, response: str, query: str) -> float:
        """Check relevance of response to query."""
        try:
            # Simple relevance based on keyword overlap and semantic similarity
            query_words = set(query.lower().split())
            response_words = set(response.lower().split())
            
            # Keyword overlap
            overlap = len(query_words.intersection(response_words))
            relevance_score = overlap / len(query_words) if query_words else 0
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            logger.warning(f"Relevance check error: {e}")
            return 0.5
    
    async def _check_specificity(self, response: str) -> float:
        """Check specificity and detail level of response."""
        try:
            # Factors indicating specificity
            specificity_indicators = 0
            
            # Check for numbers/statistics
            if re.search(r'\d+', response):
                specificity_indicators += 1
            
            # Check for dates
            if re.search(r'\b\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', response):
                specificity_indicators += 1
            
            # Check for proper nouns (locations, organizations)
            words = response.split()
            capitalized_words = [w for w in words if w[0].isupper() and len(w) > 1]
            if len(capitalized_words) >= 3:
                specificity_indicators += 1
            
            # Check for specific terms (vs. vague language)
            vague_terms = ['some', 'many', 'several', 'various', 'often', 'sometimes']
            specific_terms = ['approximately', 'exactly', 'precisely', 'according to']
            
            vague_count = sum(1 for term in vague_terms if term in response.lower())
            specific_count = sum(1 for term in specific_terms if term in response.lower())
            
            if specific_count > vague_count:
                specificity_indicators += 1
            
            # Normalize score
            specificity_score = min(specificity_indicators / 4, 1.0)
            return specificity_score
            
        except Exception as e:
            logger.warning(f"Specificity check error: {e}")
            return 0.5
    
    def _extract_query_components(self, query: str) -> List[str]:
        """Extract key components from query."""
        # Simple component extraction (could be enhanced with NLP)
        components = []
        
        # Extract question words
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'which']
        for word in question_words:
            if word in query.lower():
                components.append(word)
        
        # Extract key nouns (simplified)
        words = query.split()
        potential_nouns = [word for word in words if len(word) > 3 and word.islower()]
        components.extend(potential_nouns[:3])  # Take first 3
        
        return components


class AdvancedRAGSystem:
    """Main advanced RAG system combining all components."""
    
    def __init__(self, config: RAGConfig = None):
        """Initialize advanced RAG system."""
        self.config = config or RAGConfig()
        self.vector_store = AdvancedVectorStore(self.config)
        self.retriever = HybridRetriever(self.config, self.vector_store)
        self.context_compressor = ContextCompressor(self.config)
        self.accuracy_enhancer = AccuracyEnhancer(self.config)
        
        # Initialize LLM clients
        self.llm_clients = {}
        self._initialize_llm_clients()
        
        logger.info("🚀 Advanced RAG System initialized")
    
    def _initialize_llm_clients(self):
        """Initialize LLM clients."""
        try:
            # OpenAI client
            if os.getenv('OPENAI_API_KEY'):
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.llm_clients['openai'] = openai
                logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.warning(f"OpenAI client initialization failed: {e}")
        
        try:
            # Anthropic client
            if os.getenv('ANTHROPIC_API_KEY'):
                self.llm_clients['anthropic'] = anthropic.Anthropic(
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
                logger.info("✅ Anthropic client initialized")
        except Exception as e:
            logger.warning(f"Anthropic client initialization failed: {e}")
    
    async def add_knowledge_base(self, documents: List[str], metadata: List[Dict] = None):
        """Add documents to the knowledge base."""
        logger.info(f"📚 Adding {len(documents)} documents to knowledge base")
        
        # Process documents
        processed_docs = await self._process_documents(documents, metadata)
        
        # Add to vector store
        await self.vector_store.add_documents(processed_docs)
        
        # Update retrievers
        self.retriever._initialize_sparse_retrieval()
        
        logger.info("✅ Knowledge base updated")
    
    async def _process_documents(
        self,
        documents: List[str],
        metadata: List[Dict] = None
    ) -> List[Document]:
        """Process documents for optimal retrieval."""
        metadata = metadata or [{}] * len(documents)
        
        # Initialize text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        processed_docs = []
        
        for i, (doc_text, doc_metadata) in enumerate(zip(documents, metadata)):
            # Split document into chunks
            chunks = text_splitter.split_text(doc_text)
            
            for j, chunk in enumerate(chunks):
                chunk_metadata = doc_metadata.copy()
                chunk_metadata.update({
                    'document_id': i,
                    'chunk_id': j,
                    'total_chunks': len(chunks)
                })
                
                processed_docs.append(Document(
                    page_content=chunk,
                    metadata=chunk_metadata
                ))
        
        return processed_docs
    
    async def generate_response(
        self,
        query: str,
        model: str = "gpt-4",
        mode: RetrievalMode = None
    ) -> RAGResponse:
        """Generate enhanced response using RAG."""
        start_time = time.time()
        
        logger.info(f"🎯 Generating RAG response for: {query[:100]}...")
        
        try:
            # Retrieve relevant context
            retrieval_result = await self.retriever.retrieve(query, mode)
            
            # Compress context
            compressed_context = await self.context_compressor.compress_context(
                retrieval_result.documents,
                query
            )
            
            # Generate response with LLM
            response_text = await self._generate_llm_response(
                query, compressed_context, model
            )
            
            # Enhance accuracy
            accuracy_indicators = await self.accuracy_enhancer.enhance_accuracy(
                response_text, compressed_context, query
            )
            
            # Calculate confidence
            confidence = self._calculate_overall_confidence(
                retrieval_result.confidence_score,
                accuracy_indicators['overall_accuracy']
            )
            
            # Prepare sources
            sources = self._prepare_sources(retrieval_result.documents)
            
            processing_time = time.time() - start_time
            
            return RAGResponse(
                answer=response_text,
                confidence=confidence,
                sources=sources,
                retrieval_info=retrieval_result,
                processing_time=processing_time,
                model_used=model,
                context_length=len(compressed_context),
                accuracy_indicators=accuracy_indicators
            )
            
        except Exception as e:
            logger.error(f"RAG response generation error: {e}")
            raise
    
    async def _generate_llm_response(
        self,
        query: str,
        context: str,
        model: str
    ) -> str:
        """Generate response using specified LLM."""
        system_prompt = """You are an expert crisis analyst with deep knowledge of disaster management, emergency response, and global crisis patterns. 

Based on the provided context, answer the user's question with:
1. Accurate, factual information
2. Specific details and statistics when available
3. Clear explanations of impacts and consequences
4. Actionable insights when relevant
5. Proper attribution to sources

If the context doesn't contain enough information to fully answer the question, clearly state what information is missing."""

        user_prompt = f"""Context: {context}

Question: {query}

Please provide a comprehensive and accurate answer based on the context provided."""

        try:
            if model.startswith('gpt') and 'openai' in self.llm_clients:
                response = await openai.ChatCompletion.acreate(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Low temperature for accuracy
                    max_tokens=800
                )
                return response.choices[0].message.content
            
            elif model.startswith('claude') and 'anthropic' in self.llm_clients:
                message = await self.llm_clients['anthropic'].messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=800,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return message.content[0].text
            
            else:
                # Fallback to a simple response
                return f"Based on the available information: {context[:500]}..."
                
        except Exception as e:
            logger.error(f"LLM response generation error: {e}")
            return "I apologize, but I'm unable to generate a response at this time due to a technical issue."
    
    def _calculate_overall_confidence(
        self,
        retrieval_confidence: float,
        accuracy_score: float
    ) -> float:
        """Calculate overall confidence score."""
        # Weighted combination of retrieval and accuracy confidence
        overall_confidence = 0.6 * retrieval_confidence + 0.4 * accuracy_score
        return min(overall_confidence, 1.0)
    
    def _prepare_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Prepare source information for response."""
        sources = []
        
        for doc in documents:
            source_info = {
                'content_preview': doc.page_content[:200] + "...",
                'metadata': doc.metadata,
                'source': doc.metadata.get('source', 'Unknown'),
                'relevance': 'High'  # Could be calculated based on retrieval scores
            }
            sources.append(source_info)
        
        return sources


# Global RAG system instance
_rag_system = None

def get_rag_system() -> AdvancedRAGSystem:
    """Get global RAG system instance."""
    global _rag_system
    if _rag_system is None:
        _rag_system = AdvancedRAGSystem()
    return _rag_system


# Convenience functions
async def add_crisis_knowledge(documents: List[str], metadata: List[Dict] = None):
    """Add crisis-related documents to knowledge base."""
    rag_system = get_rag_system()
    await rag_system.add_knowledge_base(documents, metadata)


async def get_enhanced_response(query: str, model: str = "gpt-4") -> RAGResponse:
    """Get enhanced response using RAG system."""
    rag_system = get_rag_system()
    return await rag_system.generate_response(query, model)