# 🚀 Complete Setup Guide: Frontend + Backend + MongoDB

This guide will help you connect all components of the Fake News Detector Card Grid system.

## 📋 Prerequisites

### Required Software
- **Python 3.8+** - For the backend Flask application
- **MongoDB** - Database for storing predictions and user data
- **Modern Web Browser** - Chrome, Firefox, Safari, or Edge
- **Git** (optional) - For version control

### System Requirements
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: At least 2GB free space
- **Network**: Internet connection for package downloads

## 🛠️ Step-by-Step Setup

### Step 1: Install MongoDB

#### Windows:
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. Start MongoDB service:
   ```cmd
   net start MongoDB
   ```

#### macOS:
```bash
# Install using Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Linux (Ubuntu/Debian):
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

### Step 2: Verify MongoDB Installation

```bash
# Check if MongoDB is running
mongosh --eval "db.adminCommand('ismaster')"
```

You should see output indicating MongoDB is running successfully.

### Step 3: Install Python Dependencies

```bash
# Navigate to project directory
cd fake_news_detector_fullstack

# Install required packages
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables (Optional)

Create a `.env` file in the project root:

```bash
# .env file
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here
MONGODB_URI=mongodb://localhost:27017/fake_news_app
PORT=5000
```

### Step 5: Train the Machine Learning Model

```bash
# Navigate to training directory
cd training

# Train the model (this may take a few minutes)
python train_model.py
```

### Step 6: Run Database Migration

```bash
# Navigate to backend directory
cd training/backend

# Run migration script
python migrate_data.py
```

### Step 7: Start the Application

#### Option A: Use the Automated Startup Script (Recommended)
```bash
# From project root directory
python start_server.py
```

#### Option B: Manual Startup
```bash
# Navigate to backend directory
cd training/backend

# Start Flask server
python app.py
```

### Step 8: Access the Application

1. Open your web browser
2. Navigate to: `http://localhost:5000`
3. You should see the Pinterest-like card grid interface

## 🔧 Configuration Options

### MongoDB Configuration

#### Custom MongoDB URI
If using a different MongoDB setup:

```python
# In training/backend/app.py
app.config["MONGO_URI"] = "mongodb://username:password@host:port/database"
```

#### MongoDB Atlas (Cloud)
For cloud MongoDB:

```python
app.config["MONGO_URI"] = "mongodb+srv://username:password@cluster.mongodb.net/fake_news_app"
```

### Backend Configuration

#### Change Port
```python
# In training/backend/app.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)  # Change port to 8000
```

#### Enable CORS for Different Origins
```python
# In training/backend/app.py
CORS(app, origins=["http://localhost:3000", "http://your-domain.com"])
```

### Frontend Configuration

#### Update API Base URL
```javascript
// In training/frontend/script.js
const API_BASE = 'http://localhost:8000/api';  // Change if backend port differs
```

## 🧪 Testing the Connection

### 1. Test Database Connection
```bash
# From backend directory
python -c "
from app import mongo
try:
    mongo.db.command('ping')
    print('✅ MongoDB connection successful')
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
"
```

### 2. Test API Endpoints
```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test prediction endpoint
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test news article about technology."}'
```

### 3. Test Frontend Integration
1. Open browser developer tools (F12)
2. Go to Network tab
3. Refresh the page
4. Check for successful API calls to `/api/cards` and `/api/stats`

## 🐛 Troubleshooting

### Common Issues and Solutions

#### MongoDB Connection Error
```
Error: MongoServerError: Authentication failed
```
**Solution**: Check MongoDB credentials and ensure the service is running
```bash
# Restart MongoDB service
# Windows:
net stop MongoDB && net start MongoDB

# macOS:
brew services restart mongodb-community

# Linux:
sudo systemctl restart mongod
```

#### Port Already in Use
```
Error: [Errno 48] Address already in use
```
**Solution**: Change the port or kill the process using the port
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process (replace PID with actual process ID)
kill -9 PID

# Or use a different port
python app.py --port 8000
```

#### CORS Errors in Browser
```
Access to fetch at 'http://localhost:5000/api/cards' from origin 'http://localhost:3000' has been blocked by CORS policy
```
**Solution**: Update CORS configuration in backend
```python
# In training/backend/app.py
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:5000"])
```

#### Model Files Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: 'model/model.pkl'
```
**Solution**: Train the model first
```bash
cd training
python train_model.py
```

#### JavaScript Errors
```
ReferenceError: CardGrid is not defined
```
**Solution**: Check script loading order in HTML
```html
<!-- Ensure scripts are loaded in correct order -->
<script src="js/components/CardGrid.js"></script>
<script src="js/components/NewsCard.js"></script>
<script src="script.js"></script>
```

## 📊 Monitoring and Logs

### View Application Logs
```bash
# Backend logs
tail -f training/backend/app.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

### Monitor Database
```bash
# Connect to MongoDB shell
mongosh

# Switch to your database
use fake_news_app

# View collections
show collections

# Count documents
db.predictions.countDocuments()

# View recent predictions
db.predictions.find().sort({timestamp: -1}).limit(5)
```

### Performance Monitoring
```bash
# Check system resources
htop  # or top on some systems

# Monitor network connections
netstat -an | grep :5000
```

## 🔒 Security Considerations

### Production Deployment
1. **Change Secret Key**: Use a strong, random secret key
2. **Enable HTTPS**: Use SSL certificates
3. **Database Security**: Enable MongoDB authentication
4. **Environment Variables**: Store sensitive data in environment variables
5. **Rate Limiting**: Configure appropriate rate limits
6. **Input Validation**: Ensure all inputs are properly validated

### Example Production Configuration
```python
# production_config.py
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGODB_URI = os.environ.get('MONGODB_URI')
    DEBUG = False
    TESTING = False
```

## 🚀 Next Steps

1. **Add Sample Data**: Use the migration script to add sample articles
2. **Customize Styling**: Modify CSS files to match your brand
3. **Add Features**: Implement additional functionality like user authentication
4. **Deploy**: Consider deployment options like Heroku, AWS, or DigitalOcean
5. **Monitor**: Set up logging and monitoring for production use

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review application logs for error messages
3. Ensure all prerequisites are properly installed
4. Verify network connectivity between components

---

**🎉 Congratulations!** Your Pinterest-like fake news detector is now fully connected and ready to use!