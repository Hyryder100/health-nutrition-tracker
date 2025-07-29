# 🍎 NutriTracker AI - Smart Health & Nutrition Management

A comprehensive, AI-powered health and nutrition tracking platform that helps users achieve their wellness goals through intelligent meal analysis, personalized recommendations, and advanced health insights.

## 🌟 Key Features

### 🤖 AI-Powered Intelligence
- **Smart Meal Analysis**: Describe your meals in natural language and get detailed nutrition breakdowns powered by OpenAI
- **Intelligent Calorie Estimation**: Accurate calorie and macronutrient calculations based on meal descriptions
- **Health Score Rating**: Each meal receives an AI-calculated health score (1-10) with improvement suggestions
- **Ingredient Recognition**: Automatic identification of meal components and nutritional content

### 📊 Comprehensive Health Tracking
- **Nutrition Monitoring**: Track calories, proteins, carbohydrates, fats, fiber, sodium, and micronutrients
- **Water Intake**: Monitor daily hydration with smart reminders and progress tracking
- **Exercise Logging**: Record workouts with calorie burn estimation and activity categorization
- **Sleep Quality**: Track sleep hours and quality ratings with trend analysis
- **Weight Management**: Monitor weight changes with historical data visualization

### 🗓️ AI Meal Planning
- **Personalized Meal Plans**: Generate 7-day meal plans based on health goals and dietary preferences
- **Smart Shopping Lists**: Automatically generated grocery lists from meal plans
- **Dietary Restriction Support**: Accommodates vegetarian, vegan, gluten-free, keto, and other dietary needs
- **Calorie Target Optimization**: Meal plans tailored to individual calorie and macro targets

### 💡 Health Insights & Coaching
- **Weekly Health Reports**: AI-generated insights on nutrition patterns and progress
- **Personalized Recommendations**: Actionable suggestions based on individual health data
- **Nutrient Gap Analysis**: Identify deficiencies and excesses in your diet
- **Goal Progress Tracking**: Monitor advancement toward health and nutrition objectives

### 🎯 Smart Suggestions
- **Real-time Tips**: Daily recommendations for better nutrition and hydration
- **Meal Improvements**: AI suggestions to make existing meals healthier
- **Habit Building**: Guidance for developing sustainable healthy eating patterns
- **Progress Alerts**: Notifications about goal achievements and milestones

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.9+, Flask 3.1.1 |
| **Database** | SQLite with optimized schema |
| **AI/ML** | OpenAI GPT-4, scikit-learn |
| **Frontend** | Modern HTML5, CSS3, JavaScript ES6+ |
| **Styling** | Custom CSS with CSS Grid and Flexbox |
| **Charts** | Chart.js for data visualization |
| **Security** | bcrypt for password hashing, Flask-Login |
| **Environment** | python-dotenv for configuration |

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- OpenAI API key (optional but recommended for full AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nutritracker-ai.git
   cd nutritracker-ai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI API Key for AI nutrition analysis
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_super_secret_key_for_production

# Database Configuration
DATABASE_URL=sqlite:///database.db

# App Configuration
FLASK_ENV=development
DEBUG=True

# Optional: Nutrition API for enhanced food database
NUTRITION_API_KEY=your_nutrition_api_key_here
```

### OpenAI API Setup

1. Sign up at [OpenAI](https://platform.openai.com/)
2. Generate an API key
3. Add the key to your `.env` file
4. The application will use GPT-4 for meal analysis and recommendations

## 📱 User Guide

### Getting Started

1. **Create Account**: Register with a unique username and secure password
2. **Complete Profile**: Add personal information, health goals, and dietary preferences
3. **Start Logging**: Begin tracking meals, water, exercise, and sleep
4. **Get AI Insights**: Review personalized recommendations and health reports

### Core Features

#### 🍽️ Meal Tracking
- Describe meals in natural language: "Grilled chicken breast with quinoa and steamed broccoli"
- AI automatically analyzes nutrition content and assigns health scores
- View detailed breakdowns of calories, macros, and micronutrients
- Get suggestions for meal improvements

#### 📊 Dashboard Overview
- Quick stats on daily calories, water, exercise, and sleep
- Progress bars showing goal completion
- Smart suggestions based on current data
- Easy access to all tracking features

#### 🤖 AI Meal Planning
- Generate personalized weekly meal plans
- Customize based on calorie targets and dietary restrictions
- Get shopping lists automatically generated
- Save favorite meal plans for reuse

#### 💡 Health Insights
- Weekly AI-generated health reports
- Identify nutrition patterns and trends
- Receive actionable recommendations
- Track progress toward health goals

### Advanced Features

#### Meal Improvement Suggestions
- Get AI recommendations to make meals healthier
- Learn about ingredient substitutions and cooking tips
- Understand the health benefits of suggested changes

#### Goal Setting and Tracking
- Set specific health and nutrition goals
- Monitor progress with visual charts
- Receive motivational tips and reminders

#### Data Export and Sharing
- Export health insights and meal plans
- Share achievements with friends
- Backup data for personal records

## 🏗️ Database Schema

The application uses SQLite with the following key tables:

- **users**: User authentication and basic info
- **user_profiles**: Detailed health profiles and preferences
- **meals**: Meal entries with comprehensive nutrition data
- **exercise**: Workout tracking with calories and duration
- **water**: Daily hydration monitoring
- **sleep**: Sleep hours and quality ratings
- **weight**: Weight tracking over time
- **meal_plans**: AI-generated meal planning data
- **health_insights**: Stored AI analysis and recommendations

## 🔒 Security Features

- **Password Hashing**: bcrypt for secure password storage
- **Session Management**: Flask-Login for secure user sessions
- **Data Validation**: Server-side input validation and sanitization
- **CSRF Protection**: Built-in protection against cross-site request forgery
- **Environment Variables**: Sensitive data stored securely

## 🎨 UI/UX Features

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark Mode Support**: Automatic adaptation to system preferences
- **Modern Interface**: Clean, intuitive design with smooth animations
- **Accessibility**: Screen reader friendly with proper ARIA labels
- **Progressive Enhancement**: Works with JavaScript disabled

## 📊 Data Visualization

- **Interactive Charts**: Chart.js powered nutrition and progress graphs
- **Progress Bars**: Real-time goal completion indicators
- **Trend Analysis**: Weekly and monthly pattern visualization
- **Color-coded Insights**: Visual health score and recommendation system

## 🔄 API Integration

### OpenAI Integration
- GPT-4 for meal analysis and nutrition extraction
- Intelligent meal planning and recommendation generation
- Health insight analysis and personalized coaching

### Fallback Systems
- Graceful degradation when AI services are unavailable
- Basic nutrition estimation using keyword matching
- Offline functionality for core tracking features

## 🚀 Deployment

### Production Setup

1. **Environment Configuration**
   ```bash
   export FLASK_ENV=production
   export DEBUG=False
   ```

2. **Database Migration**
   ```bash
   python -c "from app import init_db; init_db()"
   ```

3. **Web Server** (example with Gunicorn)
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and request features on GitHub Issues
- **Community**: Join our Discord server for community support
- **Email**: Contact us at support@nutritracker-ai.com

## 🔄 Roadmap

### Version 2.0 (Planned)
- [ ] Mobile app (React Native)
- [ ] Advanced meal photo recognition
- [ ] Integration with fitness trackers
- [ ] Social features and community challenges
- [ ] Nutrition coach chat bot
- [ ] Advanced analytics and reporting

### Version 1.5 (In Development)
- [ ] Food database integration
- [ ] Barcode scanning for packaged foods
- [ ] Recipe import and analysis
- [ ] Meal timing optimization
- [ ] Supplement tracking

## 📈 Changelog

### Version 1.0.0 (Current)
- ✅ AI-powered meal analysis with OpenAI
- ✅ Comprehensive nutrition tracking
- ✅ Personalized meal planning
- ✅ Health insights and recommendations
- ✅ Modern responsive web interface
- ✅ User authentication and profiles
- ✅ Data visualization with Chart.js
- ✅ Secure data handling

---

**NutriTracker AI** - Transforming health through intelligent nutrition tracking. Built with ❤️ for better wellness.

*Last updated: December 2024*
