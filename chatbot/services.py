"""
Business logic for chatbot: OpenAI integration, logging.
"""
import os
from django.conf import settings
from .models import ChatbotLog, ChatbotSettings
from accounts.models import User

# Initialize OpenAI client with proper error handling
try:
    from openai import OpenAI
    
    def get_openai_client():
        """Get OpenAI client with current API key"""
        # Try to get API key from multiple sources
        api_key = ChatbotSettings.get_api_key() or os.environ.get("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        
        if api_key:
            return OpenAI(api_key=api_key)
        return None
    
except ImportError:
    def get_openai_client():
        return None
    print("WARNING: OpenAI package not installed. Chatbot will use rule-based responses only.")

def log_chatbot_interaction(user, message, response):
    """
    Log chatbot interactions for analysis and improvement
    """
    ChatbotLog.objects.create(
        user=user,
        user_message=message,
        bot_response=response,
        reviewed_by_admin=False
    )

def get_openai_response(message, user=None):
    """
    Generate a response using OpenAI's API
    """
    # Get OpenAI client
    client = get_openai_client()
    
    # Check if OpenAI client is available
    if not client:
        print("OpenAI client not available. Using rule-based response.")
        return rule_based_response(message)
    
    try:
        # Build system message
        system_message = "You are a helpful assistant for elderly care."
        
        # Add user context if available
        user_context = ""
        if user and isinstance(user, User):
            user_context = f" The user's name is {user.get_full_name()}."
        
        # Get model from settings with fallback
        model = ChatbotSettings.get_model() or "gpt-3.5-turbo"
        
        # Create the chat completion
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message + user_context},
                {"role": "user", "content": message}
            ]
        )
        
        # Extract and return the response
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        # Fallback to rule-based response if API fails
        return rule_based_response(message)

def rule_based_response(message):
    """
    Generate a rule-based response for the chatbot (fallback method)
    """
    message = message.lower()
    
    # Greetings
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings', 'namaste']):
        return "Namaste! How can I assist you today?"
    
    # Health related
    elif any(word in message for word in ['medicine', 'pill', 'medication']):
        return "It's important to take your medications as prescribed. Would you like me to remind you about your medication schedule?"
    
    # Wellness
    elif any(word in message for word in ['exercise', 'yoga', 'meditation']):
        return "Regular gentle exercise like yoga can be very beneficial. Would you like some simple exercises suitable for seniors?"
    
    # Emotional support
    elif any(word in message for word in ['sad', 'lonely', 'alone', 'depressed']):
        return "I'm sorry to hear you're feeling that way. Would you like to talk about it or would you prefer I connect you with a caregiver?"
    
    # Family
    elif any(word in message for word in ['family', 'son', 'daughter', 'grandchild']):
        return "Family connections are important. Would you like help setting up a call with your family members?"
    
    # Help
    elif any(word in message for word in ['help', 'assistance', 'support']):
        return "I'm here to help! I can assist with medication reminders, connecting with caregivers, or providing wellness information. What do you need help with?"
    
    # Fallback
    else:
        return "I'm still learning to understand different questions. Could you please rephrase that or ask me about medications, exercise, connecting with family, or emotional support?"







