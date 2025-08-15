"""
Real-Time Crisis Intelligence & Predictive Analytics System.

This module provides advanced real-time monitoring, trend analysis,
and predictive capabilities for crisis detection and forecasting.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import websockets
import json
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
import feedparser
import tweepy
from textblob import TextBlob

logger = logging.getLogger(__name__)


@dataclass
class CrisisPrediction:
    """Crisis prediction result."""
    region: str
    crisis_type: str
    probability: float
    confidence_level: float
    predicted_date: datetime
    severity_score: float
    risk_factors: List[str]
    historical_patterns: Dict[str, Any]
    early_warning_indicators: List[str]
    recommended_actions: List[str]


@dataclass
class RealTimeAlert:
    """Real-time crisis alert."""
    alert_id: str
    timestamp: datetime
    crisis_type: str
    location: str
    severity: str
    confidence: float
    source: str
    description: str
    coordinates: Optional[Tuple[float, float]]
    affected_population: Optional[int]
    keywords: List[str]
    urgency_level: int  # 1-10 scale


@dataclass
class TrendAnalysis:
    """Crisis trend analysis result."""
    trend_type: str
    direction: str  # increasing, decreasing, stable
    strength: float  # 0-1
    time_period: str
    key_indicators: List[str]
    statistical_significance: float
    forecast_horizon: int  # days
    confidence_intervals: Dict[str, float]


class RealTimeCrisisIntelligence:
    """
    Advanced real-time crisis intelligence system with predictive capabilities.
    """
    
    def __init__(self):
        """Initialize the real-time intelligence system."""
        self.prediction_models = {}
        self.scalers = {}
        self.alert_threshold = 0.7
        self.monitoring_active = False
        self.data_sources = {}
        self.websocket_connections = set()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._initialize_models()
        self._setup_data_sources()
    
    def _initialize_models(self):
        """Initialize predictive models for different crisis types."""
        logger.info("🤖 Initializing Real-Time Intelligence Models...")
        
        crisis_types = [
            'earthquake', 'flood', 'hurricane', 'wildfire', 
            'pandemic', 'drought', 'volcano', 'tsunami'
        ]
        
        for crisis_type in crisis_types:
            try:
                # Random Forest for probability prediction
                self.prediction_models[f'{crisis_type}_probability'] = RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    n_jobs=-1
                )
                
                # Isolation Forest for anomaly detection
                self.prediction_models[f'{crisis_type}_anomaly'] = IsolationForest(
                    contamination=0.1,
                    random_state=42,
                    n_jobs=-1
                )
                
                # Scaler for feature normalization
                self.scalers[crisis_type] = StandardScaler()
                
                logger.info(f"✅ Initialized models for {crisis_type}")
                
            except Exception as e:
                logger.error(f"❌ Error initializing {crisis_type} models: {e}")
    
    def _setup_data_sources(self):
        """Setup real-time data sources."""
        logger.info("🌐 Setting up real-time data sources...")
        
        # News RSS feeds
        self.data_sources['news_feeds'] = [
            'https://feeds.reuters.com/reuters/worldNews',
            'https://feeds.bbci.co.uk/news/world/rss.xml',
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.npr.org/1001/rss.xml'
        ]
        
        # Weather APIs
        self.data_sources['weather_apis'] = [
            'https://api.openweathermap.org/data/2.5/weather',
            'https://api.weatherbit.io/v2.0/current',
            'https://api.tomorrow.io/v4/weather/realtime'
        ]
        
        # Geological data
        self.data_sources['geological'] = [
            'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson',
            'https://volcano.si.edu/news/WeeklyVolcanoRSS.xml'
        ]
        
        # Social media monitoring
        self.data_sources['social_monitoring'] = {
            'keywords': [
                'earthquake', 'tsunami', 'hurricane', 'wildfire', 'flood',
                'emergency', 'disaster', 'crisis', 'evacuation', 'breaking'
            ],
            'languages': ['en', 'es', 'fr', 'pt', 'ar', 'zh'],
            'sentiment_threshold': -0.5
        }
        
        logger.info("✅ Data sources configured")
    
    async def start_monitoring(self):
        """Start real-time crisis monitoring."""
        if self.monitoring_active:
            logger.warning("⚠️ Monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info("🚀 Starting real-time crisis monitoring...")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_news_feeds()),
            asyncio.create_task(self._monitor_geological_data()),
            asyncio.create_task(self._monitor_weather_patterns()),
            asyncio.create_task(self._monitor_social_media()),
            asyncio.create_task(self._generate_predictions()),
            asyncio.create_task(self._websocket_server()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
        finally:
            self.monitoring_active = False
    
    async def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        logger.info("🛑 Stopping real-time monitoring...")
    
    async def _monitor_news_feeds(self):
        """Monitor news RSS feeds for crisis-related content."""
        logger.info("📰 Starting news feed monitoring...")
        
        while self.monitoring_active:
            try:
                for feed_url in self.data_sources['news_feeds']:
                    try:
                        feed = feedparser.parse(feed_url)
                        
                        for entry in feed.entries[:10]:  # Latest 10 entries
                            alert = await self._analyze_news_entry(entry)
                            if alert:
                                await self._process_alert(alert)
                        
                    except Exception as e:
                        logger.error(f"Error processing feed {feed_url}: {e}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"News monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_geological_data(self):
        """Monitor geological data sources."""
        logger.info("🌍 Starting geological monitoring...")
        
        while self.monitoring_active:
            try:
                # Monitor USGS earthquake data
                response = requests.get(
                    self.data_sources['geological'][0],
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for feature in data.get('features', []):
                        alert = await self._analyze_earthquake_data(feature)
                        if alert:
                            await self._process_alert(alert)
                
                # Monitor volcano data
                volcano_feed = feedparser.parse(
                    self.data_sources['geological'][1]
                )
                
                for entry in volcano_feed.entries[:5]:
                    alert = await self._analyze_volcano_data(entry)
                    if alert:
                        await self._process_alert(alert)
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except Exception as e:
                logger.error(f"Geological monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_weather_patterns(self):
        """Monitor weather patterns for extreme events."""
        logger.info("🌦️ Starting weather pattern monitoring...")
        
        while self.monitoring_active:
            try:
                # Monitor major cities for extreme weather
                major_cities = [
                    {'name': 'New York', 'lat': 40.7128, 'lon': -74.0060},
                    {'name': 'London', 'lat': 51.5074, 'lon': -0.1278},
                    {'name': 'Tokyo', 'lat': 35.6762, 'lon': 139.6503},
                    {'name': 'Mumbai', 'lat': 19.0760, 'lon': 72.8777},
                    {'name': 'São Paulo', 'lat': -23.5505, 'lon': -46.6333}
                ]
                
                for city in major_cities:
                    alert = await self._analyze_weather_data(city)
                    if alert:
                        await self._process_alert(alert)
                
                await asyncio.sleep(1800)  # Check every 30 minutes
                
            except Exception as e:
                logger.error(f"Weather monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _monitor_social_media(self):
        """Monitor social media for crisis indicators."""
        logger.info("📱 Starting social media monitoring...")
        
        while self.monitoring_active:
            try:
                # Simulate social media monitoring
                # In production, integrate with Twitter API, Reddit API, etc.
                alerts = await self._analyze_social_sentiment()
                
                for alert in alerts:
                    await self._process_alert(alert)
                
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                logger.error(f"Social media monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _generate_predictions(self):
        """Generate crisis predictions using ML models."""
        logger.info("🔮 Starting predictive analysis...")
        
        while self.monitoring_active:
            try:
                # Generate predictions for each region and crisis type
                regions = [
                    'North America', 'South America', 'Europe', 'Asia', 
                    'Africa', 'Oceania', 'Middle East'
                ]
                
                crisis_types = [
                    'earthquake', 'flood', 'hurricane', 'wildfire',
                    'pandemic', 'drought', 'volcano'
                ]
                
                predictions = []
                
                for region in regions:
                    for crisis_type in crisis_types:
                        prediction = await self._predict_crisis_probability(
                            region, crisis_type
                        )
                        
                        if prediction.probability > 0.3:  # Only high-probability predictions
                            predictions.append(prediction)
                
                # Broadcast predictions
                await self._broadcast_predictions(predictions)
                
                await asyncio.sleep(3600)  # Generate predictions every hour
                
            except Exception as e:
                logger.error(f"Prediction generation error: {e}")
                await asyncio.sleep(600)
    
    async def _websocket_server(self):
        """WebSocket server for real-time updates."""
        logger.info("🔌 Starting WebSocket server...")
        
        async def handle_client(websocket, path):
            """Handle WebSocket client connection."""
            self.websocket_connections.add(websocket)
            logger.info(f"📡 New WebSocket client connected: {websocket.remote_address}")
            
            try:
                await websocket.wait_closed()
            finally:
                self.websocket_connections.discard(websocket)
                logger.info(f"📡 WebSocket client disconnected: {websocket.remote_address}")
        
        # Start WebSocket server
        server = await websockets.serve(
            handle_client,
            "localhost",
            8765,
            ping_interval=30,
            ping_timeout=60
        )
        
        logger.info("✅ WebSocket server started on ws://localhost:8765")
        
        # Keep server running while monitoring is active
        while self.monitoring_active:
            await asyncio.sleep(1)
        
        server.close()
        await server.wait_closed()
    
    async def _analyze_news_entry(self, entry) -> Optional[RealTimeAlert]:
        """Analyze news entry for crisis indicators."""
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            content = f"{title} {description}".lower()
            
            # Crisis keywords
            crisis_keywords = {
                'earthquake': ['earthquake', 'seismic', 'tremor', 'magnitude'],
                'hurricane': ['hurricane', 'typhoon', 'cyclone', 'storm'],
                'flood': ['flood', 'flooding', 'inundation', 'overflow'],
                'wildfire': ['wildfire', 'forest fire', 'bushfire', 'flames'],
                'pandemic': ['pandemic', 'epidemic', 'outbreak', 'virus'],
                'volcano': ['volcano', 'volcanic', 'eruption', 'lava'],
                'tsunami': ['tsunami', 'tidal wave', 'sea surge']
            }
            
            # Check for crisis indicators
            detected_crises = []
            for crisis_type, keywords in crisis_keywords.items():
                if any(keyword in content for keyword in keywords):
                    detected_crises.append(crisis_type)
            
            if not detected_crises:
                return None
            
            # Analyze sentiment and urgency
            blob = TextBlob(content)
            sentiment = blob.sentiment.polarity
            
            # Extract location (simplified)
            location = self._extract_location_from_text(content)
            
            # Calculate severity based on keywords
            severity_keywords = ['catastrophic', 'devastating', 'major', 'severe', 'massive']
            severity_score = sum(1 for keyword in severity_keywords if keyword in content)
            severity = 'HIGH' if severity_score >= 2 else 'MEDIUM' if severity_score >= 1 else 'LOW'
            
            # Create alert
            alert = RealTimeAlert(
                alert_id=f"news_{int(time.time())}",
                timestamp=datetime.now(),
                crisis_type=detected_crises[0],  # Primary crisis type
                location=location,
                severity=severity,
                confidence=min(0.6 + (severity_score * 0.1), 0.9),
                source=f"News: {entry.get('link', 'Unknown')}",
                description=description[:200],
                coordinates=None,  # Could be enhanced with geocoding
                affected_population=None,
                keywords=detected_crises,
                urgency_level=min(severity_score + 3, 10)
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error analyzing news entry: {e}")
            return None
    
    async def _analyze_earthquake_data(self, feature) -> Optional[RealTimeAlert]:
        """Analyze earthquake data from USGS."""
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            magnitude = properties.get('mag', 0)
            place = properties.get('place', 'Unknown location')
            time_ms = properties.get('time', 0)
            coordinates = geometry.get('coordinates', [0, 0, 0])
            
            # Only alert for significant earthquakes
            if magnitude < 4.0:
                return None
            
            # Calculate severity
            if magnitude >= 7.0:
                severity = 'HIGH'
                urgency = 9
            elif magnitude >= 6.0:
                severity = 'MEDIUM'
                urgency = 7
            else:
                severity = 'LOW'
                urgency = 5
            
            alert = RealTimeAlert(
                alert_id=f"earthquake_{properties.get('id', int(time.time()))}",
                timestamp=datetime.fromtimestamp(time_ms / 1000),
                crisis_type='earthquake',
                location=place,
                severity=severity,
                confidence=0.95,  # USGS data is highly reliable
                source='USGS Earthquake Hazards Program',
                description=f"Magnitude {magnitude} earthquake near {place}",
                coordinates=(coordinates[1], coordinates[0]) if len(coordinates) >= 2 else None,
                affected_population=None,
                keywords=[f'magnitude_{magnitude}', 'earthquake'],
                urgency_level=urgency
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error analyzing earthquake data: {e}")
            return None
    
    async def _analyze_volcano_data(self, entry) -> Optional[RealTimeAlert]:
        """Analyze volcano data from Smithsonian."""
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            
            # Check for volcanic activity keywords
            activity_keywords = ['eruption', 'volcanic', 'lava', 'ash', 'explosion']
            if not any(keyword in title.lower() for keyword in activity_keywords):
                return None
            
            # Extract volcano name and location
            volcano_name = title.split('-')[0].strip() if '-' in title else title
            
            alert = RealTimeAlert(
                alert_id=f"volcano_{int(time.time())}",
                timestamp=datetime.now(),
                crisis_type='volcano',
                location=volcano_name,
                severity='MEDIUM',
                confidence=0.8,
                source='Smithsonian Global Volcanism Program',
                description=description[:200],
                coordinates=None,
                affected_population=None,
                keywords=['volcano', 'eruption'],
                urgency_level=6
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error analyzing volcano data: {e}")
            return None
    
    async def _analyze_weather_data(self, city) -> Optional[RealTimeAlert]:
        """Analyze weather data for extreme conditions."""
        try:
            # Simulate weather API call (replace with actual API)
            # This would normally call OpenWeatherMap, WeatherAPI, etc.
            
            # For demonstration, generate some random extreme weather scenarios
            import random
            
            if random.random() > 0.95:  # 5% chance of extreme weather
                weather_types = [
                    ('hurricane', 'HIGH', 9),
                    ('tornado', 'HIGH', 8),
                    ('severe_storm', 'MEDIUM', 6),
                    ('extreme_heat', 'MEDIUM', 5),
                    ('blizzard', 'HIGH', 7)
                ]
                
                weather_type, severity, urgency = random.choice(weather_types)
                
                alert = RealTimeAlert(
                    alert_id=f"weather_{int(time.time())}",
                    timestamp=datetime.now(),
                    crisis_type=weather_type,
                    location=city['name'],
                    severity=severity,
                    confidence=0.7,
                    source='Weather Monitoring System',
                    description=f"Extreme {weather_type} conditions detected in {city['name']}",
                    coordinates=(city['lat'], city['lon']),
                    affected_population=None,
                    keywords=[weather_type, 'extreme_weather'],
                    urgency_level=urgency
                )
                
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing weather data: {e}")
            return None
    
    async def _analyze_social_sentiment(self) -> List[RealTimeAlert]:
        """Analyze social media sentiment for crisis indicators."""
        try:
            # Simulate social media analysis
            # In production, integrate with Twitter API, Reddit API, etc.
            
            alerts = []
            
            # Simulate detecting crisis-related social media activity
            import random
            
            if random.random() > 0.9:  # 10% chance of social alert
                crisis_types = ['earthquake', 'flood', 'wildfire', 'hurricane']
                locations = ['California', 'Florida', 'Texas', 'New York', 'Japan']
                
                crisis_type = random.choice(crisis_types)
                location = random.choice(locations)
                
                alert = RealTimeAlert(
                    alert_id=f"social_{int(time.time())}",
                    timestamp=datetime.now(),
                    crisis_type=crisis_type,
                    location=location,
                    severity='MEDIUM',
                    confidence=0.6,
                    source='Social Media Monitoring',
                    description=f"Increased social media activity about {crisis_type} in {location}",
                    coordinates=None,
                    affected_population=None,
                    keywords=[crisis_type, 'social_media'],
                    urgency_level=5
                )
                
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing social sentiment: {e}")
            return []
    
    async def _predict_crisis_probability(
        self, 
        region: str, 
        crisis_type: str
    ) -> CrisisPrediction:
        """Predict crisis probability for a region and type."""
        try:
            # Generate synthetic features for prediction
            # In production, use real historical data, weather patterns, etc.
            
            features = self._generate_prediction_features(region, crisis_type)
            
            # Use trained model to predict probability
            model_name = f'{crisis_type}_probability'
            if model_name in self.prediction_models:
                # For demonstration, use random probability
                # In production, use: probability = model.predict([features])[0]
                import random
                base_probability = random.random() * 0.8
                
                # Adjust based on recent activity
                if crisis_type == 'earthquake' and region in ['Asia', 'North America']:
                    base_probability += 0.1
                elif crisis_type == 'hurricane' and region in ['North America', 'Asia']:
                    base_probability += 0.15
                
                probability = min(base_probability, 1.0)
            else:
                probability = 0.1
            
            # Generate risk factors and recommendations
            risk_factors = self._generate_risk_factors(region, crisis_type)
            recommendations = self._generate_recommendations(crisis_type, probability)
            
            prediction = CrisisPrediction(
                region=region,
                crisis_type=crisis_type,
                probability=probability,
                confidence_level=0.75,
                predicted_date=datetime.now() + timedelta(days=random.randint(1, 30)),
                severity_score=probability * 10,
                risk_factors=risk_factors,
                historical_patterns={'trend': 'increasing', 'frequency': 'above_average'},
                early_warning_indicators=[],
                recommended_actions=recommendations
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting crisis probability: {e}")
            return CrisisPrediction(
                region=region,
                crisis_type=crisis_type,
                probability=0.0,
                confidence_level=0.0,
                predicted_date=datetime.now(),
                severity_score=0.0,
                risk_factors=[],
                historical_patterns={},
                early_warning_indicators=[],
                recommended_actions=[]
            )
    
    def _generate_prediction_features(self, region: str, crisis_type: str) -> List[float]:
        """Generate features for ML prediction."""
        # This would normally use real data: weather patterns, geological indicators,
        # historical frequency, population density, infrastructure vulnerability, etc.
        
        import random
        return [random.random() for _ in range(20)]  # 20 features
    
    def _generate_risk_factors(self, region: str, crisis_type: str) -> List[str]:
        """Generate risk factors for a crisis prediction."""
        risk_factor_map = {
            'earthquake': ['tectonic activity', 'fault lines', 'seismic history'],
            'hurricane': ['sea surface temperature', 'wind patterns', 'seasonal factors'],
            'flood': ['rainfall patterns', 'river levels', 'urban drainage'],
            'wildfire': ['drought conditions', 'vegetation dryness', 'wind patterns'],
            'volcano': ['seismic activity', 'gas emissions', 'ground deformation'],
            'pandemic': ['population density', 'travel patterns', 'health infrastructure'],
            'drought': ['precipitation patterns', 'soil moisture', 'temperature trends']
        }
        
        return risk_factor_map.get(crisis_type, ['general risk factors'])
    
    def _generate_recommendations(self, crisis_type: str, probability: float) -> List[str]:
        """Generate recommendations based on crisis type and probability."""
        base_recommendations = {
            'earthquake': [
                'Review emergency evacuation plans',
                'Check structural integrity of buildings',
                'Prepare emergency supply kits'
            ],
            'hurricane': [
                'Monitor weather forecasts closely',
                'Secure outdoor objects',
                'Review evacuation routes'
            ],
            'flood': [
                'Monitor water levels',
                'Check drainage systems',
                'Prepare sandbags if necessary'
            ],
            'wildfire': [
                'Create defensible space around properties',
                'Monitor fire weather conditions',
                'Prepare evacuation plans'
            ]
        }
        
        recommendations = base_recommendations.get(crisis_type, ['Monitor situation closely'])
        
        if probability > 0.7:
            recommendations.append('Consider immediate preventive measures')
            recommendations.append('Alert relevant authorities')
        
        return recommendations
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extract location from text (simplified)."""
        # This could be enhanced with proper NER and geocoding
        common_locations = [
            'California', 'Florida', 'Texas', 'New York', 'Japan', 'China',
            'India', 'Brazil', 'Mexico', 'Indonesia', 'Philippines', 'Turkey'
        ]
        
        text_lower = text.lower()
        for location in common_locations:
            if location.lower() in text_lower:
                return location
        
        return 'Unknown location'
    
    async def _process_alert(self, alert: RealTimeAlert):
        """Process and broadcast a real-time alert."""
        try:
            logger.info(f"🚨 Processing alert: {alert.crisis_type} in {alert.location}")
            
            # Convert alert to JSON for broadcasting
            alert_data = {
                'type': 'alert',
                'data': asdict(alert),
                'timestamp': alert.timestamp.isoformat()
            }
            
            # Broadcast to WebSocket clients
            await self._broadcast_to_websockets(alert_data)
            
            # Store alert in database (implement as needed)
            # await self._store_alert(alert)
            
            # Trigger additional actions based on severity
            if alert.severity == 'HIGH':
                await self._handle_high_severity_alert(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    async def _broadcast_predictions(self, predictions: List[CrisisPrediction]):
        """Broadcast predictions to connected clients."""
        try:
            if not predictions:
                return
            
            prediction_data = {
                'type': 'predictions',
                'data': [asdict(pred) for pred in predictions],
                'timestamp': datetime.now().isoformat()
            }
            
            await self._broadcast_to_websockets(prediction_data)
            
        except Exception as e:
            logger.error(f"Error broadcasting predictions: {e}")
    
    async def _broadcast_to_websockets(self, data: Dict):
        """Broadcast data to all connected WebSocket clients."""
        if not self.websocket_connections:
            return
        
        message = json.dumps(data, default=str)
        
        # Send to all connected clients
        disconnected = set()
        for websocket in self.websocket_connections.copy():
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error sending to WebSocket client: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        self.websocket_connections -= disconnected
    
    async def _handle_high_severity_alert(self, alert: RealTimeAlert):
        """Handle high-severity alerts with additional actions."""
        try:
            logger.warning(f"🚨 HIGH SEVERITY ALERT: {alert.crisis_type} in {alert.location}")
            
            # Send email notifications (implement as needed)
            # await self._send_email_notification(alert)
            
            # Trigger SMS alerts (implement as needed)
            # await self._send_sms_alerts(alert)
            
            # Update emergency services APIs (implement as needed)
            # await self._notify_emergency_services(alert)
            
        except Exception as e:
            logger.error(f"Error handling high severity alert: {e}")
    
    async def generate_trend_analysis(
        self, 
        crisis_type: str, 
        time_period: str = '30d'
    ) -> TrendAnalysis:
        """Generate trend analysis for a specific crisis type."""
        try:
            # In production, this would analyze historical data from the database
            
            # Simulate trend analysis
            import random
            
            directions = ['increasing', 'decreasing', 'stable']
            direction = random.choice(directions)
            
            strength = random.random()
            
            key_indicators = [
                f'{crisis_type}_frequency_change',
                f'{crisis_type}_severity_trend',
                f'{crisis_type}_geographical_spread'
            ]
            
            analysis = TrendAnalysis(
                trend_type=crisis_type,
                direction=direction,
                strength=strength,
                time_period=time_period,
                key_indicators=key_indicators,
                statistical_significance=0.95 if strength > 0.7 else 0.75,
                forecast_horizon=30,
                confidence_intervals={'lower': 0.1, 'upper': 0.9}
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error generating trend analysis: {e}")
            return TrendAnalysis(
                trend_type=crisis_type,
                direction='unknown',
                strength=0.0,
                time_period=time_period,
                key_indicators=[],
                statistical_significance=0.0,
                forecast_horizon=0,
                confidence_intervals={}
            )
    
    def generate_crisis_dashboard_data(self) -> Dict[str, Any]:
        """Generate comprehensive dashboard data."""
        try:
            # This would normally aggregate real data from the database
            dashboard_data = {
                'summary': {
                    'active_alerts': len(self.websocket_connections),
                    'total_predictions': 15,
                    'high_risk_regions': 3,
                    'monitoring_status': 'active' if self.monitoring_active else 'inactive'
                },
                'recent_alerts': [
                    # Would be populated with recent alerts
                ],
                'risk_levels': {
                    'critical': 2,
                    'high': 5,
                    'medium': 8,
                    'low': 12
                },
                'geographic_distribution': {
                    'North America': 8,
                    'Europe': 5,
                    'Asia': 12,
                    'Africa': 4,
                    'South America': 3,
                    'Oceania': 1
                },
                'crisis_types': {
                    'earthquake': 15,
                    'flood': 12,
                    'hurricane': 8,
                    'wildfire': 6,
                    'volcano': 3,
                    'pandemic': 2
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {}
    
    def create_interactive_visualizations(self) -> Dict[str, str]:
        """Create interactive visualizations for the dashboard."""
        try:
            # Crisis distribution pie chart
            crisis_data = {
                'earthquake': 15, 'flood': 12, 'hurricane': 8,
                'wildfire': 6, 'volcano': 3, 'pandemic': 2
            }
            
            fig_pie = px.pie(
                values=list(crisis_data.values()),
                names=list(crisis_data.keys()),
                title='Crisis Distribution by Type'
            )
            
            # Risk level timeline
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
            risk_levels = np.random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], size=len(dates))
            
            fig_timeline = px.line(
                x=dates,
                y=[{'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}[level] for level in risk_levels],
                title='Risk Level Timeline'
            )
            
            # Geographic heatmap (simplified)
            fig_map = px.scatter_geo(
                lat=[40.7128, 51.5074, 35.6762, 19.0760],
                lon=[-74.0060, -0.1278, 139.6503, 72.8777],
                size=[10, 8, 12, 6],
                color=[3, 2, 4, 2],
                hover_name=['New York', 'London', 'Tokyo', 'Mumbai'],
                title='Global Crisis Activity'
            )
            
            # Convert to JSON for web display
            visualizations = {
                'crisis_distribution': fig_pie.to_json(),
                'risk_timeline': fig_timeline.to_json(),
                'global_map': fig_map.to_json()
            }
            
            return visualizations
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            return {}


# Global instance
_intelligence_system = None

def get_intelligence_system() -> RealTimeCrisisIntelligence:
    """Get global intelligence system instance."""
    global _intelligence_system
    if _intelligence_system is None:
        _intelligence_system = RealTimeCrisisIntelligence()
    return _intelligence_system