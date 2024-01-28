import stripe
from dotenv import dotenv_values

config = dotenv_values()
stripe.api_key = config['STRIPE_SECRET_KEY']
