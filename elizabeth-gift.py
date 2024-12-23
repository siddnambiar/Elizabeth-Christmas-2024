import toml
import streamlit as st
import random
import time
import google.generativeai as genai
import re
import json

# --- Configuration ---
THEME = {
    "background_color": "#f70696",
    "text_color": "#ffffff",
    "button_text_color": "#333333",
    "button_color": "#ffffff",
    "button_hover_color": "#f0f0f0",
    "accent_color": "#ffffff",
    "font_family": "serif",
    "padding": "30px",
    "border_color": "#ffffff"
}

# --- Animal and Context Data ---
ANIMALS = ["squirrel", "raccoon", "possum", "cardinal", "nuthatches", "blue jay", "deer", "butterfly", "hummingbird", "chipmunk"]
CONTEXTS = ["diet", "habitat", "behavior", "lifespan", "unique abilities", "communication"]

# --- Session State Initialization ---
# Using a dictionary for easier management
SESSION_KEYS = {
    "current_screen": 'landing',
    "score": 0,
    "questions_asked": set(),
    "answered": False,
    "glass_revealed": False,
    "total_questions": 5,
    "current_question_data": {},
    "llm_initialized": False,
    "question_number": 0,
    "intro_animation_played": False,
}

# Initialize session state variables using a loop
for key, default_value in SESSION_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def load_api_key():
    """Loads the API key from Streamlit Cloud secrets or environment."""
    try:
        api_key = st.secrets["google"]["api_key"]
        if api_key:
          return api_key
        else:
          st.error("API key not found in Streamlit secrets. Please ensure it has been configured.")
          return None
    except KeyError:
       st.error("API key not found in Streamlit secrets. Please ensure it has been configured under google/api_key.")
       return None
    except Exception as e:
      st.error(f"An error occurred during API key load: {e}")
      return None

# Initialize Gemini and add to session state
def initialize_gemini():
    api_key = load_api_key()
    if api_key:
        genai.configure(api_key=api_key)
        st.session_state.model = genai.GenerativeModel("gemini-1.5-flash")
        st.session_state.llm_initialized = True
    else:
      return None

# Randomly select an animal
def select_random_animal():
    return random.choice(ANIMALS)

# Randomly select a context
def select_random_context():
    return random.choice(CONTEXTS)

def generate_question_data(model):
    """Generates a question, options, correct answer, and additional fact using an LLM."""
    try:
        animal = select_random_animal()
        context = select_random_context()
        prompt = f"""Generate a question about a {animal}'s {context}.
        Provide 3 multiple choice options, and indicate the single correct answer. The format should be a JSON object with keys for "question", "options" (which is an array), "correct_answer", and "additional_fact". Do not include a title.

        Here is an example of the format you should use:
        {{
            "question": "What do I do with the acorns that I bury?",
            "options": ["Leave them be", "Remember their location for later", "Forget where I buried them"],
            "correct_answer": "Forget where I buried them",
            "additional_fact": "That helps plant thousands of trees!"
        }}
        """
        response = model.generate_content(prompt)
        if not response or not response.text:
            st.error("LLM returned an empty response.")
            return None

        question_data = response.text.strip()

        # Remove markdown code block if present
        match = re.match(r'```(?:json)?\s*(.*?)\s*```', question_data, re.DOTALL)
        if match:
             question_data = match.group(1).strip()

        try:
          return json.loads(question_data)
        except json.JSONDecodeError as e:
           st.error(f"JSON decode error: {e}")
           st.error(f"LLM output: {question_data}")
           return None

    except Exception as e:
       st.error(f"Error during LLM call: {e}")
       return None

st.set_page_config(
    page_title="A Gift for Elizabeth",
    initial_sidebar_state="collapsed",
)

def apply_custom_css():
    """Apply custom CSS styling to the application."""
    st.markdown(
        f"""
        <style>
        body {{
            background-color: {THEME["background_color"]};
            color: {THEME["text_color"]};
            font-family: {THEME["font_family"]};
            margin: 0;
        }}
        .stApp {{
            max-width: 100%;
            padding: {THEME["padding"]};
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
         .title-text {{
            color: {THEME["accent_color"]};
            font-size: 2.8em;
            text-align: center;
            padding-bottom: 15px;
            line-height: 1.2;
            font-weight: bold;
            animation: fadeIn 1.2s ease-out;
        }}
        .small-text {{
            color: {THEME["text_color"]};
            font-size: 1.1em;
            text-align: center;
            padding-bottom: 25px;
            line-height: 1.4;
            animation: fadeIn 1.2s ease-out;
        }}
         .score-text {{
            color: {THEME["text_color"]};
            font-size: 1.4em;
            text-align: center;
            padding-bottom: 15px;
             font-weight: bold;
        }}
        .gift-card {{
            background-color: transparent;
            text-align: center;
            padding: 20px;
            margin: 20px auto;
            max-width: 700px;
            border-radius: 10px;
            border: 1px solid {THEME["border_color"]};
            animation: fadeIn 1.2s ease-out;
        }}
        .button-container {{
            text-align: center;
            margin: 20px auto;
            max-width: 400px;
            animation: fadeIn 1.2s ease-out;
        }}
       .stButton>button {{
            background-color: {THEME["button_color"]};
            color: {THEME["button_text_color"]};
            padding: 12px 25px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1.1em;
            min-width: 175px;
            width: 100%;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        .stButton>button:hover {{
            background-color: {THEME["button_hover_color"]};
            transform: translateY(-3px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }}
        .message-box {{
            background-color: transparent;
            padding: 25px;
            margin: 25px auto;
            text-align: center;
            line-height: 1.7;
            max-width: 900px;
            border-radius: 10px;
            border: 1px solid {THEME["border_color"]};
            animation: fadeIn 1.2s ease-out;
        }}
        .image-container {{
            text-align: center;
            padding: 25px;
            margin: 15px auto;
            max-width: 700px;
            animation: fadeIn 1.2s ease-out;
        }}
        .info-container {{
            background-color: transparent;
            padding: 20px;
            margin: 20px auto;
            text-align: center;
            line-height: 1.6;
            max-width: 900px;
            border-radius: 10px;
            border: 1px solid {THEME["border_color"]};
             animation: fadeIn 1.2s ease-out;
        }}
          .option-button-row {{
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 10px auto; /* Added margin for spacing */
            max-width: 400px;
        }}
        a {{
            color: {THEME["accent_color"]};
            text-decoration: none;
            transition: all 0.3s ease;
        }}
        a:hover {{
            text-decoration: underline;
            opacity: 0.8;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        @keyframes slideInFromBottom {{
            from {{transform: translateY(100px); opacity: 0;}}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def reset_game_state():
    """Reset game state variables."""
    st.session_state.score = 0
    st.session_state.questions_asked = set()
    st.session_state.answered = False
    if 'current_question_data' in st.session_state:
        del st.session_state.current_question_data
    st.session_state.question_number = 0
    st.session_state.intro_animation_played = False


def display_landing_screen():
    """Display the initial landing screen with animation and reset button"""
    st.markdown(
        "<h1 class='title-text'>Hello Elizabeth! Good Morning.<br/>I hope you're having a wonderful Christmas morning.</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
      if st.session_state.intro_animation_played == False:
          st.markdown("Would you like to play a fun game to learn more about our backyard friends?", unsafe_allow_html=True)
          if st.button("Click this button to start!", use_container_width=True):
            with st.spinner("Let's Get Started..."):
              time.sleep(1)
              st.session_state.intro_animation_played = True
              reset_game_state()
              st.session_state.current_screen = 'critter_game'
              st.rerun()
      else:
        if st.button("Begin Your Morning Adventure!", use_container_width=True):
            reset_game_state()
            st.session_state.current_screen = 'critter_game'
            st.rerun()

def display_critter_game():
    """Display the critter game screen with facts and interactions."""
    st.markdown("<h1 class='title-text' style='animation: slideInFromBottom 0.8s ease-out;'>Backyard Friends</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='small-text' style='animation: slideInFromBottom 0.8s ease-out;'>Let's learn some fun facts about our backyard friends! Each correct guess adds a point!</p>",
        unsafe_allow_html=True
    )

    # Display score and question count
    st.markdown(
        f"<p class='score-text' style='animation: slideInFromBottom 0.8s ease-out;'>Score: {st.session_state.score} | Questions Remaining: {st.session_state.total_questions - st.session_state.question_number}</p>",
        unsafe_allow_html=True
    )

    try:
         # Initialize LLM if not already done
        if not st.session_state.llm_initialized:
             initialize_gemini()

        # Generate a question if none is current
        if not st.session_state.current_question_data and st.session_state.llm_initialized:
            with st.spinner('Fetching new question...'):
                question_data = generate_question_data(st.session_state.model)
                if question_data:
                    st.session_state.current_question_data = question_data
                    st.session_state.question_number += 1
                else:
                    st.error("Failed to generate question, please try again!")
                    return

        if 'question' in st.session_state.current_question_data:
             # Display the current fact
            st.markdown(
                f"<div class='message-box' style='animation: slideInFromBottom 0.8s ease-out;'><p class='small-text' style='font-size: 1.3em;'>{st.session_state.current_question_data['question']}</p></div>",
                unsafe_allow_html=True
            )
            # Create buttons for animal choices
            if not st.session_state.answered:
               
                with st.container():
                    st.markdown("<div class='option-button-row'>", unsafe_allow_html=True)
                    for i, option in enumerate(st.session_state.current_question_data["options"]):
                        if st.button(option, key=f"choice_{i}", use_container_width=True):
                                st.session_state.answered = True
                                if st.session_state.current_question_data["options"][i] == st.session_state.current_question_data["correct_answer"]:
                                     st.session_state.score += 1
                                     st.session_state.last_answer = f"Correct! 🎉 {st.session_state.current_question_data['additional_fact']}"
                                else:
                                     st.session_state.last_answer = f"Not quite! The correct answer was {st.session_state.current_question_data['correct_answer']}! 🎓 {st.session_state.current_question_data['additional_fact']}"
                                st.session_state.questions_asked.add(st.session_state.current_question_data["question"])
                                st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                

        # Show answer response
        if st.session_state.answered:
             st.markdown(
                 f"<p class='small-text' style='font-size: 1.3em; animation: slideInFromBottom 0.8s ease-out;'>{st.session_state.last_answer}</p>",
                 unsafe_allow_html=True
             )
             col1, col2, col3 = st.columns([1, 2, 1])
             with col2:
                 if st.button("Next Fact", use_container_width=True):
                     if st.session_state.question_number >= st.session_state.total_questions:
                         st.session_state.current_screen = 'reveal_glass'
                         st.rerun()
                     else:
                        if 'current_question_data' in st.session_state:
                            del st.session_state.current_question_data
                        st.session_state.answered = False
                        st.rerun()
        
             with col3:
               if st.button("Restart Game", use_container_width=True):
                  reset_game_state()
                  st.session_state.current_screen = 'critter_game'
                  st.rerun()

    except Exception as e:
        st.error(f"Something went wrong in the game. Let's start over! Error: {e}")
        reset_game_state()
        st.rerun()

def display_reveal_glass():
    """Display the glass reveal screen with animation effect."""
    st.markdown("<h1 class='title-text' style='animation: slideInFromBottom 0.8s ease-out;'>A Special Morning Gift</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p class='small-text' style='animation: slideInFromBottom 0.8s ease-out;'>You did great! Final Score: {st.session_state.score}/{st.session_state.total_questions}</p>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if not st.session_state.glass_revealed:
            st.markdown(
                "<div class='image-container'><p class='small-text' style='animation: slideInFromBottom 0.8s ease-out;'>Now for your surprise... tap to reveal!</p></div>",
                unsafe_allow_html=True
            )
            if st.button("Reveal Your Gift", use_container_width=True):
                st.session_state.glass_revealed = True
                st.rerun()
        else:
            st.markdown(
                "<div class='image-container'><p class='small-text' style='animation: slideInFromBottom 0.8s ease-out;'>Your gift awaits...</p></div>",
                unsafe_allow_html=True
            )
            if st.button("See Your Gift", use_container_width=True):
                st.session_state.current_screen = 'gift_card'
                st.rerun()

def display_gift_card():
    """Display the gift card screen with workshop details."""
    st.markdown("<h1 class='title-text' style='animation: slideInFromBottom 0.8s ease-out;'>A Gift For You, My Love</h1>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class='gift-card' style='animation: slideInFromBottom 0.8s ease-out;'>
            <p class='small-text'>
                You get to create a beautiful glass flower at Corradetti Glass Studio!<br/>
                Join me, or invite a friend to come along!
            </p>
            <p class='small-text'><b>Workshop Date:</b> April 12th: 12pm</p>
            <p class='small-text'>
                <b>Location:</b> Park in any of the lots at Clipper Mill. If you can't find a spot
                just use the complimentary valet we share with the restaurant.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
         f"""
         <div class='info-container' style='animation: slideInFromBottom 0.8s ease-out;'>
             <p class='small-text
         <div class='info-container' style='animation: slideInFromBottom 0.8s ease-out;'>
             <p class='small-text'>
                  Have fun playing with hot glass! In this activity we’ll show you how to stretch & pull 2,000 degree glass to create a 8-12″ colorful flower. These make great Mother’s Day gifts. We handle the skilled part and you do the fun part. Arrive at the hour you register for to get your numbered ticket. Your individual 15 minute working time is within that hour. Pieces will be cooled & ready for pick up 2 days later. Want to do all the work on your own? Try our 6hr Beginner Glassblowing Class.
             </p>
             <p class='small-text'>
                   <a href='https://corradetti.com/product/flower-mini-workshop/' target='_blank'>Click here for more information on the event!</a>
             </p>
         </div>
         """,
         unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("See More Classes", use_container_width=True):
            st.markdown(
                f"<div class='small-text'><a href='https://corradetti.com/mini-workshops/' target='_blank'>Corradetti Mini-Workshops</a></div>",
                unsafe_allow_html=True
            )

        if st.button("A Note", use_container_width=True):
            st.session_state.current_screen = 'message_screen'
            st.rerun()

def display_message_screen():
    """Display the final message screen with personal Christmas note."""
    st.markdown("<h1 class='title-text' style='animation: slideInFromBottom 0.8s ease-out;'>My Heart To You 💝</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='message-box' style='animation: slideInFromBottom 0.8s ease-out;'>
            <p class='small-text'>
                My dearest Elizabeth 🌟,
                <br><br>
                First, merry Christmas! 🎄 I think about what you mentioned to me about how holidays are happier for you since we have been together, and thinking of that warms my heart. Very few things make me as happy as seeing you happy, and I am constantly thankful that I get to spend our holidays together for years and years to come. ✨
                <br><br>
                As with any happy relationship, we have had our challenges. For the longest time in life, I lived by a set of rules, ideologies, and values that were instilled in me because of where and how I was raised. Looking back, moving to the US was a daunting task, and I really should have been more intentional about my feelings during the transitory period of adjusting to life in the US. 🌎
                <br><br>
                As it stands, I never did do any exploration around my feelings and continued to live life as though the same set of rules, ideologies, and values would hold me in good stead as I navigated life in this country. This was a mistake, and I know that now because I am finally starting to understand that the sense of discomfort I had felt through so many social, professional, and private experiences over the years wasn't intended for me to "fix" myself and "get over" the discomfort, but instead was because my mind and body were trying to communicate my likes, dislikes, wants, and opinions. For most of my life, I simply could not figure out how to be gentle with myself and try to pay attention to the discomfort and sit with it, and to not let it overwhelm me. 🫂
                <br><br>
                A lot of that started changing the day I met you. 💫 I didn't know it at the time, and neither you nor I had any idea what sort of personal journeys each of us would go through. I sometimes tell you about qualities that I admire in you - such as your sense of loyalty to loved ones, the warmth you bring to close relationships, and the empathy you have for your fellow humans and especially critters. 🐾
                <br><br>
                The qualities of yours that I probably don't talk about as much though are how you've always been gentle, welcoming, and understanding of all things about me. This year especially, I know I've thrown some curveballs at you. I would have completely understood if all of these curveballs frustrated you. And I'm sure there were times you felt frustrated. And yet you've ALWAYS been willing to listen to me, and consider my point of view, and you've always prioritized the importance of having an open communication channel. 💝
                <br><br>
                I cannot begin to express how grateful I am for this, and how I think the reason I've been able to make so much progress on my social, cultural, and sexual identities is because of the implicit mental space you've given me to work some of this shit out. 🌈
                <br><br>
                You're an incredible partner, and I am very thankful to have you. Merry Christmas, my love. 🎄✨
                <br><br>
                Love,<br>
                Sidd 💕
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    
def main():
    """Main application entry point."""
    try:
        apply_custom_css()

        # Display appropriate screen based on current state
        screens = {
            'landing': display_landing_screen,
            'critter_game': display_critter_game,
            'reveal_glass': display_reveal_glass,
            'gift_card': display_gift_card,
            'message_screen': display_message_screen
        }

        current_screen = st.session_state.current_screen
        if current_screen in screens:
            screens[current_screen]()
        else:
            st.session_state.current_screen = 'landing'
            st.rerun()

    except Exception as e:
        st.error(f"Something went wrong. Returning to start... Error: {e}")
        st.session_state.current_screen = 'landing' # Reset the screen
        st.rerun()

if __name__ == '__main__':
    main()