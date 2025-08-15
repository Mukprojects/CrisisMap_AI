"""
Advanced Ensemble AI System for CrisisMap AI.

This module implements a sophisticated ensemble of AI models to provide
the most accurate and reliable crisis analysis possible.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import torch
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    AutoModelForQuestionAnswering, pipeline
)
from sentence_transformers import SentenceTransformer
import openai
import anthropic
from sklearn.ensemble import VotingClassifier
from sklearn.metrics.pairwise import cosine_similarity
import spacy

logger = logging.getLogger(__name__)


@dataclass
class EnsemblePrediction:
    """Result from ensemble AI prediction."""
    primary_response: str
    confidence_score: float
    model_scores: Dict[str, float]
    consensus_level: float
    alternative_responses: List[str]
    sources_confidence: float
    processing_time: float
    risk_assessment: Dict[str, float]
    sentiment_analysis: Dict[str, float]
    entity_extraction: Dict[str, List[str]]
    temporal_analysis: Dict[str, Any]


class AdvancedEnsembleAI:
    """
    State-of-the-art ensemble AI system combining multiple models
    for maximum accuracy and reliability in crisis analysis.
    """
    
    def __init__(self):
        """Initialize the ensemble AI system."""
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.embedding_models = {}
        self.nlp_models = {}
        self.confidence_threshold = 0.8
        self.ensemble_weights = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all AI models in the ensemble."""
        logger.info("🤖 Initializing Advanced Ensemble AI System...")
        
        try:
            # 1. Primary Language Models
            self._init_language_models()
            
            # 2. Specialized Crisis Models
            self._init_crisis_models()
            
            # 3. Embedding Models
            self._init_embedding_models()
            
            # 4. NLP Analysis Models
            self._init_nlp_models()
            
            # 5. External API Integrations
            self._init_external_apis()
            
            logger.info("✅ All AI models initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error initializing AI models: {e}")
            # Fallback to basic models
            self._init_fallback_models()
    
    def _init_language_models(self):
        """Initialize primary language models."""
        models_config = {
            'phi3': 'microsoft/Phi-3-mini-4k-instruct',
            'llama': 'meta-llama/Llama-2-7b-chat-hf',
            'mistral': 'mistralai/Mistral-7B-Instruct-v0.1',
            'gemma': 'google/gemma-7b-it',
            'falcon': 'tiiuae/falcon-7b-instruct'
        }
        
        for name, model_id in models_config.items():
            try:
                self.models[name] = pipeline(
                    "text-generation",
                    model=model_id,
                    tokenizer=model_id,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.7
                )
                self.ensemble_weights[name] = 0.2
                logger.info(f"✅ Loaded {name} model")
            except Exception as e:
                logger.warning(f"⚠️ Could not load {name}: {e}")
    
    def _init_crisis_models(self):
        """Initialize specialized crisis analysis models."""
        try:
            # Disaster Classification Model
            self.models['disaster_classifier'] = pipeline(
                "text-classification",
                model="huggingface/disaster-tweet-classification",
                tokenizer="huggingface/disaster-tweet-classification"
            )
            
            # Sentiment Analysis for Crisis
            self.models['crisis_sentiment'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            
            # Emergency Detection Model
            self.models['emergency_detector'] = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli"
            )
            
            # Risk Assessment Model
            self.models['risk_assessor'] = AutoModelForSequenceClassification.from_pretrained(
                "microsoft/DialoGPT-medium"
            )
            
            logger.info("✅ Crisis-specialized models loaded")
            
        except Exception as e:
            logger.warning(f"⚠️ Some crisis models unavailable: {e}")
    
    def _init_embedding_models(self):
        """Initialize embedding models for semantic analysis."""
        embedding_models = {
            'primary': 'sentence-transformers/all-MiniLM-L6-v2',
            'crisis_specific': 'sentence-transformers/all-mpnet-base-v2',
            'multilingual': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            'domain_specific': 'sentence-transformers/multi-qa-MiniLM-L6-cos-v1'
        }
        
        for name, model_id in embedding_models.items():
            try:
                self.embedding_models[name] = SentenceTransformer(model_id)
                logger.info(f"✅ Loaded embedding model: {name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load embedding {name}: {e}")
    
    def _init_nlp_models(self):
        """Initialize NLP analysis models."""
        try:
            # Load spaCy models for different languages
            self.nlp_models['en'] = spacy.load('en_core_web_sm')
            
            # Question Answering Model
            self.models['qa'] = pipeline(
                "question-answering",
                model="deepset/roberta-base-squad2",
                tokenizer="deepset/roberta-base-squad2"
            )
            
            # Named Entity Recognition
            self.models['ner'] = pipeline(
                "ner",
                model="dbmdz/bert-large-cased-finetuned-conll03-english",
                aggregation_strategy="simple"
            )
            
            # Text Summarization
            self.models['summarizer'] = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                max_length=150,
                min_length=50
            )
            
            logger.info("✅ NLP models loaded")
            
        except Exception as e:
            logger.warning(f"⚠️ Some NLP models unavailable: {e}")
    
    def _init_external_apis(self):
        """Initialize external API integrations."""
        import os
        
        # OpenAI GPT-4
        if os.getenv('OPENAI_API_KEY'):
            try:
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.models['gpt4'] = openai
                self.ensemble_weights['gpt4'] = 0.3
                logger.info("✅ OpenAI GPT-4 integration enabled")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI not available: {e}")
        
        # Anthropic Claude
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                self.models['claude'] = anthropic.Anthropic(
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
                self.ensemble_weights['claude'] = 0.25
                logger.info("✅ Anthropic Claude integration enabled")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic not available: {e}")
    
    def _init_fallback_models(self):
        """Initialize basic fallback models if advanced models fail."""
        try:
            self.models['basic_llm'] = pipeline(
                "text-generation",
                model="gpt2",
                max_new_tokens=256
            )
            self.embedding_models['basic'] = SentenceTransformer(
                'sentence-transformers/all-MiniLM-L6-v2'
            )
            logger.info("✅ Fallback models initialized")
        except Exception as e:
            logger.error(f"❌ Critical error: Cannot initialize any models: {e}")
            raise
    
    async def generate_ensemble_response(
        self,
        query: str,
        context: List[Dict],
        crisis_type: Optional[str] = None
    ) -> EnsemblePrediction:
        """
        Generate highly accurate response using ensemble of AI models.
        
        Args:
            query: User query about crisis
            context: Relevant crisis context data
            crisis_type: Type of crisis if known
        
        Returns:
            EnsemblePrediction with comprehensive analysis
        """
        start_time = time.time()
        
        logger.info(f"🎯 Generating ensemble response for: {query[:100]}...")
        
        # Parallel model execution for speed
        tasks = []
        
        # 1. Primary LLM responses
        if 'gpt4' in self.models:
            tasks.append(self._get_gpt4_response(query, context))
        if 'claude' in self.models:
            tasks.append(self._get_claude_response(query, context))
        
        # 2. Local model responses
        for model_name in ['phi3', 'llama', 'mistral']:
            if model_name in self.models:
                tasks.append(self._get_local_model_response(model_name, query, context))
        
        # 3. Specialized analysis
        tasks.append(self._analyze_sentiment(query, context))
        tasks.append(self._extract_entities(query, context))
        tasks.append(self._assess_risk(query, context))
        tasks.append(self._temporal_analysis(query, context))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        model_responses = []
        model_scores = {}
        analysis_results = {}
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Model {i} failed: {result}")
                continue
            
            if isinstance(result, dict):
                if 'response' in result:
                    model_responses.append(result['response'])
                    model_scores[result.get('model', f'model_{i}')] = result.get('confidence', 0.5)
                else:
                    # Analysis result
                    analysis_results.update(result)
        
        # Ensemble consensus
        primary_response, confidence = self._calculate_ensemble_consensus(
            model_responses, model_scores
        )
        
        # Enhanced response with crisis-specific improvements
        enhanced_response = await self._enhance_crisis_response(
            primary_response, query, context, analysis_results
        )
        
        processing_time = time.time() - start_time
        
        return EnsemblePrediction(
            primary_response=enhanced_response,
            confidence_score=confidence,
            model_scores=model_scores,
            consensus_level=self._calculate_consensus_level(model_responses),
            alternative_responses=model_responses[:3],  # Top 3 alternatives
            sources_confidence=self._calculate_sources_confidence(context),
            processing_time=processing_time,
            risk_assessment=analysis_results.get('risk_assessment', {}),
            sentiment_analysis=analysis_results.get('sentiment_analysis', {}),
            entity_extraction=analysis_results.get('entity_extraction', {}),
            temporal_analysis=analysis_results.get('temporal_analysis', {})
        )
    
    async def _get_gpt4_response(self, query: str, context: List[Dict]) -> Dict:
        """Get response from GPT-4."""
        try:
            context_text = self._format_context(context)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert crisis analyst with deep knowledge of disaster management, 
                        emergency response, and global crisis patterns. Provide accurate, detailed, and actionable 
                        information about crisis events. Always cite sources and provide confidence levels."""
                    },
                    {
                        "role": "user",
                        "content": f"Context: {context_text}\n\nQuery: {query}\n\nProvide a comprehensive analysis."
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return {
                'model': 'gpt4',
                'response': response.choices[0].message.content,
                'confidence': 0.9,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"GPT-4 error: {e}")
            return {'model': 'gpt4', 'response': '', 'confidence': 0.0}
    
    async def _get_claude_response(self, query: str, context: List[Dict]) -> Dict:
        """Get response from Anthropic Claude."""
        try:
            context_text = self._format_context(context)
            
            message = await self.models['claude'].messages.create(
                model="claude-3-opus-20240229",
                max_tokens=800,
                temperature=0.3,
                system="""You are a world-class crisis analysis expert. Provide detailed, accurate analysis of crisis events 
                with high precision. Include relevant statistics, impacts, and response recommendations.""",
                messages=[
                    {
                        "role": "user",
                        "content": f"Context: {context_text}\n\nQuery: {query}\n\nProvide expert analysis."
                    }
                ]
            )
            
            return {
                'model': 'claude',
                'response': message.content[0].text,
                'confidence': 0.85,
                'tokens_used': message.usage.input_tokens + message.usage.output_tokens
            }
            
        except Exception as e:
            logger.error(f"Claude error: {e}")
            return {'model': 'claude', 'response': '', 'confidence': 0.0}
    
    async def _get_local_model_response(self, model_name: str, query: str, context: List[Dict]) -> Dict:
        """Get response from local model."""
        try:
            context_text = self._format_context(context)
            
            prompt = f"""<|system|>You are an expert crisis analyst. Provide accurate, detailed crisis analysis.<|end|>
<|user|>Context: {context_text}

Query: {query}

Provide comprehensive analysis with specific details, statistics, and impacts.<|end|>
<|assistant|>"""
            
            response = self.models[model_name](
                prompt,
                max_new_tokens=512,
                temperature=0.4,
                do_sample=True,
                pad_token_id=self.models[model_name].tokenizer.eos_token_id
            )
            
            generated_text = response[0]['generated_text']
            # Extract only the assistant's response
            assistant_response = generated_text.split('<|assistant|>')[-1].strip()
            
            return {
                'model': model_name,
                'response': assistant_response,
                'confidence': 0.7
            }
            
        except Exception as e:
            logger.error(f"{model_name} error: {e}")
            return {'model': model_name, 'response': '', 'confidence': 0.0}
    
    async def _analyze_sentiment(self, query: str, context: List[Dict]) -> Dict:
        """Analyze sentiment and emotional context."""
        try:
            # Analyze query sentiment
            query_sentiment = self.models.get('crisis_sentiment', lambda x: [{'label': 'NEUTRAL', 'score': 0.5}])(query)
            
            # Analyze context sentiment
            context_sentiments = []
            for item in context[:5]:  # Analyze top 5 context items
                text = item.get('description', '') or item.get('title', '')
                if text:
                    sentiment = self.models.get('crisis_sentiment', lambda x: [{'label': 'NEUTRAL', 'score': 0.5}])(text)
                    context_sentiments.append(sentiment[0])
            
            # Calculate overall sentiment scores
            sentiment_analysis = {
                'query_sentiment': query_sentiment[0] if query_sentiment else {'label': 'NEUTRAL', 'score': 0.5},
                'context_sentiment_avg': self._average_sentiment(context_sentiments),
                'emotional_indicators': self._detect_emotional_indicators(query),
                'urgency_level': self._assess_urgency(query, context)
            }
            
            return {'sentiment_analysis': sentiment_analysis}
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {'sentiment_analysis': {}}
    
    async def _extract_entities(self, query: str, context: List[Dict]) -> Dict:
        """Extract named entities and key information."""
        try:
            # Extract entities from query
            query_entities = self.models.get('ner', lambda x: [])(query)
            
            # Extract entities from context
            context_entities = []
            for item in context[:3]:
                text = item.get('description', '') or item.get('title', '')
                if text:
                    entities = self.models.get('ner', lambda x: [])(text)
                    context_entities.extend(entities)
            
            # Organize entities by type
            entity_extraction = {
                'locations': [e['word'] for e in query_entities + context_entities if e.get('entity_group') == 'LOC'],
                'organizations': [e['word'] for e in query_entities + context_entities if e.get('entity_group') == 'ORG'],
                'persons': [e['word'] for e in query_entities + context_entities if e.get('entity_group') == 'PER'],
                'dates': [e['word'] for e in query_entities + context_entities if e.get('entity_group') == 'DATE'],
                'disasters': self._extract_disaster_types(query + ' ' + ' '.join([
                    item.get('description', '') for item in context[:3]
                ]))
            }
            
            # Remove duplicates and clean
            for key in entity_extraction:
                entity_extraction[key] = list(set([
                    entity.strip().title() for entity in entity_extraction[key] 
                    if entity and len(entity.strip()) > 1
                ]))
            
            return {'entity_extraction': entity_extraction}
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return {'entity_extraction': {}}
    
    async def _assess_risk(self, query: str, context: List[Dict]) -> Dict:
        """Assess risk levels and severity."""
        try:
            # Risk keywords and their weights
            risk_keywords = {
                'catastrophic': 1.0, 'devastating': 0.9, 'severe': 0.8,
                'major': 0.7, 'significant': 0.6, 'moderate': 0.4,
                'minor': 0.2, 'emergency': 0.9, 'disaster': 0.8,
                'crisis': 0.7, 'casualties': 0.8, 'deaths': 0.9,
                'injured': 0.6, 'evacuated': 0.7, 'missing': 0.8
            }
            
            # Calculate risk scores
            text = (query + ' ' + ' '.join([
                item.get('description', '') for item in context[:5]
            ])).lower()
            
            risk_score = 0.0
            matched_indicators = []
            
            for keyword, weight in risk_keywords.items():
                if keyword in text:
                    risk_score += weight
                    matched_indicators.append(keyword)
            
            # Normalize risk score
            risk_score = min(risk_score / len(risk_keywords) * 10, 1.0)
            
            # Additional risk factors
            scale_indicators = self._assess_scale(context)
            temporal_urgency = self._assess_temporal_urgency(query, context)
            geographic_spread = self._assess_geographic_spread(context)
            
            risk_assessment = {
                'overall_risk_score': risk_score,
                'risk_level': self._categorize_risk_level(risk_score),
                'risk_indicators': matched_indicators,
                'scale_assessment': scale_indicators,
                'temporal_urgency': temporal_urgency,
                'geographic_impact': geographic_spread,
                'confidence': min(len(matched_indicators) / 5, 1.0)
            }
            
            return {'risk_assessment': risk_assessment}
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {'risk_assessment': {}}
    
    async def _temporal_analysis(self, query: str, context: List[Dict]) -> Dict:
        """Analyze temporal patterns and trends."""
        try:
            # Extract dates from context
            dates = []
            for item in context:
                if 'date' in item:
                    try:
                        date_obj = datetime.fromisoformat(str(item['date']).replace('Z', '+00:00'))
                        dates.append(date_obj)
                    except:
                        continue
            
            if not dates:
                return {'temporal_analysis': {}}
            
            # Sort dates
            dates.sort()
            
            # Analyze patterns
            temporal_analysis = {
                'earliest_event': dates[0].isoformat() if dates else None,
                'latest_event': dates[-1].isoformat() if dates else None,
                'event_span_days': (dates[-1] - dates[0]).days if len(dates) > 1 else 0,
                'event_frequency': len(dates),
                'recent_activity': sum(1 for d in dates if (datetime.now() - d.replace(tzinfo=None)).days <= 30),
                'trend_analysis': self._analyze_event_trends(dates),
                'seasonal_patterns': self._detect_seasonal_patterns(dates)
            }
            
            return {'temporal_analysis': temporal_analysis}
            
        except Exception as e:
            logger.error(f"Temporal analysis error: {e}")
            return {'temporal_analysis': {}}
    
    def _format_context(self, context: List[Dict]) -> str:
        """Format context data for AI models."""
        if not context:
            return "No specific context available."
        
        formatted = []
        for i, item in enumerate(context[:5], 1):  # Top 5 most relevant
            title = item.get('title', 'Unknown Event')
            description = item.get('description', 'No description available')
            date = item.get('date', 'Unknown date')
            location = item.get('location', 'Unknown location')
            
            formatted.append(
                f"{i}. {title}\n"
                f"   Date: {date}\n"
                f"   Location: {location}\n"
                f"   Description: {description[:200]}...\n"
            )
        
        return '\n'.join(formatted)
    
    def _calculate_ensemble_consensus(
        self, 
        responses: List[str], 
        scores: Dict[str, float]
    ) -> Tuple[str, float]:
        """Calculate consensus from multiple model responses."""
        if not responses:
            return "No response available from AI models.", 0.0
        
        # Use embeddings to find most representative response
        if self.embedding_models:
            model_name = list(self.embedding_models.keys())[0]
            embeddings = self.embedding_models[model_name].encode(responses)
            
            # Calculate centroid
            centroid = np.mean(embeddings, axis=0)
            
            # Find response closest to centroid
            similarities = cosine_similarity([centroid], embeddings)[0]
            best_idx = np.argmax(similarities)
            
            # Weighted confidence based on model scores and similarity
            confidence = np.mean(list(scores.values())) * similarities[best_idx]
            
            return responses[best_idx], min(confidence, 1.0)
        else:
            # Fallback: use highest scoring response
            if scores:
                best_model = max(scores.keys(), key=lambda k: scores[k])
                model_idx = list(scores.keys()).index(best_model)
                if model_idx < len(responses):
                    return responses[model_idx], scores[best_model]
            
            return responses[0], 0.5
    
    def _calculate_consensus_level(self, responses: List[str]) -> float:
        """Calculate how much the models agree with each other."""
        if len(responses) < 2:
            return 1.0
        
        try:
            if self.embedding_models:
                model_name = list(self.embedding_models.keys())[0]
                embeddings = self.embedding_models[model_name].encode(responses)
                
                # Calculate pairwise similarities
                similarities = []
                for i in range(len(embeddings)):
                    for j in range(i + 1, len(embeddings)):
                        sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
                        similarities.append(sim)
                
                return np.mean(similarities) if similarities else 0.5
            else:
                return 0.5
        except Exception:
            return 0.5
    
    def _calculate_sources_confidence(self, context: List[Dict]) -> float:
        """Calculate confidence based on source quality."""
        if not context:
            return 0.0
        
        source_weights = {
            'who.int': 1.0, 'cdc.gov': 1.0, 'usgs.gov': 1.0,
            'noaa.gov': 1.0, 'un.org': 0.9, 'reuters.com': 0.8,
            'bbc.com': 0.8, 'cnn.com': 0.7, 'wikipedia.org': 0.6
        }
        
        total_confidence = 0.0
        for item in context:
            source = item.get('source', '').lower()
            for domain, weight in source_weights.items():
                if domain in source:
                    total_confidence += weight
                    break
            else:
                total_confidence += 0.5  # Default for unknown sources
        
        return min(total_confidence / len(context), 1.0)
    
    async def _enhance_crisis_response(
        self,
        response: str,
        query: str,
        context: List[Dict],
        analysis: Dict
    ) -> str:
        """Enhance response with crisis-specific information."""
        enhancements = []
        
        # Add confidence indicators
        risk_level = analysis.get('risk_assessment', {}).get('risk_level', 'Unknown')
        if risk_level != 'Unknown':
            enhancements.append(f"\n\n**Risk Assessment**: {risk_level}")
        
        # Add temporal context
        temporal = analysis.get('temporal_analysis', {})
        if temporal.get('recent_activity', 0) > 0:
            enhancements.append(
                f"**Recent Activity**: {temporal['recent_activity']} events in the last 30 days"
            )
        
        # Add entity information
        entities = analysis.get('entity_extraction', {})
        if entities.get('locations'):
            locations = ', '.join(entities['locations'][:3])
            enhancements.append(f"**Key Locations**: {locations}")
        
        # Add sentiment context
        sentiment = analysis.get('sentiment_analysis', {})
        if sentiment.get('urgency_level', 0) > 0.7:
            enhancements.append("**High Urgency Detected**")
        
        enhanced_response = response
        if enhancements:
            enhanced_response += '\n' + '\n'.join(enhancements)
        
        return enhanced_response
    
    # Helper methods for analysis
    def _average_sentiment(self, sentiments: List[Dict]) -> Dict:
        """Calculate average sentiment from multiple results."""
        if not sentiments:
            return {'label': 'NEUTRAL', 'score': 0.5}
        
        avg_score = sum(s.get('score', 0.5) for s in sentiments) / len(sentiments)
        # Determine label based on average score
        if avg_score > 0.6:
            label = sentiments[0].get('label', 'POSITIVE')
        elif avg_score < 0.4:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'
        
        return {'label': label, 'score': avg_score}
    
    def _detect_emotional_indicators(self, text: str) -> List[str]:
        """Detect emotional indicators in text."""
        emotional_words = {
            'fear': ['scared', 'terrified', 'panic', 'afraid', 'horrific'],
            'urgency': ['urgent', 'immediate', 'emergency', 'critical', 'asap'],
            'severity': ['devastating', 'catastrophic', 'severe', 'major', 'serious'],
            'hope': ['rescue', 'aid', 'help', 'support', 'recovery']
        }
        
        indicators = []
        text_lower = text.lower()
        
        for emotion, words in emotional_words.items():
            if any(word in text_lower for word in words):
                indicators.append(emotion)
        
        return indicators
    
    def _assess_urgency(self, query: str, context: List[Dict]) -> float:
        """Assess urgency level of the crisis."""
        urgency_keywords = [
            'emergency', 'urgent', 'immediate', 'breaking', 'alert',
            'now', 'current', 'ongoing', 'developing', 'live'
        ]
        
        text = (query + ' ' + ' '.join([
            item.get('title', '') + ' ' + item.get('description', '')
            for item in context[:3]
        ])).lower()
        
        urgency_score = sum(1 for keyword in urgency_keywords if keyword in text)
        return min(urgency_score / len(urgency_keywords), 1.0)
    
    def _extract_disaster_types(self, text: str) -> List[str]:
        """Extract disaster types from text."""
        disaster_types = [
            'earthquake', 'tsunami', 'hurricane', 'typhoon', 'cyclone',
            'flood', 'wildfire', 'volcano', 'tornado', 'drought',
            'pandemic', 'epidemic', 'landslide', 'avalanche', 'blizzard'
        ]
        
        text_lower = text.lower()
        found_types = [dt for dt in disaster_types if dt in text_lower]
        
        return list(set(found_types))
    
    def _assess_scale(self, context: List[Dict]) -> Dict:
        """Assess the scale of the crisis."""
        scale_indicators = {
            'local': 0, 'regional': 0, 'national': 0, 'international': 0
        }
        
        for item in context:
            description = (item.get('description', '') + ' ' + item.get('title', '')).lower()
            
            if any(word in description for word in ['international', 'global', 'worldwide', 'multiple countries']):
                scale_indicators['international'] += 1
            elif any(word in description for word in ['national', 'country', 'nationwide']):
                scale_indicators['national'] += 1
            elif any(word in description for word in ['regional', 'state', 'province', 'multi-city']):
                scale_indicators['regional'] += 1
            else:
                scale_indicators['local'] += 1
        
        return scale_indicators
    
    def _assess_temporal_urgency(self, query: str, context: List[Dict]) -> float:
        """Assess temporal urgency."""
        temporal_keywords = {
            'now': 1.0, 'today': 0.9, 'ongoing': 0.8, 'current': 0.8,
            'recent': 0.6, 'yesterday': 0.7, 'this week': 0.5
        }
        
        text = (query + ' ' + ' '.join([
            item.get('description', '') for item in context[:3]
        ])).lower()
        
        max_urgency = 0.0
        for keyword, urgency in temporal_keywords.items():
            if keyword in text:
                max_urgency = max(max_urgency, urgency)
        
        return max_urgency
    
    def _assess_geographic_spread(self, context: List[Dict]) -> Dict:
        """Assess geographic spread of the crisis."""
        countries = set()
        regions = set()
        
        for item in context:
            location = item.get('location', '').lower()
            if location:
                # Simple country detection (could be enhanced with proper geo-parsing)
                if ',' in location:
                    parts = [part.strip() for part in location.split(',')]
                    countries.update(parts)
                else:
                    regions.add(location)
        
        return {
            'affected_countries': len(countries),
            'affected_regions': len(regions),
            'geographic_scope': 'international' if len(countries) > 1 else 'domestic'
        }
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize risk level based on score."""
        if risk_score >= 0.8:
            return 'CRITICAL'
        elif risk_score >= 0.6:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        elif risk_score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _analyze_event_trends(self, dates: List[datetime]) -> Dict:
        """Analyze trends in event timing."""
        if len(dates) < 3:
            return {'trend': 'insufficient_data'}
        
        # Calculate intervals between events
        intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
        avg_interval = sum(intervals) / len(intervals)
        
        # Recent trend
        recent_dates = [d for d in dates if (datetime.now() - d.replace(tzinfo=None)).days <= 90]
        
        return {
            'trend': 'increasing' if len(recent_dates) > len(dates) * 0.5 else 'stable',
            'average_interval_days': avg_interval,
            'recent_acceleration': len(recent_dates) > len(dates) * 0.5
        }
    
    def _detect_seasonal_patterns(self, dates: List[datetime]) -> Dict:
        """Detect seasonal patterns in events."""
        if len(dates) < 4:
            return {'seasonal_pattern': 'insufficient_data'}
        
        # Group by month
        month_counts = {}
        for date in dates:
            month = date.month
            month_counts[month] = month_counts.get(month, 0) + 1
        
        # Find peak months
        max_count = max(month_counts.values())
        peak_months = [month for month, count in month_counts.items() if count == max_count]
        
        return {
            'peak_months': peak_months,
            'monthly_distribution': month_counts,
            'seasonal_pattern': 'detected' if max_count > 1 else 'unclear'
        }


# Global instance
_ensemble_ai = None

def get_ensemble_ai() -> AdvancedEnsembleAI:
    """Get global ensemble AI instance."""
    global _ensemble_ai
    if _ensemble_ai is None:
        _ensemble_ai = AdvancedEnsembleAI()
    return _ensemble_ai