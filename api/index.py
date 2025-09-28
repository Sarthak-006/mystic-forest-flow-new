from flask import Flask, request, jsonify, send_from_directory, make_response
import requests
import hashlib
import os
import time
from flask_cors import CORS
import traceback
# Import your story_nodes, other helpers (modified to remove pygame)
# MAKE SURE Pillow is installed for manga generation later
# from PIL import Image, ImageDraw # If doing manga server-side

app = Flask(__name__)
CORS(app, origins=["*"], methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])  # Enable CORS for all routes

# --- Constants (Remove Pygame colors/fonts) ---
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
IMAGE_MODEL = 'flux'
# ... other non-pygame constants ...
# ... your story_nodes dictionary ...

# --- Game Story Nodes ---
story_nodes = {
    "start": {
        "situation": "You find yourself in a mysterious forest. The path ahead splits in two directions. What do you do?",
        "prompt": "Fantasy forest with two paths, mysterious, ethereal light, detailed",
        "seed": 12345,
        "choices": [
            {
                "text": "Take the path that leads deeper into the forest",
                "next_node": "deep_forest",
                "score_modifier": 1,
                "tag": "curious"
            },
            {
                "text": "Take the path that seems to lead out of the forest",
                "next_node": "forest_edge",
                "score_modifier": 0,
                "tag": "cautious"
            }
        ]
    },
    "deep_forest": {
        "situation": "As you venture deeper into the forest, you encounter a small magical creature trapped under a fallen branch.",
        "prompt": "Small magical glowing creature trapped under branch, fantasy forest, rays of light, detailed",
        "seed": 54321,
        "choices": [
            {
                "text": "Help free the creature",
                "next_node": "grateful_creature",
                "score_modifier": 2,
                "tag": "kind"
            },
            {
                "text": "Ignore the creature and continue exploring",
                "next_node": "lost_forest",
                "score_modifier": -1,
                "tag": "selfish"
            }
        ]
    },
    "grateful_creature": {
        "situation": "You free the creature, who thanks you and offers to lead you to a hidden treasure as a reward.",
        "prompt": "Magical glowing creature leading adventurer through fantasy forest, magical trail, treasure map, detailed",
        "seed": 67890,
        "choices": [
            {
                "text": "Follow the creature to the treasure",
                "next_node": "hidden_treasure",
                "score_modifier": 1,
                "tag": "adventurous"
            },
            {
                "text": "Thank the creature but say you need to find your way out",
                "next_node": "creature_guidance",
                "score_modifier": 0,
                "tag": "practical"
            }
        ]
    },
    "hidden_treasure": {
        "situation": "The creature leads you to an ancient chest hidden beneath tree roots. Inside you find a magical amulet that glows with power.",
        "prompt": "Ancient treasure chest with magical glowing amulet, tree roots, fantasy forest, detailed",
        "seed": 13579,
        "choices": [
            {
                "text": "Take the amulet and wear it",
                "next_node": "amulet_power",
                "score_modifier": 2,
                "tag": "risk-taker"
            },
            {
                "text": "Leave the amulet, treasures in enchanted forests often have curses",
                "next_node": "wise_decision",
                "score_modifier": 1,
                "tag": "wise"
            }
        ]
    },
    "amulet_power": {
        "situation": "As you put on the amulet, you feel a surge of magical energy. Your senses heighten, and you can now see magical paths in the forest that were invisible before.",
        "prompt": "Character wearing glowing magical amulet, visible magical paths, enchanted forest, magical energy, detailed",
        "seed": 24680,
        "choices": [
            {
                "text": "Follow the brightest magical path",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "bold"
            },
            {
                "text": "Use your new power to find the safest way out",
                "next_node": "_calculate_end",
                "score_modifier": 0,
                "tag": "careful"
            }
        ]
    },
    "forest_edge": {
        "situation": "You reach the edge of the forest and see a small village in the distance. There's also a strange cave entrance nearby.",
        "prompt": "Edge of fantasy forest, distant village, mysterious cave entrance, sunset, detailed",
        "seed": 97531,
        "choices": [
            {
                "text": "Head toward the village",
                "next_node": "village_arrival",
                "score_modifier": 0,
                "tag": "social"
            },
            {
                "text": "Explore the mysterious cave",
                "next_node": "cave_entrance",
                "score_modifier": 1,
                "tag": "adventurous"
            }
        ]
    },
    "generic_good_ending": {
        "is_end": True,
        "ending_category": "Heroic Journey",
        "situation": "Your choices have led you to become a hero of the forest. The magical creatures celebrate your deeds, and you've discovered powers within yourself you never knew existed. You return home with incredible stories and the knowledge that you've made a positive difference in this magical realm.",
        "prompt": "Hero celebrated by magical forest creatures, magical aura, fantasy celebration, triumphant pose, detailed",
        "seed": 11111,
        "choices": []
    },
    "generic_neutral_ending": {
        "is_end": True,
        "ending_category": "Forest Explorer",
        "situation": "You've had an interesting adventure in the magical forest. While you didn't become a legendary hero, you've seen wonders few others have witnessed. You make your way back home, forever changed by your experiences in the enchanted woods.",
        "prompt": "Character exiting magical forest, looking back with wonder, mixed emotions, sunset, detailed",
        "seed": 22222,
        "choices": []
    },
    "generic_bad_ending": {
        "is_end": True,
        "ending_category": "Lost Wanderer",
        "situation": "Your choices have led you astray. You find yourself hopelessly lost in the darkening forest. The magical creatures no longer help you, and strange shadows follow your every move. You fear you may never find your way home again.",
        "prompt": "Lost traveler in dark fantasy forest, ominous shadows, fear, getting dark, detailed",
        "seed": 33333,
        "choices": []
    },
    "lost_forest": {
        "situation": "As you continue deeper into the forest, ignoring the trapped creature, you start to realize you're getting lost. The trees seem to close in around you.",
        "prompt": "Lost in dense fantasy forest, closing in trees, disorienting paths, foreboding atmosphere, detailed",
        "seed": 44444,
        "choices": [
            {
                "text": "Try to retrace your steps",
                "next_node": "lost_deeper",
                "score_modifier": -1,
                "tag": "practical"
            },
            {
                "text": "Climb a tree to get a better view",
                "next_node": "tree_climb",
                "score_modifier": 1,
                "tag": "resourceful"
            }
        ]
    },
    "lost_deeper": {
        "situation": "Attempting to retrace your steps only leads you deeper into the forest. Night is falling, and strange noises surround you.",
        "prompt": "Dark fantasy forest at night, eerie glowing eyes, lost traveler, fear, detailed",
        "seed": 55555,
        "choices": [
            {
                "text": "Make camp and wait for daylight",
                "next_node": "_calculate_end",
                "score_modifier": -1,
                "tag": "patient"
            },
            {
                "text": "Keep moving despite the darkness",
                "next_node": "_calculate_end",
                "score_modifier": -2,
                "tag": "stubborn"
            }
        ]
    },
    "tree_climb": {
        "situation": "From atop a tall tree, you spot a clearing with a strange stone circle that seems to glow with magic. You also see the forest edge in the far distance.",
        "prompt": "View from tall tree, fantasy forest, glowing stone circle in clearing, forest edge in distance, detailed",
        "seed": 66666,
        "choices": [
            {
                "text": "Head toward the mysterious stone circle",
                "next_node": "stone_circle",
                "score_modifier": 1,
                "tag": "curious"
            },
            {
                "text": "Make your way toward the forest edge",
                "next_node": "forest_edge",
                "score_modifier": 0,
                "tag": "cautious"
            }
        ]
    },
    "creature_guidance": {
        "situation": "The magical creature nods understandingly and offers to guide you to the forest edge instead. It leads you along a hidden path that seems to shimmer with gentle magic.",
        "prompt": "Magical creature guiding traveler along shimmering path, forest edge visible, fantasy forest, detailed",
        "seed": 77777,
        "choices": [
            {
                "text": "Thank the creature again before parting ways",
                "next_node": "forest_edge",
                "score_modifier": 1,
                "tag": "grateful"
            },
            {
                "text": "Ask the creature if it would like to accompany you further",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "friendly"
            }
        ]
    },
    "stone_circle": {
        "situation": "You find an ancient stone circle with strange symbols. The air feels charged with magic, and the stones seem to pulse with an inner light.",
        "prompt": "Ancient stone circle with glowing symbols, magical aura, fantasy forest clearing, detailed",
        "seed": 88888,
        "choices": [
            {
                "text": "Touch the central stone and speak a word of power",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "magical"
            },
            {
                "text": "Study the symbols to try to understand their meaning",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "scholarly"
            }
        ]
    },
    "wise_decision": {
        "situation": "You decide to leave the amulet behind. As you walk away, you hear a faint hissing sound and turn to see the amulet dissolving into a puddle of poisonous liquid. Your caution has saved you.",
        "prompt": "Fantasy amulet dissolving into poisonous liquid, cautious adventurer backing away, magical chest, detailed",
        "seed": 99999,
        "choices": [
            {
                "text": "Continue exploring the forest with heightened caution",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "vigilant"
            },
            {
                "text": "Ask the creature to guide you back to safer territory",
                "next_node": "creature_guidance",
                "score_modifier": 0,
                "tag": "practical"
            }
        ]
    },
    "village_arrival": {
        "situation": "You arrive at the village to find it's inhabited by friendly forest folk who welcome you warmly. They offer food and shelter, curious about your forest adventures.",
        "prompt": "Fantasy village with forest folk welcoming traveler, cozy cottages, warm lighting, detailed",
        "seed": 12121,
        "choices": [
            {
                "text": "Share your adventures and ask about the forest's secrets",
                "next_node": "_calculate_end",
                "score_modifier": 1,
                "tag": "social"
            },
            {
                "text": "Thank them but explain you need to continue your journey",
                "next_node": "_calculate_end",
                "score_modifier": 0,
                "tag": "independent"
            }
        ]
    },
    "cave_entrance": {
        "situation": "The cave entrance reveals a passage lined with glowing crystals that illuminate the darkness with a soft blue light.",
        "prompt": "Cave entrance with glowing blue crystals, mysterious passage, fantasy setting, detailed",
        "seed": 23232,
        "choices": [
            {
                "text": "Venture deeper into the crystal cave",
                "next_node": "_calculate_end",
                "score_modifier": 2,
                "tag": "brave"
            },
            {
                "text": "Take just one small crystal and head back to the forest edge",
                "next_node": "_calculate_end",
                "score_modifier": -1,
                "tag": "greedy"
            }
        ]
    },
    "heroic_savior_ending": {
        "is_end": True,
        "ending_category": "Heroic Savior",
        "situation": "Your kindness and courage have made you a legendary hero of the forest. The magical creatures see you as their champion and protector. You've discovered ancient powers within yourself that allow you to communicate with the forest and its inhabitants. Your name will be sung in the folklore of this realm for generations to come.",
        "prompt": "Epic fantasy hero, magical forest defender, ancient powers, magical creatures celebrating, detailed fantasy illustration",
        "seed": 11112,
        "choices": []
    },
    "wise_mage_ending": {
        "is_end": True,
        "ending_category": "Wise Mage",
        "situation": "Your wisdom and magical affinity have transformed you into a powerful mage. The forest has accepted you as one of its guardians, and you've established a small tower where you study the ancient magics that flow through this realm. Many travelers seek your guidance, and you've become a respected figure throughout the lands.",
        "prompt": "Wise mage in forest tower, magical tomes, arcane study, glowing runes, fantasy illustration, detailed",
        "seed": 11113,
        "choices": []
    },
    "forest_guardian_ending": {
        "is_end": True,
        "ending_category": "Forest Guardian",
        "situation": "The magic of the forest has chosen you as its guardian. You've bonded with the ancient spirits of the woods, gaining the ability to shape and protect this magical realm. Your body now carries marks of the forest—perhaps leaves for hair or bark-like skin—as you've become part-human, part-forest entity, respected and sometimes feared by those who enter your domain.",
        "prompt": "Human-forest hybrid guardian, bark skin, leaf hair, forest spirits, magical forest throne, fantasy character, detailed illustration",
        "seed": 11114,
        "choices": []
    },
    "peaceful_traveler_ending": {
        "is_end": True,
        "ending_category": "Peaceful Traveler",
        "situation": "You've explored the wonders of the magical forest and learned much from your journey. Though you didn't become a legendary hero, you carry the forest's wisdom with you. You now travel between villages, sharing tales of the enchanted woods and occasionally using small magics you learned there to help those in need.",
        "prompt": "Wandering storyteller, magical trinkets, village gathering, fantasy traveler, sunset, detailed illustration",
        "seed": 22223,
        "choices": []
    },
    "forest_explorer_ending": {
        "is_end": True, 
        "ending_category": "Forest Explorer",
        "situation": "Your exploration of the magical forest has made you a renowned expert in magical flora and fauna. You've documented countless species unknown to the outside world, creating detailed journals that scholars pay handsomely to study. You now lead occasional expeditions into the forest, guiding those brave enough to witness its wonders.",
        "prompt": "Fantasy naturalist, magical creature sketches, expedition camp, journals, forest background, detailed illustration",
        "seed": 22224,
        "choices": []
    },
    "merchant_ending": {
        "is_end": True,
        "ending_category": "Forest Merchant",
        "situation": "Your adventures in the magical forest have given you access to rare herbs, magical trinkets, and exotic materials. You've established a small but profitable trading post at the forest's edge, becoming the go-to merchant for magical components. Wizards and alchemists from far and wide seek your uniquely sourced goods.",
        "prompt": "Fantasy merchant shop, magical herbs and potions, trading post, forest edge, customer wizards, detailed illustration",
        "seed": 22225,
        "choices": []
    },
    "lost_soul_ending": {
        "is_end": True,
        "ending_category": "Lost Soul",
        "situation": "The forest's magic has clouded your mind and you've lost your way—both literally and figuratively. You wander the ever-shifting paths, no longer remembering who you were before entering these woods. The forest creatures watch you with pity, but none approach, for you have become a cautionary tale told to those who might enter the forest unprepared.",
        "prompt": "Lost wanderer in dark forest, tattered clothes, confused expression, glowing eyes watching from darkness, fantasy horror, detailed illustration",
        "seed": 33334,
        "choices": []
    },
    "cursed_wanderer_ending": {
        "is_end": True,
        "ending_category": "Cursed Wanderer",
        "situation": "Your selfish actions in the forest have drawn the ire of ancient spirits. A curse now follows you—perhaps your shadow moves independently, or your reflection shows a twisted version of yourself. You search endlessly for a cure, but the curse seems to strengthen the further you get from the forest that birthed it.",
        "prompt": "Cursed traveler, unnatural shadow, twisted reflection in water, dark fantasy, horror elements, detailed illustration",
        "seed": 33335,
        "choices": []
    },
    "forest_prisoner_ending": {
        "is_end": True,
        "ending_category": "Forest Prisoner",
        "situation": "The forest has claimed you as its prisoner. The paths continuously lead you back to the center, no matter which direction you travel. You've built a small shelter and learned to survive, but freedom eludes you. Sometimes you see other travelers through the trees, but when you call out, they cannot seem to hear you—as if you exist in a separate layer of reality.",
        "prompt": "Prisoner of magical forest, small shelter, paths that loop back, barrier of light, travelers passing by unaware, fantasy horror, detailed illustration",
        "seed": 33336,
        "choices": []
    }
}

# --- Game State (In-memory - BAD for multiple users/production) ---
game_state = {
    "current_node_id": "start",
    "story_path": [], # Store tuples: (node_id, choice_text, score_mod)
    "current_score": 0,
    "sentiment_tally": {},
    "last_error": None,
    "last_reset": time.time()  # Track when the game was last reset
}

# Add a user_sessions dictionary to track individual user sessions
user_sessions = {}

# --- Helper Functions (Refactored - NO PYGAME) ---
def get_dynamic_seed(base_seed, path_node_ids, session_id=None):
    """Generate a unique seed based on the path taken and session ID"""
    if not session_id:
        # Use existing path-based seed if no session ID
        path_hash = hashlib.md5(''.join(path_node_ids).encode()).hexdigest()
        seed = (base_seed + int(path_hash, 16)) % 999999
    else:
        # Create a unique seed combining base seed, path, and session ID
        combined = f"{base_seed}-{''.join(path_node_ids)}-{session_id}"
        seed_hash = hashlib.md5(combined.encode()).hexdigest()
        seed = int(seed_hash, 16) % 999999
    
    return seed

def enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id=None):
    """Enhance the base prompt with unique elements based on the user's journey"""
    # Get the user's style preferences (if stored in their session)
    style_elements = []
    if session_id and session_id in user_sessions and 'style_preferences' in user_sessions[session_id]:
        style_elements = user_sessions[session_id]['style_preferences']
    
    # Default style elements if none are set
    if not style_elements:
        style_elements = ["detailed", "fantasy", "ethereal"]
    
    # Add sentiment-based modifiers
    if sentiment_tally.get('kind', 0) > sentiment_tally.get('selfish', 0):
        style_elements.append("warm light")
    else:
        style_elements.append("cool tones")
        
    if sentiment_tally.get('adventurous', 0) > 1:
        style_elements.append("vibrant")
    
    if sentiment_tally.get('cautious', 0) > 1:
        style_elements.append("muted colors")
    
    # Add a unique element based on session ID if available
    if session_id:
        # Use the session ID to deterministically select unique style elements
        session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
        
        # List of potential style modifiers to make images unique
        unique_styles = [
            "cinematic lighting", "golden hour", "blue hour", "mist", 
            "ray tracing", "dramatic shadows", "soft focus", "high contrast",
            "low saturation", "high saturation", "dreamlike", "surreal",
            "watercolor style", "oil painting style", "concept art", "digital art"
        ]
        
        # Select 1-3 unique styles based on session ID
        num_styles = 1 + (session_hash % 3)  # 1 to 3 styles
        for i in range(num_styles):
            style_index = (session_hash + i) % len(unique_styles)
            style_elements.append(unique_styles[style_index])
    
    # Combine everything into an enhanced prompt
    enhanced = f"{base_prompt}, {', '.join(style_elements)}"
    
    # Make each image different even for the same node by adding timestamp
    timestamp = int(time.time())
    enhanced += f", seed:{timestamp}"
    
    return enhanced

def reset_game_state(session_id=None):
    """Reset the game state"""
    initial_state = {
        "current_node_id": "start",
        "path_history": ["start"],
        "score": 0,
        "sentiment_tally": {},
        "choice_history": [],
        "created_at": time.time()
    }
    
    # If we have a session ID, store the state in the user_sessions dictionary
    if session_id:
        if session_id not in user_sessions:
            user_sessions[session_id] = {}
        
        # Generate some random style preferences for this session
        import random
        all_style_options = [
            "fantasy", "medieval", "ethereal", "mystical", "dramatic", 
            "whimsical", "dark", "bright", "colorful", "muted"
        ]
        user_sessions[session_id]['style_preferences'] = random.sample(all_style_options, 3)
        user_sessions[session_id]['state'] = initial_state
        return user_sessions[session_id]['state']
    
    return initial_state

def get_node_details(node_id):
    """Get details for a story node with personalized content"""
    try:
        # Get base node
        node = story_nodes.get(node_id)
        if not node:
            return None
            
        # Make a copy so we don't modify the original
        node_copy = node.copy()
        
        # Personalize choices if we're not at an end node
        if not node_copy.get("is_end", False) and "choices" in node_copy:
            # Deep copy choices to avoid modifying original
            node_copy["choices"] = [choice.copy() for choice in node_copy["choices"]]
            
            # Personalize choice texts with small variations
            for choice in node_copy["choices"]:
                if "text" in choice:
                    # We could add small variations to choice text here
                    # But we'll keep the first choice consistent as required
                    pass  # Implemented in the next update
        
        return node_copy
        
    except Exception as e:
        traceback.print_exc()
        return None

# --- API Endpoints ---
@app.route('/')
def serve_index():
    try:
        return send_from_directory('../public', 'index.html')
    except Exception as e:
        print(f"Error serving index: {str(e)}")
        # Fallback response
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mystic Forest Flow</title>
        </head>
        <body>
            <h1>Mystic Forest Flow</h1>
            <p>Loading game...</p>
            <script>
                // Redirect to API test
                fetch('/api/test')
                    .then(response => response.json())
                    .then(data => console.log('API Status:', data))
                    .catch(error => console.error('API Error:', error));
            </script>
        </body>
        </html>
        """, 200

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Mystic Forest Flow API is running"})

@app.route('/api/test')
def test_endpoint():
    return jsonify({"message": "API is working", "timestamp": time.time()})

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('../public', path)
    except Exception as e:
        print(f"Error serving static file {path}: {str(e)}")
        return f"Error serving file: {str(e)}", 404

@app.route('/api/state', methods=['GET'])
def get_current_state():
    try:
        # Get user's session ID from cookies or create a new one
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate a new session ID
            import secrets
            session_id = hashlib.md5(f"{time.time()}-{secrets.token_hex(8)}".encode()).hexdigest()
        
        # Get or create the user's game state
        if session_id in user_sessions and 'state' in user_sessions[session_id]:
            game_state = user_sessions[session_id]['state']
        else:
            game_state = reset_game_state(session_id)
        
        current_node_id = game_state["current_node_id"]
        node_details = get_node_details(current_node_id)
        
        if not node_details:
            return jsonify({"error": "Invalid node"}), 400
        
        # Generate image URL with dynamic seed and enhanced prompt
        path_node_ids = game_state.get("path_history", [])
        sentiment_tally = game_state.get("sentiment_tally", {})
        choice_history = game_state.get("choice_history", [])
        last_choice = choice_history[-1] if choice_history else None
        
        base_seed = node_details.get("seed", 12345)
        dynamic_seed = get_dynamic_seed(base_seed, path_node_ids, session_id)
        
        path_tuples = [(node, game_state.get("sentiment_tally", {}).get(node, 0)) 
                       for node in path_node_ids]
        
        base_prompt = node_details.get("prompt", "")
        enhanced_prompt = enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id)
        
        # Create the image URL
        encoded_prompt = requests.utils.quote(enhanced_prompt)
        image_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}"
        
        # Personalize choices with variations except the first choice
        choices = node_details.get("choices", [])
        if choices and len(choices) > 0:
            # Keep a deep copy to avoid modifying the original
            choices = [choice.copy() for choice in choices]
            
            # Get user's personality traits from sessions or generate new ones
            if session_id not in user_sessions:
                user_sessions[session_id] = {}
            
            if 'personality_traits' not in user_sessions[session_id]:
                # Generate random personality traits for this user
                import random
                traits = ["cautious", "bold", "diplomatic", "direct", "curious", "practical", 
                          "optimistic", "pessimistic", "detailed", "concise"]
                user_sessions[session_id]['personality_traits'] = random.sample(traits, 3)
            
            user_traits = user_sessions[session_id]['personality_traits']
            
            # Get a hash from the session ID to make choices consistently unique per user
            session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
            
            # Personalize choices (except first one at the start node) with small variations
            for i, choice in enumerate(choices):
                # Skip first choice at start node to keep it consistent
                if current_node_id == "start" and i == 0:
                    continue
                    
                original_text = choice.get("text", "")
                
                # Adjective modifiers based on personality
                adjectives = {
                    "cautious": ["carefully", "cautiously", "deliberately"],
                    "bold": ["boldly", "bravely", "confidently"],
                    "diplomatic": ["politely", "respectfully", "graciously"],
                    "direct": ["directly", "straightforwardly", "bluntly"],
                    "curious": ["curiously", "inquisitively", "wonderingly"],
                    "practical": ["practically", "sensibly", "reasonably"],
                    "optimistic": ["hopefully", "optimistically", "eagerly"],
                    "pessimistic": ["warily", "skeptically", "doubtfully"],
                    "detailed": ["meticulously", "thoroughly", "carefully"],
                    "concise": ["simply", "briefly", "efficiently"]
                }
                
                # Get suitable adjectives for this user's personality
                suitable_adjectives = []
                for trait in user_traits:
                    if trait in adjectives:
                        suitable_adjectives.extend(adjectives[trait])
                
                if suitable_adjectives:
                    # Select a consistent adjective based on session and choice
                    adj_index = (session_hash + i) % len(suitable_adjectives)
                    selected_adj = suitable_adjectives[adj_index]
                    
                    # Insert the adjective into the choice text if it makes sense
                    # Identify the verb in the choice text
                    words = original_text.split()
                    # Simple heuristic: Look for verbs typical in choices
                    common_verbs = ["Take", "Go", "Explore", "Talk", "Help", "Ignore", "Follow", "Leave", 
                                   "Examine", "Search", "Ask", "Fight", "Run", "Hide", "Climb", "Jump"]
                    
                    for j, word in enumerate(words):
                        if word in common_verbs and j < len(words) - 1:
                            # Insert adjective after the verb
                            modified_text = " ".join(words[:j+1]) + " " + selected_adj + " " + " ".join(words[j+1:])
                            choice["text"] = modified_text
                            break
        
        # Get the score from the game state, ensuring consistency in property names
        score = game_state.get("score", 0)
        
        # Prepare the response
        response_data = {
            "situation": node_details.get("situation", ""),
            "is_end": node_details.get("is_end", False),
            "ending_category": node_details.get("ending_category", ""),
            "choices": choices,  # Use personalized choices
            "image_url": image_url,
            "image_prompt": enhanced_prompt,
            "current_score": score,  # Use consistent name for frontend
            "score": score  # Include both for backward compatibility
        }
        
        # Generate special end-game content if this is an end node
        if node_details.get("is_end", False):
            manga_prompt = f"Manga style, story summary of {enhanced_prompt}"
            encoded_manga_prompt = requests.utils.quote(manga_prompt)
            response_data["manga_image_url"] = f"{POLLINATIONS_BASE_URL}{encoded_manga_prompt}"
            
            summary_prompt = f"Fantasy book cover, hero's journey, {enhanced_prompt}"
            encoded_summary_prompt = requests.utils.quote(summary_prompt)
            response_data["summary_image_url"] = f"{POLLINATIONS_BASE_URL}{encoded_summary_prompt}"
        
        # Create response with cookie
        response = make_response(jsonify(response_data))
        response.set_cookie('session_id', session_id, max_age=86400*30)  # 30 days
        return response
        
    except Exception as e:
        print(f"Error in get_current_state: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/choice', methods=['POST'])
def make_choice():
    try:
        data = request.json
        choice_index = data.get('choice_index')
        
        if choice_index is None:
            return jsonify({"error": "Missing choice_index"}), 400
        
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"error": "No session found"}), 400
        
        # Get the user's game state
        if session_id not in user_sessions or 'state' not in user_sessions[session_id]:
            return jsonify({"error": "No game in progress"}), 400
            
        game_state = user_sessions[session_id]['state']
        current_node_id = game_state["current_node_id"]
        
        # Get current node details
        node_details = get_node_details(current_node_id)
        if not node_details:
            return jsonify({"error": "Invalid current node"}), 400
            
        # Validate choice index
        if not node_details.get("choices") or choice_index >= len(node_details["choices"]):
            return jsonify({"error": "Invalid choice index"}), 400
            
        # Get the chosen choice
        choice = node_details["choices"][choice_index]
        
        # Special processing for dynamic ending calculation
        next_node_id = choice.get("next_node")
        if next_node_id == "_calculate_end":
            # Calculate ending based on score and sentiment
            score = game_state.get("score", 0)
            sentiment_tally = game_state.get("sentiment_tally", {})
            
            # Count positive vs negative tags
            positive_count = sum(sentiment_tally.get(tag, 0) for tag in 
                             ["kind", "adventurous", "bold", "wise", "resourceful"])
            negative_count = sum(sentiment_tally.get(tag, 0) for tag in 
                             ["selfish", "cautious", "stubborn"])
            
            # Determine ending based on score and sentiment balance
            if score >= 5 and positive_count > negative_count:
                next_node_id = "generic_good_ending"
            elif score <= 0 or negative_count > positive_count:
                next_node_id = "generic_bad_ending"
            else:
                next_node_id = "generic_neutral_ending"
                
            # Create a unique ending variation based on the session ID
            # This ensures each user gets a different ending
            custom_endings = {
                "generic_good_ending": [
                    "heroic_savior_ending", "wise_mage_ending", "forest_guardian_ending"
                ],
                "generic_neutral_ending": [
                    "peaceful_traveler_ending", "forest_explorer_ending", "merchant_ending"
                ],
                "generic_bad_ending": [
                    "lost_soul_ending", "cursed_wanderer_ending", "forest_prisoner_ending"
                ]
            }
            
            if next_node_id in custom_endings:
                # Use the session ID to pick a specific variant
                session_hash = int(hashlib.md5(session_id.encode()).hexdigest(), 16)
                ending_options = custom_endings[next_node_id]
                ending_index = session_hash % len(ending_options)
                custom_ending = ending_options[ending_index]
                
                # If we have this ending defined, use it instead
                if custom_ending in story_nodes:
                    next_node_id = custom_ending
        
        # Update game state
        game_state["current_node_id"] = next_node_id
        game_state["path_history"].append(next_node_id)
        
        # Update score
        score_modifier = choice.get("score_modifier", 0)
        game_state["score"] += score_modifier
        
        # Update sentiment tally
        tag = choice.get("tag")
        if tag:
            if tag not in game_state["sentiment_tally"]:
                game_state["sentiment_tally"][tag] = 0
            game_state["sentiment_tally"][tag] += 1
        
        # Record this choice
        game_state["choice_history"].append({
            "from_node": current_node_id,
            "choice_index": choice_index,
            "choice_text": choice.get("text", ""),
            "tag": tag
        })
        
        # Save the updated state
        user_sessions[session_id]['state'] = game_state
        
        # Return the new state
        return get_current_state()
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset_game():
    try:
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            # Generate a new session ID
            import secrets
            session_id = hashlib.md5(f"{time.time()}-{secrets.token_hex(8)}".encode()).hexdigest()
        
        # Reset the game state for this session
        reset_game_state(session_id)
        
        # Instead of just returning success message, return the actual game state
        # by calling the get_current_state function
        return get_current_state()
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/share-image', methods=['GET'])
def generate_share_image():
    try:
        # Get user's session ID from cookies
        session_id = request.cookies.get('session_id')
        if not session_id:
            return jsonify({"error": "No session found"}), 400
        
        # Get the user's game state
        if session_id not in user_sessions or 'state' not in user_sessions[session_id]:
            return jsonify({"error": "No game in progress"}), 400
            
        game_state = user_sessions[session_id]['state']
        
        # Get score and ending information
        score = game_state.get("score", 0)
        current_node_id = game_state.get("current_node_id", "")
        node_details = get_node_details(current_node_id)
        
        if not node_details:
            return jsonify({"error": "Invalid node"}), 400
            
        # Check if the game has ended
        if not node_details.get("is_end", False):
            return jsonify({"error": "Game has not ended yet"}), 400
            
        # Get the ending category
        ending_category = node_details.get("ending_category", "Adventure Complete")
        
        # Generate the specific manga image prompt with user's journey details
        path_node_ids = game_state.get("path_history", [])
        sentiment_tally = game_state.get("sentiment_tally", {})
        
        # Generate main traits from sentiment tally
        main_traits = []
        for tag, count in sentiment_tally.items():
            if count > 0:
                main_traits.append(tag)
        
        # Select top 3 traits if we have that many
        top_traits = main_traits[:3] if len(main_traits) >= 3 else main_traits
        traits_text = ", ".join(top_traits)
        
        # Create a personalized story description
        personality = f"a {traits_text} adventurer" if traits_text else "an adventurer"
        
        # Generate image URL with enhanced prompt
        base_prompt = node_details.get("prompt", "")
        path_tuples = [(node, sentiment_tally.get(node, 0)) for node in path_node_ids]
        choice_history = game_state.get("choice_history", [])
        last_choice = choice_history[-1] if choice_history else None
        
        # Get dynamic seed
        base_seed = node_details.get("seed", 12345)
        dynamic_seed = get_dynamic_seed(base_seed, path_node_ids, session_id)
        
        # Generate enhanced prompt for manga-style image
        enhanced_prompt = enhance_prompt(base_prompt, path_tuples, sentiment_tally, last_choice, session_id)
        
        # Create manga-style panel layout prompt
        share_manga_prompt = f"Manga style, 4-panel comic strip telling the story of {personality} who achieved the '{ending_category}' ending with a score of {score}, {enhanced_prompt}, clean white background with title 'Mystic Forest Adventure' and score displayed"
        
        # URL encode the prompt
        encoded_manga_prompt = requests.utils.quote(share_manga_prompt)
        share_image_url = f"{POLLINATIONS_BASE_URL}{encoded_manga_prompt}"
        
        # Return the share image URL
        return jsonify({
            "share_image_url": share_image_url,
            "score": score,
            "ending_category": ending_category
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Vercel expects the app object for Python runtimes
# The file is usually named index.py inside an 'api' folder
# If running locally:
if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')