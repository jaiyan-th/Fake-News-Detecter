# 📰 Fake News Detector - Card Grid UI

A modern, Pinterest-like card grid interface for fake news detection powered by machine learning. This application transforms news article analysis into an engaging, visual browsing experience with responsive design and advanced user interactions.

## ✨ Features

### 🎨 Pinterest-Style Interface
- **Masonry Grid Layout**: Responsive card grid that adapts to different screen sizes
- **Interactive Cards**: Hover effects, click interactions, and smooth animations
- **Infinite Scroll**: Seamless loading of more content as you browse
- **Virtual Scrolling**: Optimized performance for large datasets

### 🔍 Advanced Search & Filtering
- **Real-time Search**: Find articles by content or author
- **Smart Filtering**: Filter by prediction type (Real/Fake) and confidence levels
- **Sorting Options**: Sort by date, confidence, or author
- **Debounced Input**: Optimized search performance

### 📱 Responsive Design
- **Mobile-First**: Optimized for all device sizes
- **Adaptive Columns**: 1-5 columns based on screen width
- **Touch-Friendly**: Optimized interactions for mobile devices
- **Accessibility**: Full keyboard navigation and screen reader support

### 🚀 Performance Optimizations
- **Lazy Loading**: Images load only when visible
- **Caching**: Browser storage for improved performance
- **Intersection Observer**: Efficient scroll detection
- **CSS Grid**: Hardware-accelerated layout

### 🎯 AI-Powered Analysis
- **Machine Learning**: Trained model for fake news detection
- **Confidence Scores**: Visual confidence indicators
- **Batch Processing**: Analyze multiple articles efficiently
- **Real-time Predictions**: Instant analysis results

## 🛠️ Technology Stack

### Frontend
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern grid layout with custom properties
- **Vanilla JavaScript**: No framework dependencies
- **Web APIs**: Intersection Observer, Fetch, Local Storage

### Backend
- **Flask**: Python web framework
- **MongoDB**: Document database for article storage
- **scikit-learn**: Machine learning for text classification
- **NLTK**: Natural language processing

### Infrastructure
- **Docker**: Containerization support
- **CORS**: Cross-origin resource sharing
- **RESTful API**: Clean API design

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB
- Modern web browser

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fake_news_detector_fullstack
   ```

2. **Start the application**
   ```bash
   python start_server.py
   ```

   This script will:
   - Check system requirements
   - Install Python dependencies
   - Verify MongoDB connection
   - Run data migration
   - Start the development server

3. **Open your browser**
   Navigate to `http://localhost:5000`

### Manual Setup

If you prefer manual setup:

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MongoDB**
   ```bash
   # Windows
   net start MongoDB
   
   # macOS
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```

3. **Train the model** (if not already done)
   ```bash
   cd training
   python train_model.py
   ```

4. **Run migration**
   ```bash
   cd training/backend
   python migrate_data.py
   ```

5. **Start the server**
   ```bash
   cd training/backend
   python app.py
   ```

## 📖 Usage Guide

### Adding Articles
1. Click the "Add News" button in the header
2. Paste or type your news article text
3. Click "Analyze Article"
4. View the results in the card grid

### Browsing Articles
- **Scroll** to load more articles automatically
- **Click cards** to view detailed analysis
- **Use search** to find specific articles
- **Apply filters** to narrow down results

### Keyboard Shortcuts
- `Ctrl/Cmd + K`: Focus search input
- `Ctrl/Cmd + N`: Add new article
- `Ctrl/Cmd + L`: Toggle layout
- `Arrow Keys`: Navigate between cards
- `Enter/Space`: Open card details
- `Escape`: Close modals

### Mobile Usage
- **Tap cards** to view details
- **Pull to refresh** (if implemented)
- **Swipe gestures** in modals
- **Touch-optimized** interface

## 🏗️ Architecture

### Component Structure
```
├── CardGrid (Main container)
│   ├── CardColumn (Responsive columns)
│   │   └── NewsCard (Individual cards)
│   │       ├── CardImage
│   │       ├── CardContent
│   │       ├── CardMetadata
│   │       └── CardActions
│   └── InfiniteScrollLoader
└── CardModal (Detailed view)
```

### API Endpoints
- `GET /api/cards` - Paginated article list
- `POST /api/predict` - Analyze new article
- `GET /api/cards/:id` - Article details
- `GET /api/cards/search` - Search articles
- `GET /api/cards/stats` - Statistics

### Data Flow
1. User submits article text
2. Backend processes with ML model
3. Prediction stored in MongoDB
4. Frontend updates card grid
5. Real-time statistics update

## 🎨 Customization

### Layout Options
- **Compact**: Smaller cards, tighter spacing
- **Normal**: Default balanced layout
- **Spacious**: Larger cards, more spacing

### Responsive Breakpoints
- **Mobile**: < 768px (1 column)
- **Tablet**: 768px - 1023px (2 columns)
- **Desktop**: 1024px - 1199px (3 columns)
- **Large**: 1200px - 1399px (4 columns)
- **XL**: 1400px+ (5 columns)

### Color Themes
- **Real News**: Green (#10b981)
- **Fake News**: Red (#ef4444)
- **Neutral**: Blue (#3b82f6)

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=development
FLASK_DEBUG=1
MONGODB_URI=mongodb://localhost:27017/fake_news_app
```

### CSS Custom Properties
```css
:root {
  --card-width: 300px;
  --gap: 20px;
  --columns: 3;
  --border-radius: 12px;
}
```

## 🧪 Testing

### Manual Testing
1. Add various types of articles
2. Test responsive behavior
3. Verify search functionality
4. Check accessibility features

### Browser Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🚀 Deployment

### Production Setup
1. Set environment to production
2. Configure MongoDB Atlas
3. Use Gunicorn for WSGI
4. Set up reverse proxy (Nginx)
5. Enable HTTPS

### Docker Deployment
```bash
docker-compose up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- scikit-learn for machine learning capabilities
- Flask for the web framework
- MongoDB for data storage
- The open-source community for inspiration

## 📞 Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with details
4. Include browser and system information

---

**Built with ❤️ for better news verification**
