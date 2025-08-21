from flask import Flask, render_template, request, jsonify, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'shockbot_secret'
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['ShockAbsorber']
collection = db['absorbers']

# Valid inputs
VALID_STROKES = [25, 50, 70, 75, 100, 125, 127, 150, 165, 200]
VALID_ABSORBERS = [1, 2, 3, 4]
VALID_CURRENCIES = ['INR', 'USD']

# State machine for conversation
STATES = [
    'ask_scenario', 'ask_mass', 'ask_velocity', 'ask_cycles', 'ask_force',
    'ask_stroke', 'ask_absorbers', 'ask_currency', 'calculate'
]

@app.route('/')
def index():
    session.clear()
    session['state'] = 'ask_scenario'
    session['inputs'] = {}
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message').strip()
    current_state = session.get('state', 'ask_scenario')
    response = ''
    next_state = current_state

    if user_input.lower() == 'restart':
        session.clear()
        session['state'] = 'ask_scenario'
        session['inputs'] = {}
        return jsonify({'response': 'Restarted. Choose a scenario: 1. Mass with Propelling Force'})

    if current_state == 'ask_scenario':
        if user_input == '1':
            session['inputs']['scenario'] = 'Mass with Propelling Force'
            response = 'Enter mass (kg or tonne):'
            next_state = 'ask_mass'
        else:
            response = 'Please select "1" for Mass with Propelling Force.'
    
    elif current_state == 'ask_mass':
        try:
            mass = float(user_input.split()[0])
            unit = user_input.split()[1] if len(user_input.split()) > 1 else 'kg'
            if unit not in ['kg', 'tonne']:
                response = 'Unit must be kg or tonne. Try again:'
            else:
                session['inputs']['mass'] = mass
                session['inputs']['mass_unit'] = unit
                response = 'Enter velocity (m/sec or m/min):'
                next_state = 'ask_velocity'
        except:
            response = 'Invalid mass. Enter a number (e.g., "50 kg"):'

    elif current_state == 'ask_velocity':
        try:
            velocity = float(user_input.split()[0])
            unit = user_input.split()[1] if len(user_input.split()) > 1 else 'm/sec'
            if unit not in ['m/sec', 'm/min']:
                response = 'Unit must be m/sec or m/min. Try again:'
            else:
                session['inputs']['velocity'] = velocity
                session['inputs']['velocity_unit'] = unit
                response = 'Enter cycles per hour:'
                next_state = 'ask_cycles'
        except:
            response = 'Invalid velocity. Enter a number (e.g., "2 m/sec"):'

    elif current_state == 'ask_cycles':
        try:
            cycles = float(user_input)
            if cycles <= 0:
                response = 'Cycles must be positive. Try again:'
            else:
                session['inputs']['cycles'] = cycles
                response = 'Enter force (N):'
                next_state = 'ask_force'
        except:
            response = 'Invalid cycles. Enter a number:'

    elif current_state == 'ask_force':
        try:
            force = float(user_input)
            if force <= 0:
                response = 'Force must be positive. Try again:'
            else:
                session['inputs']['force'] = force
                response = 'Select stroke (25, 50, 70, 75, 100, 125, 127, 150, 165, 200 mm):'
                next_state = 'ask_stroke'
        except:
            response = 'Invalid force. Enter a number:'

    elif current_state == 'ask_stroke':
        try:
            stroke = float(user_input)
            if stroke not in VALID_STROKES:
                response = f'Stroke must be one of {VALID_STROKES}. Try again:'
            else:
                session['inputs']['stroke'] = stroke
                response = 'Select number of shock absorbers (1, 2, 3, 4):'
                next_state = 'ask_absorbers'
        except:
            response = 'Invalid stroke. Enter a number:'

    elif current_state == 'ask_absorbers':
        try:
            absorbers = int(user_input)
            if absorbers not in VALID_ABSORBERS:
                response = f'Number of absorbers must be one of {VALID_ABSORBERS}. Try again:'
            else:
                session['inputs']['absorbers'] = absorbers
                response = 'Choose currency (INR or USD):'
                next_state = 'ask_currency'
        except:
            response = 'Invalid number. Enter 1, 2, 3, or 4:'

    elif current_state == 'ask_currency':
        currency = user_input.upper()
        if currency not in VALID_CURRENCIES:
            response = 'Currency must be INR or USD. Try again:'
        else:
            session['inputs']['currency'] = currency
            session['inputs']['min_temperature'] = 60  # Default
            next_state = 'calculate'
            response = calculate_and_recommend()

    session['state'] = next_state
    return jsonify({'response': response})

def calculate_and_recommend():
    inputs = session['inputs']
    mass = inputs['mass'] * 1000 if inputs['mass_unit'] == 'tonne' else inputs['mass']
    velocity = inputs['velocity'] / 60 if inputs['velocity_unit'] == 'm/min' else inputs['velocity']
    
    # Placeholder calculations
    calculations = {
        'kinetic_energy': 0.5 * mass * velocity ** 2,
        'potential_energy': inputs['force'] * (inputs['stroke'] / 1000),
        'total_energy': (0.5 * mass * velocity ** 2) + (inputs['force'] * (inputs['stroke'] / 1000)),
        'energy_per_hour': ((0.5 * mass * velocity ** 2) + (inputs['force'] * (inputs['stroke'] / 1000))) * inputs['cycles'],
        'impact_velocity': velocity,
        'emass_min': (0.5 * mass * velocity ** 2) / (velocity ** 2)
    }

    # Mock MongoDB query
    try:
        result = collection.find_one({'inputs.stroke': inputs['stroke']})
        recommendations = result.get('recommendations', ['Model X', 'Model Y']) if result else ['Mock Model']
    except Exception as e:
        recommendations = ['Mock Model']

    # Store in MongoDB
    try:
        collection.insert_one({
            'scenario': inputs['scenario'],
            'inputs': inputs,
            'calculations': calculations,
            'recommendations': recommendations
        })
    except:
        pass  # Ignore MongoDB errors for demo

    return (f"Recommended absorbers: {', '.join(recommendations)}\n"
            f"Calculations: Kinetic Energy: {calculations['kinetic_energy']:.2f} kg, "
            f"Potential Energy: {calculations['potential_energy']:.2f} Nm, "
            f"Total Energy: {calculations['total_energy']:.2f} Nm, "
            f"Energy per Hour: {calculations['energy_per_hour']:.2f} Nm/hr, "
            f"Impact Velocity: {calculations['impact_velocity']:.2f} m/s, "
            f"Emass min: {calculations['emass_min']:.2f} kg")

if __name__ == '__main__':
    app.run(debug=True)