import os
import json
import re
from typing import Dict, List, Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AInutritionService:
    def __init__(self):
        """Initialize the AI nutrition service with optional OpenAI integration."""
        self.client = None
        
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key != 'your_openai_api_key_here':
                try:
                    self.client = openai.OpenAI(api_key=api_key)
                    print("OpenAI client initialized successfully")
                except Exception as e:
                    print(f"Warning: Could not initialize OpenAI client: {e}")
                    self.client = None
            else:
                print("Warning: OpenAI API key not configured. Using fallback responses.")
        else:
            print("Warning: OpenAI library not available. Using fallback responses.")
        
    def analyze_meal(self, meal_description: str, portion_size: str = "normal") -> Dict:
        """
        Analyze a meal description and return detailed nutritional information
        """
        if not self.client:
            return self._fallback_analysis(meal_description)
            
        try:
            prompt = f"""
            Analyze this meal and provide detailed nutritional information in JSON format:
            
            Meal: {meal_description}
            Portion size: {portion_size}
            
            Please provide the response in this exact JSON format:
            {{
                "calories": number,
                "protein_g": number,
                "carbs_g": number,
                "fat_g": number,
                "fiber_g": number,
                "sodium_mg": number,
                "health_score": number (1-10),
                "meal_category": "breakfast/lunch/dinner/snack",
                "nutrition_highlights": ["key nutritional benefits"],
                "potential_improvements": ["suggestions for making it healthier"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            print(f"Error in AI meal analysis: {e}")
        
        return self._fallback_analysis(meal_description)
    
    def generate_meal_plan(self, user_profile: Dict, dietary_preferences: List[str] = None, 
                           calorie_target: int = 2000, days: int = 7) -> Dict:
        """
        Generate a personalized meal plan based on user profile and preferences
        """
        if not self.client:
            return self._fallback_meal_plan(user_profile, calorie_target, days)
            
        try:
            preferences_str = ", ".join(dietary_preferences) if dietary_preferences else "No specific preferences"
            
            prompt = f"""
            Create a {days}-day meal plan for a person with the following profile:
            
            Profile: {user_profile}
            Daily calorie target: {calorie_target}
            Dietary preferences: {preferences_str}
            
            Please provide the response in this exact JSON format:
            {{
                "total_days": {days},
                "avg_calories_per_day": estimated_average,
                "nutrition_highlights": ["key benefits of this meal plan"],
                "shopping_list": ["ingredient1", "ingredient2"],
                "daily_plans": [
                    {{
                        "day": 1,
                        "total_calories": estimated_calories,
                        "meals": {{
                            "breakfast": {{"name": "meal name", "calories": number}},
                            "lunch": {{"name": "meal name", "calories": number}},
                            "dinner": {{"name": "meal name", "calories": number}},
                            "snacks": ["snack1", "snack2"]
                        }}
                    }}
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"Error in AI meal plan generation: {e}")
        
        return self._fallback_meal_plan(user_profile, calorie_target, days)

    def get_health_insights(self, nutrition_data: Dict, user_goals: List[str] = None) -> Dict:
        """
        Analyze nutrition data and provide health insights
        """
        if not self.client:
            return self._fallback_insights(nutrition_data)
            
        try:
            goals_str = ", ".join(user_goals) if user_goals else "General health"
            
            prompt = f"""
            Analyze this nutrition data and provide health insights:
            
            Nutrition Data: {nutrition_data}
            User Goals: {goals_str}
            
            Please provide the response in this exact JSON format:
            {{
                "overall_score": number (1-10),
                "strengths": ["positive aspects"],
                "areas_for_improvement": ["areas to work on"],
                "recommendations": {{
                    "immediate": ["immediate actions"],
                    "long_term": ["long-term changes"],
                    "meal_suggestions": ["specific meal ideas"]
                }},
                "nutrient_analysis": {{
                    "adequate": ["nutrients at good levels"],
                    "deficient": ["nutrients that need increase"],
                    "excessive": ["nutrients that should be reduced"]
                }}
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"Error in AI health insights: {e}")
        
        return self._fallback_insights(nutrition_data)

    def suggest_meal_improvements(self, meal_description: str, health_goals: List[str] = None) -> Dict:
        """
        Suggest improvements for a meal based on health goals
        """
        if not self.client:
            return self._fallback_suggestions(meal_description)
            
        try:
            goals_str = ", ".join(health_goals) if health_goals else "General health"
            
            prompt = f"""
            Suggest improvements for this meal:
            
            Meal: {meal_description}
            Health Goals: {goals_str}
            
            Please provide the response in this exact JSON format:
            {{
                "improved_meal": "description of improved version",
                "changes_made": ["list of specific changes"],
                "nutritional_improvements": ["how nutrition improved"],
                "substitutions": [
                    {{"original": "ingredient", "replacement": "better option", "reason": "why it's better"}}
                ],
                "cooking_tips": ["healthier cooking methods"],
                "health_benefits": ["expected health benefits"]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            print(f"Error in AI meal improvements: {e}")
        
        return self._fallback_suggestions(meal_description)
    
    def _fallback_analysis(self, meal_description: str) -> Dict:
        """Fallback analysis when AI service is unavailable"""
        # Simple calorie estimation based on keywords
        calorie_estimates = {
            'salad': 150, 'chicken': 250, 'rice': 200, 'bread': 100,
            'pasta': 300, 'pizza': 400, 'burger': 500, 'sandwich': 300
        }
        
        estimated_calories = 250  # default
        for food, calories in calorie_estimates.items():
            if food in meal_description.lower():
                estimated_calories = calories
                break
        
        return {
            "calories": estimated_calories,
            "protein_g": 20,
            "carbs_g": 30,
            "fat_g": 10,
            "fiber_g": 5,
            "sodium_mg": 500,
            "health_score": 7,
            "meal_category": "meal",
            "nutrition_highlights": ["Basic nutritional estimate"],
            "potential_improvements": ["AI analysis unavailable - consider adding more vegetables"]
        }
    
    def _fallback_meal_plan(self, user_profile: Dict, calorie_target: int, days: int) -> Dict:
        """Fallback meal plan when AI service is unavailable"""
        daily_plans = []
        for day in range(1, days + 1):
            daily_plans.append({
                "day": day,
                "total_calories": calorie_target,
                "meals": {
                    "breakfast": {"name": "Oatmeal with fruits", "calories": calorie_target // 4},
                    "lunch": {"name": "Grilled chicken salad", "calories": calorie_target // 3},
                    "dinner": {"name": "Salmon with vegetables", "calories": calorie_target // 3},
                    "snacks": ["Mixed nuts", "Greek yogurt"]
                }
            })
        
        return {
            "total_days": days,
            "avg_calories_per_day": calorie_target,
            "nutrition_highlights": ["AI meal planning unavailable - using healthy template"],
            "shopping_list": ["oats", "fruits", "chicken", "vegetables", "salmon", "nuts", "yogurt"],
            "daily_plans": daily_plans
        }
    
    def _fallback_insights(self, nutrition_data: Dict) -> Dict:
        """Fallback insights when AI service is unavailable"""
        return {
            "overall_score": 7,
            "strengths": ["Maintaining consistent food logging"],
            "areas_for_improvement": ["AI analysis unavailable - continue tracking"],
            "recommendations": {
                "immediate": ["Continue tracking your meals"],
                "long_term": ["Maintain balanced nutrition"],
                "meal_suggestions": ["Focus on whole foods"]
            },
            "nutrient_analysis": {
                "adequate": ["basic nutrition tracking"],
                "deficient": ["detailed analysis unavailable"],
                "excessive": ["none identified"]
            }
        }
    
    def _fallback_suggestions(self, meal_description: str) -> Dict:
        """Fallback suggestions when AI service is unavailable"""
        return {
            "improved_meal": f"Enhanced {meal_description} with more vegetables",
            "changes_made": ["Add more vegetables", "Use whole grains", "Choose lean proteins"],
            "nutritional_improvements": ["Increased fiber", "Better micronutrients", "Improved protein quality"],
            "substitutions": [
                {"original": "refined grains", "replacement": "whole grains", "reason": "better fiber and nutrients"},
                {"original": "fried foods", "replacement": "grilled options", "reason": "reduced unhealthy fats"}
            ],
            "cooking_tips": ["Steam vegetables to preserve nutrients", "Grill instead of frying"],
            "health_benefits": ["AI suggestions unavailable - using general healthy guidelines"]
        }