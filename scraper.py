import requests
import html
import os
import re
import time
import threading  # 👈 Background processing ke liye
from flask import Flask  # 👈 Fake Website ke liye
import json
import random
from bs4 import BeautifulSoup # 👈 Breezy ke liye ye zaroori hai
from datetime import datetime, timedelta, timezone
from dateutil import parser
from supabase import create_client
from google import genai
from google.genai import types

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
KEYS_STRING = os.environ.get("GEMINI_API_KEYS") # Comma separated string

# Keys List banao
if KEYS_STRING:
    GEMINI_API_KEYS = [k.strip() for k in KEYS_STRING.split(",") if k.strip()]
else:
    GEMINI_API_KEYS = []
    print("⚠️ Warning: No Gemini Keys Found in Environment!")

current_key_index = 0
DAYS_TO_LOOK_BACK = 30

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase!")
except Exception as e:
    print(f"❌ Supabase Connection Failed: {e}")
    exit()

# --- 2. TARGET COMPANIES (Expanded List) ---
# Format: ("Company Name", "Board ID / Domain", "Type")
# --- 3. EXPANDED TARGET COMPANIES (GOD MODE LIST) ---
TARGETS = [
    # =========================================================
    # 🇵🇰 PAKISTAN & MENA EXPANSION

    # =========================================================
    # 💰 GLOBAL FINTECH & CRYPTO
    # =========================================================
    ("Coinbase", "coinbase", "greenhouse"),
    ("Binance", "binance", "greenhouse"),
    ("Kraken", "kraken", "lever"),
    ("Ripple", "ripple", "greenhouse"),
    ("Chainlink", "chainlink", "greenhouse"),
    ("Consensys", "consensys", "greenhouse"),
    ("Block (Square)", "block", "greenhouse"),
    ("Robinhood", "robinhood", "greenhouse"),
    ("Revolut", "revolut", "greenhouse"),
    ("Wise", "wise", "greenhouse"),
    ("Chime", "chime", "greenhouse"),
    ("Nubank", "nubank", "greenhouse"),
    ("Monzo", "monzo", "greenhouse"),
    ("Plaid", "plaid", "greenhouse"),
    ("Gemini", "gemini", "greenhouse"),
    ("Fireblocks", "fireblocks", "greenhouse"),
    ("Ledger", "ledger", "greenhouse"),
    ("Metamask", "metamask", "greenhouse"),
    ("Phantom", "phantom", "greenhouse"),
    ("Uniswap", "uniswap", "greenhouse"),
    ("Aave", "aave", "greenhouse"),
    ("Compound", "compound", "greenhouse"),
    ("Lido", "lido", "greenhouse"),
    ("Arbitrum", "arbitrum", "greenhouse"),
    ("Optimism", "optimism", "greenhouse"),
    ("zkSync", "zksync", "greenhouse"),
    ("Circle", "circle", "greenhouse"),
    ("Paxos", "paxos", "greenhouse"),
    ("Tether", "tether", "greenhouse"),
    ("OKX", "okx", "greenhouse"),
    ("Bybit", "bybit", "greenhouse"),
    ("Adyen", "adyen", "greenhouse"),
    ("Checkout.com", "checkout", "greenhouse"),
    ("Klarna", "klarna", "lever"),
    ("Afterpay", "afterpay", "greenhouse"),
    ("Affirm", "affirm", "greenhouse"),
    ("SoFi", "sofi", "greenhouse"),
    ("Better.com", "better", "greenhouse"),
    ("Brex", "brex", "greenhouse"),
    ("Ramp", "ramp", "ashby"),
    ("Navan", "navan", "greenhouse"),
    ("Toast", "toast", "greenhouse"),
    ("Marqeta", "marqeta", "greenhouse"),
    ("Carta", "carta", "ashby"),
    ("Bill.com", "bill", "greenhouse"),
    ("Expensify", "expensify", "greenhouse"),
    ("Gusto", "gusto", "greenhouse"),
    ("Rippling", "rippling", "greenhouse"),

    # =========================================================
    # 🛡️ CYBERSECURITY
    # =========================================================
    ("Okta", "okta", "greenhouse"),
    ("Auth0", "auth0", "greenhouse"),
    ("Cloudflare", "cloudflare", "greenhouse"),
    ("CrowdStrike", "crowdstrike", "greenhouse"),
    ("Zscaler", "zscaler", "greenhouse"),
    ("SentinelOne", "sentinelone", "greenhouse"),
    ("Palo Alto Networks", "paloaltonetworks", "workday"),
    ("Fortinet", "fortinet", "greenhouse"),
    ("Check Point", "checkpoint", "greenhouse"),
    ("FireEye", "fireeye", "greenhouse"),
    ("Splunk", "splunk", "greenhouse"),
    ("Tanium", "tanium", "greenhouse"),
    ("Netskope", "netskope", "greenhouse"),
    ("Illumio", "illumio", "greenhouse"),
    ("Vanta", "vanta", "ashby"),
    ("Drata", "drata", "greenhouse"),
    ("Secureframe", "secureframe", "greenhouse"),
    ("Snyk", "snyk", "greenhouse"),
    ("Wiz", "wiz", "greenhouse"),
    ("Lacework", "lacework", "greenhouse"),
    ("Orca Security", "orca", "greenhouse"),
    ("Aura", "aura", "greenhouse"),
    ("1Password", "1password", "lever"),
    ("Dashlane", "dashlane", "greenhouse"),
    ("Keeper", "keeper", "greenhouse"),
    ("Nord Security", "nord", "greenhouse"),
    ("HackerOne", "hackerone", "greenhouse"),
    ("Bugcrowd", "bugcrowd", "greenhouse"),
    ("Synack", "synack", "greenhouse"),

    # =========================================================
    # 🏗️ INFRASTRUCTURE & DEVTOOLS
    # =========================================================
    ("Docker", "docker", "greenhouse"),
    ("HashiCorp", "hashicorp", "greenhouse"),
    ("Confluent", "confluent", "greenhouse"),
    ("Elastic", "elastic", "greenhouse"),
    ("MongoDB", "mongodb", "greenhouse"),
    ("Redis", "redis", "greenhouse"),
    ("Neo4j", "neo4j", "greenhouse"),
    ("Cockroach Labs", "cockroachlabs", "greenhouse"),
    ("PlanetScale", "planetscale", "greenhouse"),
    ("Neon", "neon", "ashby"),
    ("Upstash", "upstash", "ashby"),
    ("Checkly", "checkly", "ashby"),
    ("Aiven", "aiven", "greenhouse"),
    ("Grafana Labs", "grafana", "greenhouse"),
    ("Prometheus", "prometheus", "greenhouse"),
    ("Datadog", "datadog", "greenhouse"),
    ("New Relic", "newrelic", "greenhouse"),
    ("Dynatrace", "dynatrace", "greenhouse"),
    ("AppDynamics", "appdynamics", "greenhouse"),
    ("Sentry", "sentry", "greenhouse"),
    ("GitLab", "gitlab", "greenhouse"),
    ("Bitbucket", "bitbucket", "greenhouse"),
    ("CircleCI", "circleci", "greenhouse"),
    ("Travis CI", "travisci", "greenhouse"),
    ("Buildkite", "buildkite", "greenhouse"),
    ("GitHub", "github", "greenhouse"),
    ("DigitalOcean", "digitalocean", "greenhouse"),
    ("Linode", "linode", "greenhouse"),
    ("Vercel", "vercel", "ashby"),
    ("Netlify", "netlify", "greenhouse"),
    ("Fastly", "fastly", "greenhouse"),
    ("Akamai", "akamai", "workday"),

    # =========================================================
    # 🎮 GAME DEVELOPMENT
    # =========================================================
    ("Epic Games", "epicgames", "greenhouse"),
    ("Unity", "unity", "greenhouse"),
    ("Roblox", "roblox", "greenhouse"),
    ("Riot Games", "riotgames", "greenhouse"),
    ("Activision Blizzard", "activision", "greenhouse"),
    ("Electronic Arts", "ea", "greenhouse"),
    ("Ubisoft", "ubisoft", "smartrecruiters"),
    ("Take-Two", "taketwo", "greenhouse"),
    ("Zynga", "zynga", "greenhouse"),
    ("Niantic", "niantic", "greenhouse"),
    ("Supercell", "supercell", "greenhouse"),
    ("King", "king", "greenhouse"),
    ("Playrix", "playrix", "greenhouse"),
    ("Voodoo", "voodoo", "greenhouse"),
    ("Moon Active", "moonactive", "greenhouse"),
    ("Discord", "discord", "greenhouse"),
    ("Twitch", "twitch", "greenhouse"),
    ("Steam (Valve)", "valve", "greenhouse"),
    ("CD Projekt Red", "cdprojekt", "greenhouse"),
    ("Rockstar Games", "rockstar", "greenhouse"),

    # =========================================================
    # 🏥 HEALTHTECH & BIOTECH
    # =========================================================
    ("Verily", "verily", "greenhouse"),
    ("Flatiron Health", "flatiron", "greenhouse"),
    ("Oscar Health", "oscar", "greenhouse"),
    ("Ro", "ro", "greenhouse"),
    ("Hims & Hers", "hims", "greenhouse"),
    ("Headspace", "headspace", "greenhouse"),
    ("Calm", "calm", "greenhouse"),
    ("Modern Health", "modernhealth", "greenhouse"),
    ("Lyra Health", "lyra", "greenhouse"),
    ("BetterHelp", "betterhelp", "greenhouse"),
    ("Talkspace", "talkspace", "greenhouse"),
    ("Curefit", "curefit", "greenhouse"),
    ("HealthifyMe", "healthifyme", "greenhouse"),
    ("Oura", "oura", "greenhouse"),
    ("Whoop", "whoop", "greenhouse"),
    ("Noom", "noom", "greenhouse"),
    ("MyFitnessPal", "myfitnesspal", "greenhouse"),
    ("Color", "color", "greenhouse"),
    ("23andMe", "23andme", "greenhouse"),
    ("Ancestry", "ancestry", "greenhouse"),
    ("BenevolentAI", "benevolent", "greenhouse"),
    ("Recursion", "recursion", "greenhouse"),
    ("Insilico Medicine", "insilico", "greenhouse"),

    # =========================================================
    # 🎓 EDTECH
    # =========================================================
    ("Udemy", "udemy", "greenhouse"),
    ("Coursera", "coursera", "greenhouse"),
    ("Udacity", "udacity", "greenhouse"),
    ("Pluralsight", "pluralsight", "greenhouse"),
    ("Skillshare", "skillshare", "greenhouse"),
    ("MasterClass", "masterclass", "greenhouse"),
    ("Khan Academy", "khanacademy", "greenhouse"),
    ("Duolingo", "duolingo", "greenhouse"),
    ("Babbel", "babbel", "greenhouse"),
    ("Rosetta Stone", "rosettastone", "greenhouse"),
    ("Quizlet", "quizlet", "greenhouse"),
    ("Chegg", "chegg", "greenhouse"),
    ("Course Hero", "coursehero", "greenhouse"),
    ("Grammarly", "grammarly", "greenhouse"),
    ("Turnitin", "turnitin", "greenhouse"),
    ("Instructure", "instructure", "greenhouse"),
    ("Blackboard", "blackboard", "greenhouse"),
    ("ClassDojo", "classdojo", "greenhouse"),
    ("Remind", "remind", "greenhouse"),

    # =========================================================
    # 🛍️ E-COMMERCE & LOGISTICS
    # =========================================================
    ("Amazon", "amazon", "internal"),
    ("eBay", "ebay", "workday"),
    ("Shopify", "shopify", "smartrecruiters"),
    ("Magento (Adobe)", "magento", "workday"),
    ("BigCommerce", "bigcommerce", "greenhouse"),
    ("WooCommerce", "woocommerce", "greenhouse"),
    ("Etsy", "etsy", "greenhouse"),
    ("Wayfair", "wayfair", "greenhouse"),
    ("Zulily", "zulily", "greenhouse"),
    ("Wish", "wish", "greenhouse"),
    ("StockX", "stockx", "greenhouse"),
    ("GOAT", "goat", "greenhouse"),
    ("Farfetch", "farfetch", "greenhouse"),
    ("Instacart", "instacart", "greenhouse"),
    ("DoorDash", "doordash", "greenhouse"),
    ("Uber Eats", "ubereats", "greenhouse"),
    ("Gopuff", "gopuff", "greenhouse"),
    ("Deliveroo", "deliveroo", "greenhouse"),
    ("Just Eat Takeaway", "justeat", "greenhouse"),
    ("HelloFresh", "hellofresh", "greenhouse"),
    ("Blue Apron", "blueapron", "greenhouse"),
    ("Flexport", "flexport", "greenhouse"),
    ("Deliverr", "deliverr", "greenhouse"),
    ("ShipBob", "shipbob", "greenhouse"),
    ("Lalamove", "lalamove", "greenhouse"),
    ("Delhivery", "delhivery", "greenhouse"),

    # =========================================================
    # 🌍 MORE GLOBAL GIANTS & FAANG
    # =========================================================
    ("Google", "google", "internal"),
    ("Meta", "meta", "internal"),
    ("Apple", "apple", "internal"),
    ("Microsoft", "microsoft", "internal"),
    ("Netflix", "netflix", "internal"),
    ("Tesla", "tesla", "internal"),
    ("SpaceX", "spacex", "internal"),
    ("Twitter (X)", "twitter", "internal"),
    ("ByteDance (TikTok)", "bytedance", "internal"),
    ("NVIDIA", "nvidia", "internal"),
    ("Intel", "intel", "workday"),
    ("AMD", "amd", "workday"),
    ("Qualcomm", "qualcomm", "workday"),
    ("Broadcom", "broadcom", "workday"),
    ("Samsung", "samsung", "internal"),
    ("Sony", "sony", "internal"),
    ("Tencent", "tencent", "internal"),
    ("Alibaba", "alibaba", "internal"),
    ("Baidu", "baidu", "internal"),

    
    ("1Password", "1password", "lever"),
    ("Abnormal Security", "abnormalsecurity", "greenhouse"),
    ("ActionIQ", "actioniq", "greenhouse"),
    ("ActiveCampaign", "activecampaign", "greenhouse"),
    ("Ada Support", "ada", "greenhouse"),
    ("Adallom", "adallom", "greenhouse"),
    ("Addepar", "addepar", "greenhouse"),
    ("Adept", "adept", "greenhouse"),
    ("AdmitHub", "admithub", "greenhouse"),
    ("Afterpay", "afterpay", "greenhouse"),
    ("Airbyte", "airbyte", "greenhouse"),
    ("Aircall", "aircall", "greenhouse"),
    ("Airtable", "airtable", "greenhouse"),
    ("Airwallex", "airwallex", "greenhouse"),
    ("Algolia", "algolia", "greenhouse"),
    ("Alation", "alation", "greenhouse"),
    ("AllTrails", "alltrails", "greenhouse"),
    ("Alogent", "alogent", "greenhouse"),
    ("AlphaSense", "alphasense", "greenhouse"),
    ("Alt", "alt", "greenhouse"),
    ("Alteryx", "alteryx", "greenhouse"),
    ("Altos Labs", "altoslabs", "greenhouse"),
    ("Amanotes", "amanotes", "greenhouse"),
    ("Ambition", "ambition", "greenhouse"),
    ("Amino", "amino", "greenhouse"),
    ("Amplitude", "amplitude", "greenhouse"),
    ("Anduril", "anduril", "greenhouse"),
    ("Anyscale", "anyscale", "greenhouse"),
    ("AppDirect", "appdirect", "greenhouse"),
    ("AppFolio", "appfolio", "greenhouse"),
    ("AppLover", "applover", "greenhouse"),
    ("AppNexus", "appnexus", "greenhouse"),
    ("Applied Intuition", "appliedintuition", "greenhouse"),
    ("AppLovin", "applovin", "greenhouse"),
    ("Argyle", "argyle", "greenhouse"),
    ("Armis", "armis", "greenhouse"),
    ("Arrival", "arrival", "greenhouse"),
    ("Articulate", "articulate", "greenhouse"),
    ("Assembled", "assembled", "ashby"),
    ("Astriagraph", "astriagraph", "greenhouse"),
    ("Atlan", "atlan", "greenhouse"),
    ("Atlas", "atlas", "ashby"),
    ("Attentive", "attentive", "greenhouse"),
    ("Aura", "aura", "greenhouse"),
    ("Automatic", "automatic", "greenhouse"),
    ("Avaamo", "avaamo", "greenhouse"),
    ("Avantis", "avantis", "greenhouse"),
    ("Aviatrix", "aviatrix", "greenhouse"),
    ("Axios", "axios", "greenhouse"),
    ("Back Market", "backmarket", "greenhouse"),
    ("BambooHR", "bamboohr", "greenhouse"),
    ("Bandwidth", "bandwidth", "greenhouse"),
    ("BarkBox", "barkbox", "greenhouse"),
    ("Beacons", "beacons", "ashby"),
    ("Beamery", "beamery", "greenhouse"),
    ("Bellhop", "bellhop", "greenhouse"),
    ("Benchling", "benchling", "greenhouse"),
    ("Benefitfocus", "benefitfocus", "greenhouse"),
    ("BetterUp", "betterup", "greenhouse"),
    ("BigID", "bigid", "greenhouse"),
    ("BitPanda", "bitpanda", "greenhouse"),
    ("Blameless", "blameless", "greenhouse"),
    ("Blaze", "blaze", "greenhouse"),
    ("Blockdaemon", "blockdaemon", "greenhouse"),
    ("Bluecore", "bluecore", "greenhouse"),
    ("Bofigo", "bofigo", "greenhouse"),
    ("Bolt", "bolt", "greenhouse"),
    ("Boom Supersonic", "boom", "greenhouse"),
    ("Branch", "branch", "greenhouse"),
    ("Braze", "braze", "greenhouse"),
    ("Bread", "bread", "greenhouse"),
    ("Brightflow", "brightflow", "greenhouse"),
    ("BrowserStack", "browserstack", "greenhouse"),
    ("Buffer", "buffer", "greenhouse"),
    ("Builder.io", "builder", "ashby"),
    ("Burrow", "burrow", "greenhouse"),
    ("Byteboard", "byteboard", "greenhouse"),
    ("Cado Security", "cado", "greenhouse"),
    ("Cajoo", "cajoo", "greenhouse"),
    ("Calendar", "calendar", "greenhouse"),
    ("Camunda", "camunda", "greenhouse"),
    ("Canopy", "canopy", "greenhouse"),
    ("Canvas", "canvas", "greenhouse"),
    ("Capitolis", "capitolis", "greenhouse"),
    ("Capmo", "capmo", "greenhouse"),
    ("Capsule", "capsule", "greenhouse"),
    ("Carbon Health", "carbonhealth", "greenhouse"),
    ("Cargurus", "cargurus", "greenhouse"),
    ("Cargo", "cargo", "greenhouse"),
    ("BitKraft", "bitkraft", "greenhouse"),
    ("Cart.com", "cart", "greenhouse"),
    ("Castos", "castos", "greenhouse"),
    ("Catch", "catch", "greenhouse"),
    ("Cedar", "cedar", "greenhouse"),
    ("Celestial AI", "celestial", "greenhouse"),
    ("Celo", "celo", "greenhouse"),
    ("Census", "census", "ashby"),
    ("Chainalysis", "chainalysis", "greenhouse"),
    ("Change.org", "change", "greenhouse"),
    ("Chargebee", "chargebee", "greenhouse"),
    ("Chariot", "chariot", "greenhouse"),
    ("Check", "check", "greenhouse"),
    ("Checkout.com", "checkout", "greenhouse"),
    ("Checkr", "checkr", "greenhouse"),
    ("Chef", "chef", "greenhouse"),
    ("Chili Piper", "chilipiper", "greenhouse"),
    ("Chorus.ai", "chorus", "greenhouse"),
    ("ChowNow", "chownow", "greenhouse"),
    ("Circle", "circle", "greenhouse"),
    ("Citymapper", "citymapper", "greenhouse"),
    ("Clarify", "clarify", "greenhouse"),
    ("Clari", "clari", "greenhouse"),
    ("Clearbit", "clearbit", "greenhouse"),
    ("Clearcover", "clearcover", "greenhouse"),
    ("Cleo", "cleo", "greenhouse"),
    ("ClickUp", "clickup", "greenhouse"),
    ("Clockwise", "clockwise", "greenhouse"),
    ("Close", "close", "greenhouse"),
    ("Cloudinary", "cloudinary", "greenhouse"),
    ("Clutch", "clutch", "greenhouse"),
    ("Coalition", "coalition", "greenhouse"),
    ("Codecov", "codecov", "greenhouse"),
    ("Codacy", "codacy", "greenhouse"),
    ("Coda", "coda", "greenhouse"),
    ("Codeclimate", "codeclimate", "greenhouse"),
    ("Coder", "coder", "greenhouse"),
    ("Cognite", "cognite", "greenhouse"),
    ("CoinTracker", "cointracker", "ashby"),
    ("Collective", "collective", "greenhouse"),
    ("Collibra", "collibra", "greenhouse"),
    ("Comet", "comet", "greenhouse"),
    ("Common Paper", "commonpaper", "ashby"),
    ("Composer", "composer", "ashby"),
    ("Compass", "compass", "greenhouse"),
    ("Conductor", "conductor", "greenhouse"),
    ("Contentful", "contentful", "greenhouse"),
    ("Context.ai", "context", "ashby"),
    ("Contrast Security", "contrast", "greenhouse"),
    ("Convoy", "convoy", "greenhouse"),
    ("Copper", "copper", "greenhouse"),
    ("Copy.ai", "copyai", "greenhouse"),
    ("Cora", "cora", "greenhouse"),
    ("Cordial", "cordial", "greenhouse"),
    ("CoreOS", "coreos", "greenhouse"),
    ("CorgiAI", "corgi", "ashby"),
    ("Cornerstone", "cornerstone", "greenhouse"),
    ("Couchbase", "couchbase", "greenhouse"),
    ("Counterpart", "counterpart", "greenhouse"),
    ("CoverWallet", "coverwallet", "greenhouse"),
    ("Cradle", "cradle", "ashby"),
    ("Craft", "craft", "greenhouse"),
    ("Crane", "crane", "greenhouse"),
    ("Crazy Egg", "crazyegg", "greenhouse"),
    ("Credibly", "credibly", "greenhouse"),
    ("Credit Karma", "creditkarma", "greenhouse"),
    ("Cresta", "cresta", "greenhouse"),
    ("Crisp", "crisp", "greenhouse"),
    ("Crossbeam", "crossbeam", "greenhouse"),
    ("Crucible", "crucible", "greenhouse"),
    ("Crunchbase", "crunchbase", "greenhouse"),
    ("Cullinan Oncology", "cullinan", "greenhouse"),
    ("Culture Amp", "cultureamp", "greenhouse"),
    ("Curefit", "curefit", "greenhouse"),
    ("Curve", "curve", "greenhouse"),
    ("Customer.io", "customerio", "greenhouse"),
    ("Cypress", "cypress", "greenhouse"),
    ("Cybereason", "cybereason", "greenhouse"),
    ("Cybergrants", "cybergrants", "greenhouse"),
    ("D-ID", "d-id", "greenhouse"),
    ("Daily.co", "daily", "ashby"),
    ("Dailymotion", "dailymotion", "greenhouse"),
    ("Darktrace", "darktrace", "greenhouse"),
    ("Dashlane", "dashlane", "greenhouse"),
    ("DataRobot", "datarobot", "greenhouse"),
    ("Databricks", "databricks", "greenhouse"),
    ("Datadog", "datadog", "greenhouse"),
    ("Dataiku", "dataiku", "greenhouse"),
    ("Dataloop", "dataloop", "greenhouse"),
    ("Datastax", "datastax", "greenhouse"),
    ("Datazoom", "datazoom", "greenhouse"),
    ("Dave", "dave", "greenhouse"),
    ("Decent", "decent", "greenhouse"),
    ("Decimal", "decimal", "ashby"),
    ("DeepL", "deepl", "greenhouse"),
    ("Deepgram", "deepgram", "greenhouse"),
    ("Deepwatch", "deepwatch", "greenhouse"),
    ("Defi", "defi", "greenhouse"),
    ("Deel", "deel", "ashby"),
    ("Deliverr", "deliverr", "greenhouse"),
    ("Delivery Hero", "deliveryhero", "greenhouse"),
    ("Demandbase", "demandbase", "greenhouse"),
    ("Denodo", "denodo", "greenhouse"),
    ("Deuna", "deuna", "greenhouse"),
    ("Devo", "devo", "greenhouse"),
    ("Dialpad", "dialpad", "greenhouse"),
    ("Dialogflow", "dialogflow", "greenhouse"),
    ("DigitalOcean", "digitalocean", "greenhouse"),
    ("Digit", "digit", "greenhouse"),
    ("Dina", "dina", "greenhouse"),
    ("Discord", "discord", "greenhouse"),
    ("Discovery", "discovery", "greenhouse"),
    ("Ditto", "ditto", "ashby"),
    ("Divvy", "divvy", "greenhouse"),
    ("Docker", "docker", "greenhouse"),
    ("Docplanner", "docplanner", "greenhouse"),
    ("Docusign", "docusign", "greenhouse"),
    ("Dolby", "dolby", "greenhouse"),
    ("DoorDash", "doordash", "greenhouse"),
    ("Doximity", "doximity", "greenhouse"),
    ("DraftKings", "draftkings", "greenhouse"),
    ("Drata", "drata", "greenhouse"),
    ("Dremio", "dremio", "greenhouse"),
    ("Dribbble", "dribbble", "greenhouse"),
    ("Drift", "drift", "greenhouse"),
    ("DroneDeploy", "dronedeploy", "greenhouse"),
    ("Drop", "drop", "greenhouse"),
    ("Dropbox", "dropbox", "greenhouse"),
    ("Druva", "druva", "greenhouse"),
    ("DuckDuckGo", "duckduckgo", "greenhouse"),
    ("Duffel", "duffel", "ashby"),
    ("Duo Security", "duo", "greenhouse"),
    ("Duolingo", "duolingo", "greenhouse"),
    ("Durable", "durable", "ashby"),
    ("Dutchie", "dutchie", "greenhouse"),
    ("Dynamic Yield", "dynamicyield", "greenhouse"),
    ("Dynatrace", "dynatrace", "greenhouse"),
    ("E-commerce", "ecommerce", "greenhouse"),
    ("Edge Delta", "edgedelta", "greenhouse"),
    ("Edify", "edify", "greenhouse"),
    ("Elastic", "elastic", "greenhouse"),
    ("Element", "element", "greenhouse"),
    ("Elemy", "elemy", "greenhouse"),
    ("Embark", "embark", "greenhouse"),
    ("Emotive", "emotive", "greenhouse"),
    ("Empower", "empower", "greenhouse"),
    ("Encord", "encord", "ashby"),
    ("Engage", "engage", "greenhouse"),
    ("Engaging Networks", "engagingnetworks", "greenhouse"),
    ("Enigma", "enigma", "greenhouse"),
    ("Enjoy", "enjoy", "greenhouse"),
    ("Enlighten", "enlighten", "greenhouse"),
    ("Entelo", "entelo", "greenhouse"),
    ("Envoy", "envoy", "greenhouse"),
    ("Epic Games", "epicgames", "greenhouse"),
    ("Equinox", "equinox", "greenhouse"),
    ("Esusu", "esusu", "greenhouse"),
    ("Eternal", "eternal", "greenhouse"),
    ("Ethos", "ethos", "greenhouse"),
    ("Etoro", "etoro", "greenhouse"),
    ("Eventbrite", "eventbrite", "greenhouse"),
    ("Everlywell", "everlywell", "greenhouse"),
    ("Everyday", "everyday", "greenhouse"),
    ("Evidence.dev", "evidence", "ashby"),
    ("Exabeam", "exabeam", "greenhouse"),
    ("Expensify", "expensify", "greenhouse"),
    ("Exponent", "exponent", "greenhouse"),
    ("Exponential", "exponential", "greenhouse"),
    ("Fabric", "fabric", "greenhouse"),
    ("Faire", "faire", "greenhouse"),
    ("FalconX", "falconx", "greenhouse"),
    ("Farfetch", "farfetch", "greenhouse"),
    ("Fast", "fast", "greenhouse"),
    ("Fastly", "fastly", "greenhouse"),
    ("Fathom", "fathom", "greenhouse"),
    ("Feather", "feather", "greenhouse"),
    ("Feedzai", "feedzai", "greenhouse"),
    ("Fellow", "fellow", "greenhouse"),
    ("Fetch Rewards", "fetch", "greenhouse"),
    ("Fiddler AI", "fiddler", "greenhouse"),
    ("Figment", "figment", "greenhouse"),
    ("Figma", "figma", "lever"),
    ("Filevine", "filevine", "greenhouse"),
    ("Finance", "finance", "greenhouse"),
    ("Finch", "finch", "greenhouse"),
    ("Findem", "findem", "greenhouse"),
    ("FingerprintJS", "fingerprintjs", "greenhouse"),
    ("Finix", "finix", "greenhouse"),
    ("Fini", "fini", "ashby"),
    ("Fireblocks", "fireblocks", "greenhouse"),
    ("Firstbase", "firstbase", "greenhouse"),
    ("Fivetran", "fivetran", "greenhouse"),
    ("Flashpoint", "flashpoint", "greenhouse"),
    ("Flex", "flex", "greenhouse"),
    ("Flexport", "flexport", "greenhouse"),
    ("Flipboard", "flipboard", "greenhouse"),
    ("Flipkart", "flipkart", "greenhouse"),
    ("Float", "float", "greenhouse"),
    ("Flock", "flock", "greenhouse"),
    ("Flow", "flow", "greenhouse"),
    ("Flutterwave", "flutterwave", "greenhouse"),
    ("Fly.io", "fly", "ashby"),
    ("Flyr", "flyr", "greenhouse"),
    ("Focus", "focus", "greenhouse"),
    ("Font Awesome", "fontawesome", "greenhouse"),
    ("Foodpanda", "foodpanda", "greenhouse"),
    ("Formstack", "formstack", "greenhouse"),
    ("Forter", "forter", "greenhouse"),
    ("Fountain", "fountain", "greenhouse"),
    ("Frame.io", "frameio", "greenhouse"),
    ("Framer", "framer", "ashby"),
    ("FreeNow", "freenow", "greenhouse"),
    ("Freshly", "freshly", "greenhouse"),
    ("Freshworks", "freshworks", "greenhouse"),
    ("Front", "front", "greenhouse"),
    ("Frontier", "frontier", "greenhouse"),
    ("Fruitful", "fruitful", "ashby"),
    ("FullStory", "fullstory", "greenhouse"),
    ("Funnel", "funnel", "greenhouse"),
    ("Future", "future", "greenhouse"),
    ("Fuse", "fuse", "ashby"),
    ("Gainight", "gainight", "greenhouse"),
    ("Gallus", "gallus", "greenhouse"),
    ("GameAnalytics", "gameanalytics", "greenhouse"),
    ("Gamer", "gamer", "greenhouse"),
    ("Gamestream", "gamestream", "greenhouse"),
    ("Ganit", "ganit", "greenhouse"),
    ("Gantry", "gantry", "greenhouse"),
    ("Gather", "gather", "greenhouse"),
    ("Gazelle", "gazelle", "greenhouse"),
    ("Gelt", "gelt", "ashby"),
    ("Gem", "gem", "greenhouse"),
    ("Gemini", "gemini", "greenhouse"),
    ("Geneva", "geneva", "greenhouse"),
    ("Genius", "genius", "greenhouse"),
    ("Getaround", "getaround", "greenhouse"),
    ("Getir", "getir", "greenhouse"),
    ("Getty Images", "getty", "greenhouse"),
    ("Ghost", "ghost", "workable"),
    ("Mindrift", "mindrift", "workable"),
    ("Giggster", "giggster", "greenhouse"),
    ("Gilead", "gilead", "greenhouse"),
    ("GitBook", "gitbook", "greenhouse"),
    ("GitHub", "github", "greenhouse"),
    ("GitKraken", "gitkraken", "greenhouse"),
    ("GitLab", "gitlab", "greenhouse"),
    ("Giving Assistant", "givingassistant", "greenhouse"),
    ("Glassdoor", "glassdoor", "greenhouse"),
    ("Glean", "glean", "greenhouse"),
    ("Glide", "glide", "greenhouse"),
    ("Global", "global", "greenhouse"),
    ("GlobalLink", "globallink", "greenhouse"),
    ("Go-Jek", "gojek", "greenhouse"),
    ("GoCardless", "gocardless", "greenhouse"),
    ("GoDaddy", "godaddy", "greenhouse"),
    ("Goldbelly", "goldbelly", "greenhouse"),
    ("Golden", "golden", "greenhouse"),
    ("Gong", "gong", "greenhouse"),
    ("GoodRx", "goodrx", "greenhouse"),
    ("Goodnotes", "goodnotes", "greenhouse"),
    ("Google", "google", "internal"),
    ("GoPuff", "gopuff", "greenhouse"),
    ("Gorgias", "gorgias", "greenhouse"),
    ("Govilo", "govilo", "greenhouse"),
    ("Grafana Labs", "grafana", "greenhouse"),
    ("Grammarly", "grammarly", "greenhouse"),
    ("Granular", "granular", "greenhouse"),
    ("Graphite", "graphite", "ashby"),
    ("Gravatar", "gravatar", "greenhouse"),
    ("Gravity Sketch", "gravitysketch", "greenhouse"),
    ("Greenhouse", "greenhouse", "greenhouse"),
    ("Gremlin", "gremlin", "greenhouse"),
    ("Grid", "grid", "greenhouse"),
    ("Groq", "groq", "greenhouse"),
    ("GrowthBook", "growthbook", "ashby"),
    ("Grubhub", "grubhub", "greenhouse"),
    ("Guideline", "guideline", "greenhouse"),
    ("Gumball", "gumball", "greenhouse"),
    ("Gumroad", "gumroad", "ashby"),
    ("Gusto", "gusto", "greenhouse"),
    ("Gutcheck", "gutcheck", "greenhouse"),
    ("H1", "h1", "greenhouse"),
    ("HackerRank", "hackerrank", "greenhouse"),
    ("Halt", "halt", "greenhouse"),
    ("Happiest Baby", "happiestbaby", "greenhouse"),
    ("Happy Money", "happymoney", "greenhouse"),
    ("HashiCorp", "hashicorp", "greenhouse"),
    ("Hatch", "hatch", "greenhouse"),
    ("Haus", "haus", "greenhouse"),
    ("Headspace", "headspace", "greenhouse"),
    ("Heap", "heap", "greenhouse"),
    ("Hear.com", "hear", "greenhouse"),
    ("HelloFresh", "hellofresh", "greenhouse"),
    ("Help Scout", "helpscout", "greenhouse"),
    ("Heroku", "heroku", "greenhouse"),
    ("Hetzner", "hetzner", "greenhouse"),
    ("Hex", "hex", "greenhouse"),
    ("Highspot", "highspot", "greenhouse"),
    ("Hipcamp", "hipcamp", "greenhouse"),
    ("HireVue", "hirevue", "greenhouse"),
    ("Hiver", "hiver", "greenhouse"),
    ("Homelight", "homelight", "greenhouse"),
    ("Honey", "honey", "greenhouse"),
    ("Honeycomb", "honeycomb", "greenhouse"),
    ("Hopper", "hopper", "greenhouse"),
    ("Hopin", "hopin", "greenhouse"),
    ("Hostfully", "hostfully", "greenhouse"),
    ("Hotjar", "hotjar", "workable"),
    ("Housecall Pro", "housecallpro", "greenhouse"),
    ("Hugging Face", "huggingface", "greenhouse"),
    ("Human Interest", "humaninterest", "greenhouse"),
    ("Humane", "humane", "greenhouse"),
    ("Hypercontext", "hypercontext", "greenhouse"),
    ("Hyperscience", "hyperscience", "greenhouse"),
    ("Ibotta", "ibotta", "greenhouse"),
    ("Identiv", "identiv", "greenhouse"),
    ("Idio", "idio", "greenhouse"),
    ("Imperfect Foods", "imperfectfoods", "greenhouse"),
    ("Impossible Foods", "impossiblefoods", "greenhouse"),
    ("InVision", "invision", "greenhouse"),
    ("Incredible", "incredible", "greenhouse"),
    ("Inditex", "inditex", "greenhouse"),
    ("InfluxData", "influxdata", "greenhouse"),
    ("Informatica", "informatica", "greenhouse"),
    ("Inmobi", "inmobi", "greenhouse"),
    ("InnerCircle", "innercircle", "greenhouse"),
    ("Innova", "innova", "greenhouse"),
    ("InsideTracker", "insidetracker", "greenhouse"),
    ("Insider", "insider", "greenhouse"),
    ("Insight", "insight", "greenhouse"),
    ("InsightTimer", "insighttimer", "greenhouse"),
    ("Instacart", "instacart", "greenhouse"),
    ("Instana", "instana", "greenhouse"),
    ("Instapage", "instapage", "greenhouse"),
    ("Instawork", "instawork", "greenhouse"),
    ("Insurance", "insurance", "greenhouse"),
    ("Insurify", "insurify", "greenhouse"),
    ("Integrate", "integrate", "greenhouse"),
    ("Intel", "intel", "workday"),
    ("Intercom", "intercom", "greenhouse"),
    ("Interface", "interface", "greenhouse"),
    ("Interos", "interos", "greenhouse"),
    ("Inuit", "inuit", "greenhouse"),
    ("Accelone", "accelone", "breezy"),
    ("Invenia", "invenia", "greenhouse"),
    ("Invideo", "invideo", "greenhouse"),
    ("Invoca", "invoca", "greenhouse"),
    ("IonQ", "ionq", "greenhouse"),
    ("Ironclad", "ironclad", "greenhouse"),
    ("Islands", "islands", "greenhouse"),
    ("Ispirt", "ispirt", "greenhouse"),
    ("Iterative", "iterative", "greenhouse"),
    ("Itemize", "itemize", "greenhouse"),
    ("Itil", "itil", "greenhouse"),
    ("Itra", "itra", "greenhouse"),
    ("Ivory", "ivory", "greenhouse"),
    ("Ivoy", "ivoy", "greenhouse"),
    ("Iyzico", "iyzico", "greenhouse"),
    ("Jackpot.com", "jackpot", "greenhouse"),
    ("Jasper", "jasper", "greenhouse"),
    ("Jaunt", "jaunt", "greenhouse"),
    ("Jellyfish", "jellyfish", "greenhouse"),
    ("Jeny", "jeny", "greenhouse"),
    ("Jet", "jet", "greenhouse"),
    ("Jetpack", "jetpack", "greenhouse"),
    ("Jij", "jij", "greenhouse"),
    ("Jina AI", "jina", "greenhouse"),
    ("Jira", "jira", "greenhouse"),
    ("Jobber", "jobber", "greenhouse"),
    ("Jobis", "jobis", "greenhouse"),
    ("Joby Aviation", "joby", "greenhouse"),
    ("Joe", "joe", "greenhouse"),
    ("Jog", "jog", "greenhouse"),
    ("Jolt", "jolt", "greenhouse"),
    ("Joint", "joint", "greenhouse"),
    ("JOKR", "jokr", "greenhouse"),
    ("Jumia", "jumia", "greenhouse"),
    ("JumpCloud", "jumpcloud", "greenhouse"),
    ("Juniper", "juniper", "greenhouse"),
    ("Juno", "juno", "greenhouse"),
    ("Justworks", "justworks", "greenhouse"),
    ("Kajabi", "kajabi", "greenhouse"),
    ("Kaluza", "kaluza", "greenhouse"),
    ("Kandji", "kandji", "greenhouse"),
    ("Karat", "karat", "greenhouse"),
    ("Kasada", "kasada", "greenhouse"),
    ("Kashat", "kashat", "greenhouse"),
    ("Katana", "katana", "greenhouse"),
    ("Keep", "keep", "greenhouse"),
    ("Keepertax", "keepertax", "ashby"),
    ("Kekselias", "kekselias", "greenhouse"),
    ("Kendo", "kendo", "greenhouse"),
    ("Kernel", "kernel", "greenhouse"),
    ("Keybase", "keybase", "greenhouse"),
    ("Khoros", "khoros", "greenhouse"),
    ("Kickstarter", "kickstarter", "greenhouse"),
    ("Kindra", "kindra", "greenhouse"),
    ("Kinnevik", "kinnevik", "greenhouse"),
    ("Kinsa", "kinsa", "greenhouse"),
    ("Kion", "kion", "greenhouse"),
    ("Kitchen", "kitchen", "greenhouse"),
    ("Kitopi", "kitopi", "greenhouse"),
    ("Kitsune", "kitsune", "greenhouse"),
    ("Klaviyo", "klaviyo", "greenhouse"),
    ("Kleiner Perkins", "kleiner", "greenhouse"),
    ("Klarna", "klarna", "lever"),
    ("Knock", "knock", "greenhouse"),
    ("KnowBe4", "knowbe4", "greenhouse"),
    ("Kobiton", "kobiton", "greenhouse"),
    ("Kocoon", "kocoon", "greenhouse"),
    ("Kong", "kong", "greenhouse"),
    ("Konto", "konto", "greenhouse"),
    ("Kore.ai", "kore", "greenhouse"),
    ("Kover", "kover", "greenhouse"),
    ("Kraken", "kraken", "lever"),
    ("Kubeflow", "kubeflow", "greenhouse"),
    ("Kudelski", "kudelski", "greenhouse"),
    ("Kurly", "kurly", "greenhouse"),
    ("Kustomer", "kustomer", "greenhouse"),
    ("Kutuby", "kutuby", "greenhouse"),
    ("Kyte", "kyte", "greenhouse"),
    ("Labelbox", "labelbox", "greenhouse"),
    ("Labor", "labor", "greenhouse"),
    ("Lacework", "lacework", "greenhouse"),
    ("Ladder", "ladder", "greenhouse"),
    ("Landit", "landit", "greenhouse"),
    ("LangChain", "langchain", "greenhouse"),
    ("Lansweeper", "lansweeper", "greenhouse"),
    ("Launchpad", "launchpad", "greenhouse"),
    ("Lattice", "lattice", "greenhouse"),
    ("LeafLink", "leaflink", "greenhouse"),
    ("Learn", "learn", "greenhouse"),
    ("Lecto", "lecto", "greenhouse"),
    ("Ledger", "ledger", "greenhouse"),
    ("Legacy", "legacy", "greenhouse"),
    ("LegalZoom", "legalzoom", "greenhouse"),
    ("LendingHome", "lendinghome", "greenhouse"),
    ("LendingTree", "lendingtree", "greenhouse"),
    ("Lemonade", "lemonade", "greenhouse"),
    ("Lever", "lever", "lever"),
    ("Lexion", "lexion", "greenhouse"),
    ("Life360", "life360", "greenhouse"),
    ("Light", "light", "greenhouse"),
    ("Lightico", "lightico", "greenhouse"),
    ("Lightneer", "lightneer", "greenhouse"),
    ("Lightspeed", "lightspeed", "greenhouse"),
    ("Lightyear", "lightyear", "greenhouse"),
    ("Lilt", "lilt", "greenhouse"),
    ("Lime", "lime", "greenhouse"),
    ("Linear", "linear", "ashby"),
    ("LinkedIn", "linkedin", "smartrecruiters"),
    ("Linktree", "linktree", "greenhouse"),
    ("Linus", "linus", "greenhouse"),
    ("Liquid Death", "liquiddeath", "greenhouse"),
    ("Listen", "listen", "greenhouse"),
    ("LiveChat", "livechat", "greenhouse"),
    ("Livedesk", "livedesk", "greenhouse"),
    ("LivePerson", "liveperson", "greenhouse"),
    ("Livestorm", "livestorm", "greenhouse"),
    ("Local", "local", "greenhouse"),
    ("Localize", "localize", "greenhouse"),
    ("Loco", "loco", "greenhouse"),
    ("Loft", "loft", "greenhouse"),
    ("LogDNA", "logdna", "greenhouse"),
    ("Loggi", "loggi", "greenhouse"),
    ("Logitech", "logitech", "greenhouse"),
    ("Logos", "logos", "greenhouse"),
    ("Looker", "looker", "greenhouse"),
    ("Loom", "loom", "ashby"),
    ("Lottie", "lottie", "greenhouse"),
    ("Lowes", "lowes", "greenhouse"),
    ("Loyalty", "loyalty", "greenhouse"),
    ("Lucid", "lucid", "greenhouse"),
    ("Lucky", "lucky", "greenhouse"),
    ("Lugg", "lugg", "greenhouse"),
    ("Lulu", "lulu", "greenhouse"),
    ("Lumi", "lumi", "greenhouse"),
    ("Luminar", "luminar", "greenhouse"),
    ("Luminous", "luminous", "greenhouse"),
    ("Lunar", "lunar", "greenhouse"),
    ("Luno", "luno", "greenhouse"),
    ("Lusha", "lusha", "greenhouse"),
    ("Luxe", "luxe", "greenhouse"),
    ("Lyft", "lyft", "greenhouse"),
    ("Lyra", "lyra", "greenhouse"),
    ("M1", "m1", "greenhouse"),
    ("Machine", "machine", "greenhouse"),
    ("Mad", "mad", "greenhouse"),
    ("Magic", "magic", "greenhouse"),
    ("Magisto", "magisto", "greenhouse"),
    ("Magnet", "magnet", "greenhouse"),
    ("Magnify", "magnify", "greenhouse"),
    ("Magpie", "magpie", "greenhouse"),
    ("Mailchimp", "mailchimp", "greenhouse"),
    ("Mailgun", "mailgun", "greenhouse"),
    ("Make", "make", "ashby"),
    ("Malt", "malt", "greenhouse"),
    ("Mammoth", "mammoth", "greenhouse"),
    ("Mandiant", "mandiant", "greenhouse"),
    ("Mapbox", "mapbox", "greenhouse"),
    ("Maple", "maple", "greenhouse"),
    ("Mparticle", "mparticle", "greenhouse"),
    ("Markable", "markable", "greenhouse"),
    ("Marker", "marker", "greenhouse"),
    ("Market", "market", "greenhouse"),
    ("Marketing", "marketing", "greenhouse"),
    ("Marmot", "marmot", "greenhouse"),
    ("Marqeta", "marqeta", "greenhouse"),
    ("Mars", "mars", "greenhouse"),
    ("Marvell", "marvell", "greenhouse"),
    ("Master", "master", "greenhouse"),
    ("Material", "material", "greenhouse"),
    ("Matter", "matter", "greenhouse"),
    ("Matterport", "matterport", "greenhouse"),
    ("Maven", "maven", "greenhouse"),
    ("Max", "max", "greenhouse"),
    ("Maze", "maze", "greenhouse"),
    ("McAfee", "mcafee", "greenhouse"),
    ("Meal", "meal", "greenhouse"),
    ("Medallia", "medallia", "greenhouse"),
    ("Mediamath", "mediamath", "greenhouse"),
    ("Mediative", "mediative", "greenhouse"),
    ("Medium", "medium", "greenhouse"),
    ("Medly", "medly", "greenhouse"),
    ("Meet", "meet", "greenhouse"),
    ("Meetup", "meetup", "greenhouse"),
    ("Meister", "meister", "greenhouse"),
    ("Mem", "mem", "ashby"),
    ("Memory", "memory", "greenhouse"),
    ("Mend", "mend", "greenhouse"),
    ("Mental", "mental", "greenhouse"),
    ("Mentor", "mentor", "greenhouse"),
    ("Mercury", "mercury", "ashby"),
    ("Merge", "merge", "greenhouse"),
    ("Message", "message", "greenhouse"),
    ("MessageBird", "messagebird", "greenhouse"),
    ("Meta", "meta", "internal"),
    ("Metadata", "metadata", "greenhouse"),
    ("Method", "method", "greenhouse"),
    ("Metric", "metric", "greenhouse"),
    ("MetricStream", "metricstream", "greenhouse"),
    ("Metromile", "metromile", "greenhouse"),
    ("Mews", "mews", "greenhouse"),
    ("Mia", "mia", "greenhouse"),
    ("Micro", "micro", "greenhouse"),
    ("Microsoft", "microsoft", "internal"),
    ("Microstrategy", "microstrategy", "greenhouse"),
    ("Midjourney", "midjourney", "greenhouse"),
    ("Milkrun", "milkrun", "greenhouse"),
    ("Mind", "mind", "greenhouse"),
    ("MindTickle", "mindtickle", "greenhouse"),
    ("Mint", "mint", "greenhouse"),
    ("Mintbase", "mintbase", "greenhouse"),
    ("Miro", "miro", "greenhouse"),
    ("Mist", "mist", "greenhouse"),
    ("Mistral", "mistral", "ashby"),
    ("Mixpanel", "mixpanel", "greenhouse"),
    ("Miyagi", "miyagi", "greenhouse"),
    ("MNT-Halan", "mnthalan", "greenhouse"),
    ("Moat", "moat", "greenhouse"),
    ("Mobile", "mobile", "greenhouse"),
    ("Mobilize", "mobilize", "greenhouse"),
    ("Modal", "modal", "ashby"),
    ("Modern", "modern", "greenhouse"),
    ("Modest", "modest", "greenhouse"),
    ("Modo", "modo", "greenhouse"),
    ("Modulate", "modulate", "greenhouse"),
    ("Mojo", "mojo", "greenhouse"),
    ("Molecule", "molecule", "greenhouse"),
    ("Moment", "moment", "greenhouse"),
    ("Momentive", "momentive", "greenhouse"),
    ("Monzo", "monzo", "greenhouse"),
    ("Mood", "mood", "greenhouse"),
    ("Moody", "moody", "greenhouse"),
    ("Moogsoft", "moogsoft", "greenhouse"),
    ("Moon", "moon", "greenhouse"),
    ("Morning", "morning", "greenhouse"),
    ("Mosaic", "mosaic", "greenhouse"),
    ("Move", "move", "greenhouse"),
    ("Mozilla", "mozilla", "greenhouse"),
    ("Mullvad", "mullvad", "greenhouse"),
    ("Multiverse", "multiverse", "greenhouse"),
    ("Munch", "munch", "greenhouse"),
    ("Mural", "mural", "greenhouse"),
    ("Murf", "murf", "greenhouse"),
    ("Music", "music", "greenhouse"),
    ("Mux", "mux", "greenhouse"),
    ("MyGate", "mygate", "greenhouse"),
    ("Myntra", "myntra", "greenhouse"),
    ("Mystery", "mystery", "greenhouse"),
    ("N26", "n26", "greenhouse"),
    ("Nabla", "nabla", "ashby"),
    ("Namely", "namely", "greenhouse"),
    ("Nanit", "nanit", "greenhouse"),
    ("Napier", "napier", "greenhouse"),
    ("Narrative", "narrative", "greenhouse"),
    ("Native", "native", "greenhouse"),
    ("Nauto", "nauto", "greenhouse"),
    ("Navan", "navan", "greenhouse"),
    ("Navi", "navi", "greenhouse"),
    ("Near", "near", "greenhouse"),
    ("Nearmap", "nearmap", "greenhouse"),
    ("Nebula", "nebula", "greenhouse"),
    ("Nectar", "nectar", "greenhouse"),
    ("Neeva", "neeva", "greenhouse"),
    ("Neighbor", "neighbor", "greenhouse"),
    ("Neon", "neon", "ashby"),
    ("NerdWallet", "nerdwallet", "greenhouse"),
    ("Netlify", "netlify", "greenhouse"),
    ("Netskope", "netskope", "greenhouse"),
    ("Netsol", "netsol", "greenhouse"),
    ("Neuralink", "neuralink", "greenhouse"),
    ("New Relic", "newrelic", "greenhouse"),
    ("Newfront", "newfront", "greenhouse"),
    ("Nextdoor", "nextdoor", "greenhouse"),
    ("Nfverse", "nfverse", "greenhouse"),
    ("Niantic", "niantic", "greenhouse"),
    ("Nice", "nice", "greenhouse"),
    ("Nickel", "nickel", "greenhouse"),
    ("Nimble", "nimble", "greenhouse"),
    ("Nintex", "nintex", "greenhouse"),
    ("Nisum", "nisum", "greenhouse"),
    ("Niwa", "niwa", "greenhouse"),
    ("Noble", "noble", "greenhouse"),
    ("Nois", "nois", "greenhouse"),
    ("Nokia", "nokia", "greenhouse"),
    ("Nomad", "nomad", "greenhouse"),
    ("Nomic", "nomic", "greenhouse"),
    ("Noon", "noon", "greenhouse"),
    ("Nord Security", "nord", "greenhouse"),
    ("Nori", "nori", "greenhouse"),
    ("Notion", "notion", "lever"),
    ("Novo", "novo", "greenhouse"),
    ("Noyo", "noyo", "greenhouse"),
    ("Nubank", "nubank", "greenhouse"),
    ("Nucleus", "nucleus", "greenhouse"),
    ("Nudge", "nudge", "greenhouse"),
    ("Number", "number", "greenhouse"),
    ("Nurx", "nurx", "greenhouse"),
    ("Nuvemshop", "nuvemshop", "greenhouse"),
    ("Nvidia", "nvidia", "internal"),
    ("Nx", "nx", "greenhouse"),
    ("Nylas", "nylas", "greenhouse"),
    ("Oak", "oak", "greenhouse"),
    ("Oasis", "oasis", "greenhouse"),
    ("Obie", "obie", "greenhouse"),
    ("Objective", "objective", "greenhouse"),
    ("Obsidian", "obsidian", "greenhouse"),
    ("Ocean", "ocean", "greenhouse"),
    ("Octopus", "octopus", "greenhouse"),
    ("Okta", "okta", "greenhouse"),
    ("Olive", "olive", "greenhouse"),
    ("Olympia", "olympia", "greenhouse"),
    ("Omni", "omni", "greenhouse"),
    ("Omniscience", "omniscience", "greenhouse"),
    ("OnDeck", "ondeck", "greenhouse"),
    ("Onfido", "onfido", "greenhouse"),
    ("Onward", "onward", "greenhouse"),
    ("OpenAI", "openai", "greenhouse"),
    ("OpenSea", "opensea", "greenhouse"),
    ("Operational", "operational", "greenhouse"),
    ("Optical", "optical", "greenhouse"),
    ("Optimal", "optimal", "greenhouse"),
    ("Oracle", "oracle", "taleo"),
    ("Orange", "orange", "greenhouse"),
    ("Oraan", "oraan", "greenhouse"),
    ("Orb", "orb", "ashby"),
    ("Orbit", "orbit", "greenhouse"),
    ("Orca", "orca", "greenhouse"),
    ("Oren", "oren", "greenhouse"),
    ("Origin", "origin", "greenhouse"),
    ("Oscar", "oscar", "greenhouse"),
    ("Oshkosh", "oshkosh", "greenhouse"),
    ("Osprey", "osprey", "greenhouse"),
    ("Otter", "otter", "ashby"),
    ("Outdoorsy", "outdoorsy", "greenhouse"),
    ("Outreach", "outreach", "greenhouse"),
    ("Outschool", "outschool", "greenhouse"),
    ("Over", "over", "greenhouse"),
    ("Overtone", "overtone", "greenhouse"),
    ("Owl", "owl", "greenhouse"),
    ("Own", "own", "greenhouse"),
    ("Owner", "owner", "greenhouse"),
    ("Oxide", "oxide", "greenhouse"),
    ("Oyster", "oyster", "ashby"),
    ("Pacaso", "pacaso", "greenhouse"),
    ("Pacific", "pacific", "greenhouse"),
    ("Pack", "pack", "greenhouse"),
    ("Paddle", "paddle", "greenhouse"),
    ("Page", "page", "greenhouse"),
    ("PagerDuty", "pagerduty", "greenhouse"),
    ("Pail", "pail", "greenhouse"),
    ("Palantir", "palantir", "lever"),
    ("Palo", "palo", "greenhouse"),
    ("Pandadoc", "pandadoc", "greenhouse"),
    ("Panel", "panel", "greenhouse"),
    ("Panic", "panic", "greenhouse"),
    ("Paper", "paper", "greenhouse"),
    ("Papaya", "papaya", "greenhouse"),
    ("Paradox", "paradox", "greenhouse"),
    ("Parallel", "parallel", "greenhouse"),
    ("Parcel", "parcel", "greenhouse"),
    ("Pardot", "pardot", "greenhouse"),
    ("Parker", "parker", "ashby"),
    ("Partial", "partial", "greenhouse"),
    ("Particle", "particle", "greenhouse"),
    ("Partner", "partner", "greenhouse"),
    ("Party", "party", "greenhouse"),
    ("Patch", "patch", "greenhouse"),
    ("Path", "path", "greenhouse"),
    ("Pathlight", "pathlight", "greenhouse"),
    ("Patreon", "patreon", "greenhouse"),
    ("Pattern", "pattern", "greenhouse"),
    ("Pavilion", "pavilion", "greenhouse"),
    ("Pax", "pax", "greenhouse"),
    ("PayTabs", "paytabs", "greenhouse"),
    ("Payfit", "payfit", "greenhouse"),
    ("Payment", "payment", "greenhouse"),
    ("Paypal", "paypal", "internal"),
    ("Peak", "peak", "greenhouse"),
    ("Pearl", "pearl", "greenhouse"),
    ("Pebble", "pebble", "greenhouse"),
    ("Peloton", "peloton", "greenhouse"),
    ("Pencil", "pencil", "greenhouse"),
    ("Pendo", "pendo", "greenhouse"),
    ("People", "people", "greenhouse"),
    ("Pepper", "pepper", "greenhouse"),
    ("Perceptual", "perceptual", "greenhouse"),
    ("Perfect", "perfect", "greenhouse"),
    ("Perks", "perks", "greenhouse"),
    ("Perplexity", "perplexity", "greenhouse"),
    ("Persona", "persona", "greenhouse"),
    ("Personal", "personal", "greenhouse"),
    ("Petal", "petal", "greenhouse"),
    ("Phable", "phable", "greenhouse"),
    ("Phantom", "phantom", "greenhouse"),
    ("Philo", "philo", "greenhouse"),
    ("Phrase", "phrase", "greenhouse"),
    ("Pianity", "pianity", "greenhouse"),
    ("Pickle", "pickle", "greenhouse"),
    ("Pictory", "pictory", "greenhouse"),
    ("Pied", "pied", "greenhouse"),
    ("Pika", "pika", "ashby"),
    ("Pilot", "pilot", "greenhouse"),
    ("Pimly", "pimly", "greenhouse"),
    ("Pinecone", "pinecone", "greenhouse"),
    ("Ping", "ping", "greenhouse"),
    ("Pinterest", "pinterest", "greenhouse"),
    ("Pipedrive", "pipedrive", "greenhouse"),
    ("Pipefy", "pipefy", "greenhouse"),
    ("Pitch", "pitch", "greenhouse"),
    ("Pivot", "pivot", "greenhouse"),
    ("Plaid", "plaid", "greenhouse"),
    ("Planet", "planet", "greenhouse"),
    ("Planview", "planview", "greenhouse"),
    ("Play", "play", "greenhouse"),
    ("Playbook", "playbook", "greenhouse"),
    ("Playco", "playco", "greenhouse"),
    ("Playground", "playground", "greenhouse"),
    ("Playtest", "playtest", "greenhouse"),
    ("Pledge", "pledge", "greenhouse"),
    ("Plenti", "plenti", "greenhouse"),
    ("Plex", "plex", "greenhouse"),
    ("Pluto", "pluto", "greenhouse"),
    ("Podium", "podium", "greenhouse"),
    ("Point", "point", "greenhouse"),
    ("Polly", "polly", "greenhouse"),
    ("Poly", "poly", "greenhouse"),
    ("Polymer", "polymer", "greenhouse"),
    ("Post", "post", "greenhouse"),
    ("PostEx", "postex", "greenhouse"),
    ("PostHog", "posthog", "ashby"),
    ("Postman", "postman", "greenhouse"),
    ("Power", "power", "greenhouse"),
    ("Preply", "preply", "greenhouse"),
    ("Prezi", "prezi", "greenhouse"),
    ("Prisma", "prisma", "ashby"),
    ("Privitar", "privitar", "greenhouse"),
    ("Pro", "pro", "greenhouse"),
    ("Process", "process", "greenhouse"),
    ("Procore", "procore", "greenhouse"),
    ("Product", "product", "greenhouse"),
    ("Productboard", "productboard", "greenhouse"),
    ("Property", "property", "greenhouse"),
    ("Prosper", "prosper", "greenhouse"),
    ("Proton", "proton", "greenhouse"),
    ("Proxy", "proxy", "greenhouse"),
    ("Prudential", "prudential", "greenhouse"),
    ("Public", "public", "greenhouse"),
    ("Publish", "publish", "greenhouse"),
    ("Puff", "puff", "greenhouse"),
    ("Pulley", "pulley", "ashby"),
    ("Pulse", "pulse", "greenhouse"),
    ("Pure", "pure", "greenhouse"),
    ("Purple", "purple", "greenhouse"),
    ("Push", "push", "greenhouse"),
    ("Pyramid", "pyramid", "greenhouse"),
    ("Qonto", "qonto", "greenhouse"),
    ("Quora", "quora", "greenhouse"),
    ("Rabbit", "rabbit", "greenhouse"),
    ("Railway", "railway", "ashby"),
    ("Ramp", "ramp", "ashby"),
    ("Raycast", "raycast", "ashby"),
    ("Rec Room", "recroom", "greenhouse"),
    ("Reddit", "reddit", "greenhouse"),
    ("Remote", "remote", "ashby"),
    ("Render", "render", "ashby"),
    ("Retool", "retool", "ashby"),
    ("Revolut", "revolut", "greenhouse"),
    ("Rippling", "rippling", "greenhouse"),
    ("Robinhood", "robinhood", "greenhouse"),
    ("Roblox", "roblox", "greenhouse"),
    ("Runway", "runway", "greenhouse"),
    ("Salesforce", "salesforce", "workday"),
    ("Scale AI", "scale", "greenhouse"),
    ("Sentry", "sentry", "greenhouse"),
    ("Shopify", "shopify", "smartrecruiters"),
    ("Slack", "slack", "greenhouse"),
    ("Snowflake", "snowflake", "greenhouse"),
    ("Spotify", "spotify", "greenhouse"),
    ("Stripe", "stripe", "greenhouse"),
    ("Supabase", "supabase", "ashby"),
    ("Talabat", "talabat", "greenhouse"),
    ("Tinder", "tinder", "greenhouse"),
    ("Twitch", "twitch", "greenhouse"),
    ("Uber", "uber", "internal"),
    ("Unity", "unity", "greenhouse"),
    ("Vanta", "vanta", "ashby"),
    ("Vercel", "vercel", "ashby"),
    ("Webflow", "webflow", "greenhouse"),
    ("Wiz", "wiz", "greenhouse"),
    ("Zapier", "zapier", "greenhouse"),
    ("Zoom", "zoom", "greenhouse"),
    ("Zscaler", "zscaler", "greenhouse"),
    ("Motive (KeepTruckin)", "motive", "greenhouse"),
    ("Careem", "careem", "greenhouse"),
    ("SadaPay", "sadapay", "greenhouse"),
    ("Bazaar Technologies", "bazaar", "greenhouse"),
    ("Retailo", "retailo", "ashby"),
    ("Educative", "educative", "greenhouse"),
    ("10Pearls", "10pearls", "greenhouse"),
    ("Arbisoft", "arbisoft", "greenhouse"),
    ("Dubizzle", "dubizzle", "greenhouse"),
    ("Foodpanda", "foodpanda", "greenhouse"),
    ("Systems Limited", "systemsltd", "greenhouse"),
    ("VentureDive", "venturedive", "greenhouse"),
    ("Confiz", "confiz", "greenhouse"),
    ("Tintash", "tintash", "greenhouse"),
    ("Zones", "zones", "greenhouse"),
    ("Afiniti", "afiniti", "greenhouse"),
    ("S&P Global", "spglobal", "greenhouse"),
    ("Turing", "turing", "lever"),
    ("Andela", "andela", "greenhouse"),
    ("Remotebase", "remotebase", "greenhouse"),
    ("Data Darbar", "datadarbar", "greenhouse"),
    ("Bykea", "bykea", "greenhouse"),
    ("Savyour", "savyour", "greenhouse"),
    ("PostEx", "postex", "greenhouse"),
    ("Zameen", "zameen", "greenhouse"),
    ("Devsinc", "devsinc", "greenhouse"),
    ("Folio3", "folio3", "greenhouse"),
    ("i2c Inc", "i2c", "greenhouse"),
    ("Contour Software", "contour", "greenhouse"),
    ("CureMD", "curemd", "greenhouse"),
    ("NetSol Technologies", "netsol", "greenhouse"),
    ("Emumba", "emumba", "greenhouse"),
    ("TkXel", "tkxel", "greenhouse"),
    ("Rolustech", "rolustech", "greenhouse"),
    ("Codebits", "codebits", "greenhouse"),
    ("Techlogix", "techlogix", "greenhouse"),
    ("Nisum", "nisum", "greenhouse"),
    ("Cinnova", "cinnova", "greenhouse"),
    ("Nayatel", "nayatel", "workable"),
    ("Jazz", "jazz", "greenhouse"),
    ("Telenor", "telenor", "workable"),
    ("Zong", "zong", "greenhouse"),
    ("Ufone", "ufone", "greenhouse"),
    ("Bank Alfalah", "bankalfalah", "greenhouse"),
    ("HBL", "hbl", "greenhouse"),
    ("Daraz", "daraz", "greenhouse"),
    ("Cheetay", "cheetay", "greenhouse"),
    ("Airlift (Alumni)", "airlift", "greenhouse"),
    ("Jugnu", "jugnu", "greenhouse"),
    ("Tajir", "tajir", "greenhouse"),
    ("Finja", "finja", "greenhouse"),
    ("NayaPay", "nayapay", "greenhouse"),
    ("Abhi", "abhi", "greenhouse"),
    ("CreditBook", "creditbook", "greenhouse"),
    ("Khabri", "khabri", "greenhouse"),
    ("Dastgyr", "dastgyr", "greenhouse"),
    ("Markaz", "markaz", "greenhouse"),
    ("Krave Mart", "kravemart", "greenhouse"),
    ("GrocerApp", "grocerapp", "greenhouse"),
    ("Oraan", "oraan", "greenhouse"),
    ("Safepay", "safepay", "greenhouse"),
    ("KalPay", "kalpay", "greenhouse"),
    ("Metric", "metric", "greenhouse"),
    ("DealCart", "dealcart", "greenhouse"),
    ("Bagallery", "bagallery", "greenhouse"),
    ("Elo (Export Leftovers)", "elo", "greenhouse"),
    ("PriceOye", "priceoye", "greenhouse"),
    ("PakWheels", "pakwheels", "greenhouse"),
    ("IlmkiDunya", "ilmkidunya", "greenhouse"),
    ("Rozee.pk", "rozee", "greenhouse"),
    ("Mustakbil", "mustakbil", "greenhouse"),
    ("Oportun", "oportun", "greenhouse"),
    ("Talabat", "talabat", "greenhouse"),
    ("Noon", "noon", "greenhouse"),
    ("Property Finder", "propertyfinder", "greenhouse"),
    ("Kitopi", "kitopi", "greenhouse"),
    ("Swvl", "swvl", "greenhouse"),
    ("Tabby", "tabby", "greenhouse"),
    ("Tamara", "tamara", "greenhouse"),
    ("Huspy", "huspy", "greenhouse"),
    ("Sarwa", "sarwa", "greenhouse"),
    ("BitOasis", "bitoasis", "greenhouse"),
    ("Rain", "rain", "greenhouse"),
    ("CoinMENA", "coinmena", "greenhouse"),
    ("Anghami", "anghami", "greenhouse"),
    ("Starzplay", "starzplay", "greenhouse"),
    ("OSN", "osn", "greenhouse"),
    ("Shahid", "shahid", "greenhouse"),
    ("Mawdoo3", "mawdoo3", "greenhouse"),
    ("HyperPay", "hyperpay", "greenhouse"),
    ("PayTabs", "paytabs", "greenhouse"),
    ("Tap Payments", "tap", "greenhouse"),
    ("Geeks", "geeks", "greenhouse"),
# 🤖 AI & DATA SCIENCE (Massive Expansion)
    # =========================================================
    ("OpenAI", "openai", "greenhouse"),
    ("Anthropic", "anthropic", "ashby"),
    ("Mistral AI", "mistral", "ashby"),
    ("Scale AI", "scale", "greenhouse"),
    ("Databricks", "databricks", "greenhouse"),
    ("Hugging Face", "huggingface", "greenhouse"),
    ("Jasper.ai", "jasper", "greenhouse"),
    ("Midjourney", "midjourney", "greenhouse"),
    ("Stability AI", "stability", "greenhouse"),
    ("RunwayML", "runwayml", "greenhouse"),
    ("Cohere", "cohere", "greenhouse"),
    ("DeepMind", "deepmind", "greenhouse"),
    ("Perplexity AI", "perplexity", "greenhouse"),
    ("Adept AI", "adept", "greenhouse"),
    ("Inflection AI", "inflection", "greenhouse"),
    ("MosaicML", "mosaicml", "greenhouse"),
    ("Pinecone", "pinecone", "greenhouse"),
    ("Weaviate", "weaviate", "greenhouse"),
    ("Chroma", "chroma", "greenhouse"),
    ("LangChain", "langchain", "greenhouse"),
    ("LlamaIndex", "llamaindex", "greenhouse"),
    ("Unstructured", "unstructured", "greenhouse"),
    ("Arize AI", "arize", "greenhouse"),
    ("Fiddler AI", "fiddler", "greenhouse"),
    ("Snorkel AI", "snorkel", "greenhouse"),
    ("Labelbox", "labelbox", "greenhouse"),
    ("Synthesia", "synthesia", "greenhouse"),
    ("Descript", "descript", "greenhouse"),
    ("ElevenLabs", "elevenlabs", "greenhouse"),
    ("HeyGen", "heygen", "greenhouse"),
    ("Glean", "glean", "greenhouse"),
    ("Kortex", "kortex", "ashby"),
    ("Groq", "groq", "greenhouse"),
    ("Nomic AI", "nomic", "greenhouse"),
    ("Baseten", "baseten", "ashby"),
    ("Modal", "modal", "ashby"),
    ("Together AI", "together", "greenhouse"),
    ("Fireworks AI", "fireworks", "ashby"),
    ("Poe", "poe", "greenhouse"),
    ("Character.ai", "characterai", "greenhouse"),
    ("Suno", "suno", "ashby"),
    ("Udio", "udio", "ashby"),
    ("Luma AI", "luma", "greenhouse"),
    ("Pika Labs", "pika", "ashby"),
    ("Krea AI", "krea", "ashby"),
    ("Vectorized", "vectorized", "greenhouse"),
    ("DeepL", "deepl", "greenhouse"),
    ("Grammarly", "grammarly", "greenhouse"),
    ("Writer", "writer", "greenhouse"),
    ("Typeface", "typeface", "greenhouse"),
    ("Tome", "tome", "greenhouse"),
    ("Gamma", "gamma", "greenhouse"),
    ("Rewind AI", "rewind", "ashby"),
    ("Rabbit Inc", "rabbit", "greenhouse"),
    ("Humane", "humane", "greenhouse"),

    # =========================================================
    # 🟢 ASHBY & MODERN TECH STARTUPS (YC + High Growth)
    # =========================================================
    ("Vanta", "vanta", "ashby"),
    ("Linear", "linear", "ashby"),
    ("Lemon.io", "lemon", "ashby"),
    ("Framer", "framer", "ashby"),
    ("Retool", "retool", "ashby"),
    ("Supabase", "supabase", "ashby"),
    ("Vercel", "vercel", "ashby"),
    ("Railway", "railway", "ashby"),
    ("Render", "render", "ashby"),
    ("Beehiiv", "beehiiv", "ashby"),
    ("Cal.com", "cal", "ashby"),
    ("Fly.io", "fly", "ashby"),
    ("Prisma", "prisma", "ashby"),
    ("Raycast", "raycast", "ashby"),
    ("Mercury", "mercury", "ashby"),
    ("Pulley", "pulley", "ashby"),
    ("Carta", "carta", "ashby"),
    ("AngelList", "angellist", "ashby"),
    ("Bubble", "bubble", "ashby"),
    ("FlutterFlow", "flutterflow", "ashby"),
    ("Adalo", "adalo", "ashby"),
    ("Glide", "glide", "ashby"),
    ("Softr", "softr", "ashby"),
    ("Make", "make", "ashby"),
    ("n8n", "n8n", "ashby"),
    ("ClickUp", "clickup", "ashby"),
    ("Coda", "coda", "ashby"),
    ("Obsidian", "obsidian", "ashby"),
    ("Mem", "mem", "ashby"),
    ("Superhuman", "superhuman", "ashby"),
    ("Loom", "loom", "ashby"),
    ("Grain", "grain", "ashby"),
    ("Otter.ai", "otter", "ashby"),
    ("Fireflies.ai", "fireflies", "ashby"),
    ("Heptabase", "heptabase", "ashby"),
    ("Tana", "tana", "ashby"),
    ("Anytype", "anytype", "ashby"),
    ("AppFlowy", "appflowy", "ashby"),
    ("Vitrana", "vitrana", "ashby"),
    ("Dovetail", "dovetail", "ashby"),
    ("Productboard", "productboard", "greenhouse"),
    ("FullStory", "fullstory", "greenhouse"),
    ("PostHog", "posthog", "ashby"),
    ("LogRocket", "logrocket", "greenhouse"),
    ("Sentry", "sentry", "greenhouse"),
    ("Honeycomb", "honeycomb", "greenhouse"),
    ("Lightstep", "lightstep", "greenhouse"),
    ("LaunchDarkly", "launchdarkly", "greenhouse"),
    ("Split.io", "split", "greenhouse"),
    ("Aha!", "aha", "greenhouse"),
    ("Shortcut", "shortcut", "greenhouse"),
    ("Linear", "linear", "ashby"),
    ("Height", "height", "ashby"),
    ("Trello", "trello", "greenhouse"),
    ("Jira", "jira", "greenhouse"),
    ("Miro", "miro", "greenhouse"),
    ("Lucid", "lucid", "greenhouse"),
    ("Whimsical", "whimsical", "ashby"),
    ("Excalidraw", "excalidraw", "ashby"),
    # =========================================================
    # 🌎 GLOBAL REMOTE GIANTS
    # =========================================================
    ("Canonical", "canonical", "greenhouse"),
    ("Automattic", "automattic", "greenhouse"),
    ("GitLab", "gitlab", "greenhouse"),
    ("Doist", "doist", "workable"),
    ("Buffer", "buffer", "greenhouse"),
    ("Hotjar", "hotjar", "workable"),
    ("Ghost", "ghost", "workable"),
    ("DuckDuckGo", "duckduckgo", "greenhouse"),
    ("Mozilla", "mozilla", "greenhouse"),
    ("Elastic", "elastic", "greenhouse"),
    ("Grafana Labs", "grafana", "greenhouse"),
    ("HashiCorp", "hashicorp", "greenhouse"),
    ("Twilio", "twilio", "greenhouse"),
    ("Zapier", "zapier", "greenhouse"),
    ("Webflow", "webflow", "greenhouse"),
    ("InVision", "invision", "greenhouse"),
    ("Basecamp", "basecamp", "workable"),
    ("Toptal", "toptal", "greenhouse"),
    ("Crossover", "crossover", "greenhouse"),
    ("X-Team", "xteam", "greenhouse"),
    ("Clevertech", "clevertech", "greenhouse"),
    ("Time Doctor", "timedoctor", "greenhouse"),
    ("ModSquad", "modsquad", "greenhouse"),
    ("Scrapinghub (Zyte)", "zyte", "greenhouse"),
    ("1Password", "1password", "lever"),
    ("Ahrefs", "ahrefs", "workable"),
    ("Remote", "remote", "ashby"),
    ("Oyster", "oyster", "ashby"),
    ("Deel", "deel", "ashby"),
    ("Platform.sh", "platformsh", "greenhouse"),
    ("Sourcegraph", "sourcegraph", "greenhouse"),
    ("Mural", "mural", "greenhouse"),
    ("Abstract", "abstract", "greenhouse"),
    ("Harvest", "harvest", "workable"),
    ("Help Scout", "helpscout", "greenhouse"),
    ("Olark", "olark", "greenhouse"),
    ("Close", "close", "greenhouse"),
    ("Knack", "knack", "workable"),
    ("ConvertKit", "convertkit", "greenhouse"),
    ("Teachable", "teachable", "greenhouse"),
    ("Thinkific", "thinkific", "greenhouse"),
    ("Podia", "podia", "greenhouse"),
    ("Kajabi", "kajabi", "greenhouse"),
    ("Gumroad", "gumroad", "ashby"),
    ("Substack", "substack", "ashby"),
    ("Patreon", "patreon", "greenhouse"),
    ("Wikimedia Foundation", "wikimedia", "greenhouse"),
    ("Red Hat", "redhat", "greenhouse"),
    ("Suse", "suse", "greenhouse"),
    ("Mattermost", "mattermost", "greenhouse"),
    ("Rocket.Chat", "rocketchat", "greenhouse"),
    ("Bitwarden", "bitwarden", "greenhouse"),
    ("Brave Software", "brave", "greenhouse"),
    ("Tor Project", "torproject", "greenhouse"),
    ("Signal", "signal", "greenhouse"),
    ("Telegram", "telegram", "greenhouse"),
    ("Proton", "proton", "greenhouse"),
    ("Nord Security", "nordsecurity", "greenhouse"),
    ("Surfshark", "surfshark", "greenhouse"),
    ("ExpressVPN", "expressvpn", "greenhouse"),

    # =========================================================
    # 🚀 BIG TECH, SAAS & UNICORNS
    # =========================================================
    ("Stripe", "stripe", "greenhouse"),
    ("Airbnb", "airbnb", "greenhouse"),
    ("Dropbox", "dropbox", "greenhouse"),
    ("Spotify", "spotify", "greenhouse"),
    ("Reddit", "reddit", "greenhouse"),
    ("Pinterest", "pinterest", "greenhouse"),
    ("DoorDash", "doordash", "greenhouse"),
    ("Lyft", "lyft", "greenhouse"),
    ("Instacart", "instacart", "greenhouse"),
    ("Zoom", "zoom", "greenhouse"),
    ("Slack", "slack", "greenhouse"),
    ("Atlassian", "atlassian", "lever"),
    ("Figma", "figma", "lever"),
    ("Notion", "notion", "lever"),
    ("Airtable", "airtable", "greenhouse"),
    ("Asana", "asana", "greenhouse"),
    ("Monday.com", "monday", "greenhouse"),
    ("Box", "box", "greenhouse"),
    ("Okta", "okta", "greenhouse"),
    ("Datadog", "datadog", "greenhouse"),
    ("Cloudflare", "cloudflare", "greenhouse"),
    ("DigitalOcean", "digitalocean", "greenhouse"),
    ("Heroku", "heroku", "greenhouse"),
    ("Shopify", "shopify", "smartrecruiters"),
    ("HubSpot", "hubspot", "greenhouse"),
    ("Zendesk", "zendesk", "greenhouse"),
    ("Intercom", "intercom", "greenhouse"),
    ("Miro", "miro", "greenhouse"),
    ("Canva", "canva", "lever"),
    ("Salesforce", "salesforce", "workday"),
    ("Oracle", "oracle", "taleo"),
    ("Adobe", "adobe", "workday"),
    ("Intuit", "intuit", "workday"),
    ("Workday", "workday", "workday"),
    ("Snowflake", "snowflake", "greenhouse"),
    ("UiPath", "uipath", "greenhouse"),
    ("Unity", "unity", "greenhouse"),
    ("MongoDB", "mongodb", "greenhouse"),
    ("Veeva", "veeva", "greenhouse"),
    ("CrowdStrike", "crowdstrike", "greenhouse"),
    ("Zscaler", "zscaler", "greenhouse"),
    ("Samsara", "samsara", "greenhouse"),
    ("Confluent", "confluent", "greenhouse"),
    ("SentinelOne", "sentinelone", "greenhouse"),
    ("Freshworks", "freshworks", "greenhouse"),
    ("Amplitude", "amplitude", "greenhouse"),
    ("Rubrik", "rubrik", "greenhouse"),
    ("Gusto", "gusto", "greenhouse"),
    ("Rippling", "rippling", "greenhouse"),
    ("Lattice", "lattice", "greenhouse"),
    ("Culture Amp", "cultureamp", "greenhouse"),
    ("Udemy", "udemy", "greenhouse"),
    ("Coursera", "coursera", "greenhouse"),
    ("Duolingo", "duolingo", "greenhouse"),
    ("LinkedIn", "linkedin", "smartrecruiters"),
    ("Upwork", "upwork", "greenhouse"),
    ("Fiverr", "fiverr", "greenhouse"),
    ("Booking.com", "booking", "greenhouse"),
    ("Uber Eats", "ubereats", "greenhouse"),
]

# --- 3. HELPER FUNCTIONS ---

def get_gemini_client():
    global current_key_index
    api_key = GEMINI_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    return genai.Client(api_key=api_key)

def ai_process_job_safe(title, raw_html, raw_location):
    """
    ULTIMATE AI PROCESSING FUNCTION
    - Enforces Remote Only.
    - Maps strictly to User's Category Schema.
    - Formats Tags: [Sub1, Sub2, Sub3, Sub4, Country, JobType...]
    - Returns Clean HTML.
    """
    max_retries = 3
    base_wait = 2
    
    # 📌 TUMHARI STRICT CATEGORY LIST (AI Context ke liye)
    CATEGORIES_SCHEMA = {
        "Development": ["React", "Next.js", "Node.js", "Python", "MERN Stack", "WordPress", "Shopify", "Web3", "Frontend", "Backend", "DevOps", "Cybersecurity", "QA Engineer", "Automation Engineer", "Game Dev"],
        "Mobile App": ["React Native", "Flutter", "iOS", "Swift", "Android", "Kotlin", "Ionic", "App Design"],
        "AI & Machine Learning": ["AI Engineer", "Machine Learning", "NLP", "Computer Vision", "Prompt Engineering", "Chatbot Dev", "TensorFlow", "OpenAI API", "Python Scripting"],
        "Design & Creative": ["UI/UX Design", "Graphic Design", "Logo Design", "Figma", "Adobe Photoshop", "Illustrator", "Packaging Design", "Presentation Design", "NFT Art"],
        "Video & Animation": ["Video Editor", "Premiere Pro", "After Effects", "Motion Graphics", "3D Animation", "Thumbnail Artist", "Short Form", "VFX"],
        "Audio & Voice": ["Voice Over", "Audio Engineering", "Podcast Editor", "Music Production", "Sound Design", "Mixing & Mastering"],
        "Writing & Translation": ["Content Writer", "Copywriter", "Technical Writer", "Ghostwriter", "Proofreading", "Translation", "Scriptwriting", "Blog Writing", "Resume Writing"],
        "Marketing & Sales": ["SEO", "Social Media Manager", "Facebook Ads", "Google Ads", "Email Marketing", "Lead Generation", "Sales Representative", "Cold Calling", "Affiliate Marketing", "Influencer Marketing"],
        "Admin & Support": ["Virtual Assistant", "Data Entry", "Executive Assistant", "Research", "Project Management", "Transcription", "Spreadsheets"],
        "Customer Service": ["Customer Support", "Technical Support", "Community Manager", "Chat Support", "Call Center", "Zendesk"],
        "Finance & Accounting": ["Accountant", "Bookkeeping", "Financial Analyst", "Tax Preparation", "QuickBooks", "Xero", "CFO", "Crypto Trading"],
        "Legal & HR": ["Legal Consultant", "Contract Law", "Paralegal", "Recruiter", "HR Manager", "Talent Acquisition"],
        "Education & Coaching": ["Online Tutor", "Course Creator", "Language Teacher", "Math Tutor", "Coding Mentor", "Fitness Coach", "Life Coach"],
        "Data Science & Analytics": ["Data Scientist", "Data Analyst", "Business Intelligence", "Power BI", "Tableau", "SQL", "Big Data", "Data Scraping"],
        "Engineering & Architecture": ["CAD Designer", "3D Modeling", "Interior Design", "Mechanical Engineering", "Electrical Engineering", "AutoCAD", "SolidWorks"]
    }

    # JSON string banao taake Prompt mein daal sakein
    schema_str = json.dumps(CATEGORIES_SCHEMA, indent=2)

    prompt = f"""
    Act as a Strict Job Data Auditor.
    
    --- INPUT DATA ---
    Title: {title}
    Location String: {raw_location}
    Raw Content Sample: {raw_html[:6000]}...

    --- STRICT RULES (Follow Step-by-Step) ---

    1. **REMOTE CHECK (The Gatekeeper):**
       - If the job is NOT remote (e.g., requires onsite in "New York" or "London"), return `null` immediately.
       - Valid Remote signals: "Remote", "Work from home", "Anywhere", "Global", "Distributed".
    
    2. **CATEGORIZATION (The Match):**
       - Analyze the job. Match it to ONE key from this Schema:
       {schema_str}
       - Select the category that fits best.

    3. **TAGGING LOGIC (UPDATED FOR MULTIPLE COUNTRIES):**
       - **Step A (Skills):** Extract 3-4 valid sub-categories from the Schema (e.g. "React", "Node.js").
       
       - **Step B (Location Tags - CRITICAL):** - Analyze the Location String.
         - **Scenario 1:** If it lists multiple countries (e.g., "Remote - UK, Germany, Spain"), add **ALL** of them as separate tags: ["UK", "Germany", "Spain"].
         - **Scenario 2:** If it lists a Region (e.g., "EMEA", "LATAM", "Europe"), add that Region tag.
         - **Scenario 3:** If NO specific country is mentioned (just "Remote"), add "Global".
       
       - **Step C (Experience):** Detect "Senior", "Junior", "Lead", "Principal", "Mid-level". Infer from years (e.g. 5+ yrs = Senior). ADD TO TAGS.

       **Final Tag List Example:** ["React", "Frontend", "UK", "Germany", "Full-time", "Senior"]
       4. **LOCATION FORMATTING (CRITICAL - New Field):**
       - You must generate a single string for a new field called 'location_text'.
       - Format MUST be: **"Remote (Country1, Country2)"**
       - Examples:
         - If India: "Remote (India)"
         - If UK and Germany: "Remote (UK, Germany)" (All in one bracket)
         - If Global/Anywhere: "Remote (Global)"
         
         5. **JOB TYPE EXTRACTION:**
       - Extract one specific type for 'job_type' field: "Full-time", "Part-time", "Contract", "Freelance", "Internship", "Temporary".
       - Default to "Full-time" if not specified.
       
    6. **SALARY EXTRACTION (BE AGGRESSIVE):**
       - Scan specifically for "$" , "€", "£", "USD", "EUR".
       - Look for patterns like "100k-150k", "$60/hr", "50,000 - 80,000".
       - If found, return the EXACT string (e.g. "$100k - $150k").
       - Only return `null` if absolutely NO number is mentioned..   

    7. **DESCRIPTION CLEANING:**
       - Rewrite into clean **HTML**.
       - Structure: <h3>Headings</h3>, <ul><li>Lists</li></ul>, <p>Paragraphs</p>.
       - REMOVE: "Apply" buttons, "Click here", EEO statements, lengthy company footers.

    --- OUTPUT JSON FORMAT ---
    {{
        "clean_title": "Title Case Job Title",
        "category": "Exact Category Key",
        "tags": ["SubTag1", "SubTag2", "Global", "Full-time"],
        "location_text": "Remote (India, USA)",
        "job_type": "Full-time",
        "salary": "$50k - $80k",
        "is_remote": true,
        "clean_description": "<h3>Role</h3>..."
    }}
    Or return `null` if not remote.
    """

    for attempt in range(max_retries):
        try:
            client = get_gemini_client()
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type='application/json')
            )
            
            data = json.loads(response.text)
            
            # Agar AI ne null bheja (Not Remote), to skip karo
            if not data: return None
            
            # Double Check: Agar 'is_remote' false hai to null return karo
            if not data.get('is_remote', False): return None

            return data

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "exhausted" in error_msg:
                time.sleep(base_wait * (attempt + 1) * 2)
            else:
                print(f"❌ AI Error: {e}")
                return None 
    
    return None

def is_recent(date_obj):
    if not date_obj: return True
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS_TO_LOOK_BACK)
    if date_obj.tzinfo is None: date_obj = date_obj.replace(tzinfo=timezone.utc)
    return date_obj >= cutoff

# --- 4. NEW SCRAPERS (ASHBY, WORKABLE, BREEZY) ---

def fetch_ashby(company_name, board_token):
    # Ashby API: https://api.ashbyhq.com/posting-api/job-board/{board}
    print(f"🔎 Scanning Ashby: {company_name}...")
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}?includeCompensation=true"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return []
        
        jobs = res.json().get('jobs', [])
        payloads = []

        for job in jobs:
            # Ashby doesn't give date in list, so we assume fresh
            # Location check
            loc = job.get('address', {}).get('postalAddress', {}).get('addressCountry', '') or job.get('location', '')
            is_remote = job.get('isRemote', False) or "remote" in str(loc).lower()
            
            if not is_remote: continue

            # Ashby description is often in 'jobDescription' or 'descriptionHtml'
            raw_html = job.get('jobDescription') or job.get('descriptionHtml') or ""
            
            # AI Processing
            ai_data = ai_process_job_safe(job['title'], raw_html, str(loc))
            
            if ai_data:
                payloads.append({
                    "title": ai_data['clean_title'],
                    "source": company_name,
                    "link": job['jobUrl'],
                    "category": ai_data['category'],
                    "tags": ai_data['tags'],
                    "date_posted": datetime.now(timezone.utc).isoformat(), # Assume fresh
                    "approved": False,
                    "is_verified" : True,
                    "description": ai_data['clean_description'],
                    "location": ai_data.get('location_text') or "Remote (Global)",
                    "job_type": ai_data.get('job_type') or "Full-time",
                    "salary_range": ai_data.get('salary') or "Not Disclosed"
                })
        return payloads
    except Exception as e:
        print(f"⚠️ Error {company_name}: {e}")
        return []

def fetch_workable(company_name, board_token):
    # Workable Widget API: https://apply.workable.com/api/v1/accounts/{account}/postings
    print(f"🔎 Scanning Workable: {company_name}...")
    url = f"https://apply.workable.com/api/v1/accounts/{board_token}/postings"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return []
        jobs = res.json().get('jobs', [])
        payloads = []

        for job in jobs:
            # Date Check
            raw_date = job.get('published_on')
            if raw_date and not is_recent(parser.parse(raw_date)): continue

            # Remote Check
            if not job.get('telecommuting', False): continue # Workable ka "Remote" flag

            # Fetch Full Details (Description summary mein nahi hoti)
            detail_url = f"https://apply.workable.com/api/v1/accounts/{board_token}/postings/{job['shortcode']}"
            detail_res = requests.get(detail_url)
            if detail_res.status_code != 200: continue
            full_job = detail_res.json()
            
            raw_html = full_job.get('description', '') + full_job.get('requirements', '')
            
            ai_data = ai_process_job_safe(job['title'], raw_html, job.get('location', {}).get('country', ''))
            
            if ai_data:
                payloads.append({
                    "title": ai_data['clean_title'],
                    "source": company_name,
                    "link": full_job['url'],
                    "category": ai_data['category'],
                    "tags": ai_data['tags'],
                    "date_posted": datetime.now(timezone.utc).isoformat(),
                    "approved": False,
                    "is_verified" : True,
                    "description": ai_data['clean_description'],
                    "location": ai_data.get('location_text') or "Remote (Global)",
"job_type": ai_data.get('job_type') or "Full-time",
                    "salary_range": ai_data.get('salary') or "Not Disclosed"
                })
                time.sleep(1) # AI ko saans lene do
        return payloads
    except Exception as e:
        print(f"⚠️ Error {company_name}: {e}")
        return []

def fetch_breezy(company_name, board_token):
    # Breezy HR HTML Scraping: https://{company}.breezy.hr/
    print(f"🔎 Scanning Breezy HR: {company_name}...")
    url = f"https://{board_token}.breezy.hr/"
    
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        positions = soup.find_all('li', class_='position')
        
        payloads = []

        for pos in positions:
            title_elem = pos.find('h2')
            if not title_elem: continue
            title = title_elem.get_text(strip=True)
            
            link_elem = pos.find('a', href=True)
            if not link_elem: continue
            link = f"https://{board_token}.breezy.hr" + link_elem['href']
            
            location_elem = pos.find('span', class_='location')
            loc = location_elem.get_text(strip=True) if location_elem else ""
            
            # Remote Check
            if "remote" not in loc.lower() and "anywhere" not in loc.lower(): continue

            # Need to fetch detail page for description
            detail_res = requests.get(link)
            detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
            description_div = detail_soup.find('div', class_='description')
            raw_html = str(description_div) if description_div else ""

            ai_data = ai_process_job_safe(title, raw_html, loc)
            
            if ai_data:
                payloads.append({
                    "title": ai_data['clean_title'],
                    "source": company_name,
                    "link": link,
                    "category": ai_data['category'],
                    "tags": ai_data['tags'],
                    "date_posted": datetime.now(timezone.utc).isoformat(), # HTML me date nahi hoti usually
                    "approved": False,
                    "is_verified" : True,
                    "description": ai_data['clean_description'],
                    "location": ai_data.get('location_text') or "Remote (Global)",
"job_type": ai_data.get('job_type') or "Full-time",
                    "salary_range": ai_data.get('salary') or "Not Disclosed"
                })
                time.sleep(1)
        return payloads
    except Exception as e:
        print(f"⚠️ Error {company_name}: {e}")
        return []

# --- 5. EXISTING FETCHERS (SHORTENED FOR BREVITY) ---
def fetch_greenhouse(company_name, board_token):
    print(f"🔎 Scanning Greenhouse: {company_name}...")
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return []
        
        jobs = res.json().get('jobs', [])
        payloads = []

        for job in jobs:
            # 1. Date Check (Purani jobs filter karo)
            raw_date = job.get('updated_at')
            if not is_recent(parser.parse(raw_date) if raw_date else None): continue

            # 2. Remote Check (Manual Filtering before AI to save credits)
            loc_data = job.get('location', {})
            loc_name = loc_data.get('name', '') if loc_data else ''
            # Agar location mein "remote" nahi hai, to skip karo (AI ka time bachao)
            if "remote" not in loc_name.lower() and "anywhere" not in loc_name.lower(): continue

            # 3. AI Processing
            # Greenhouse ka content HTML hota hai
            raw_html = job.get('content') or ""
            # Fix double encoding issues
            if "&lt;" in raw_html: raw_html = html.unescape(raw_html)

            ai_data = ai_process_job_safe(job['title'], raw_html, loc_name)

            if ai_data:
                payloads.append({
                    "title": ai_data['clean_title'],
                    "source": company_name,
                    "link": job['absolute_url'],
                    "category": ai_data['category'],
                    "tags": ai_data['tags'],
                    # "Just Now" logic applied here 👇
                    "date_posted": datetime.now(timezone.utc).isoformat(),
                    "approved": False,
                    "is_verified" : True,
                    "description": ai_data['clean_description'], 
                    "location": ai_data.get('location_text') or "Remote (Global)",
"job_type": ai_data.get('job_type') or "Full-time",
                    "salary_range": ai_data.get('salary') or "Not Disclosed"
                })
                time.sleep(1) # Rate limit bachane ke liye

        return payloads
    except Exception as e:
        print(f"⚠️ Error {company_name}: {e}")
        return [] 

def fetch_lever(company_name, board_token):
    print(f"🔎 Scanning Lever: {company_name}...")
    url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200: return []
        
        jobs = res.json()
        payloads = []

        for job in jobs:
            # 1. Date Check
            raw_date_ts = job.get('createdAt')
            if raw_date_ts:
                job_date = datetime.fromtimestamp(raw_date_ts / 1000, tz=timezone.utc)
                if not is_recent(job_date): continue

            # 2. Remote Check (Location + Commitment)
            categories = job.get('categories', {})
            loc = categories.get('location', '')
            commitment = categories.get('commitment', '')
            
            is_remote_loc = "remote" in str(loc).lower() or "anywhere" in str(loc).lower()
            is_remote_commit = "remote" in str(commitment).lower()
            
            if not (is_remote_loc or is_remote_commit): continue

            # 3. AI Processing
            # Lever description plain text ya HTML ho sakti hai
            raw_desc_plain = job.get('descriptionPlain', '')
            raw_html = job.get('description', '') or raw_desc_plain
            
            ai_data = ai_process_job_safe(job['text'], raw_html, str(loc))

            if ai_data:
                payloads.append({
                    "title": ai_data['clean_title'],
                    "source": company_name,
                    "link": job['hostedUrl'],
                    "category": ai_data['category'],
                    "tags": ai_data['tags'],
                    # "Just Now" logic 👇
                    "date_posted": datetime.now(timezone.utc).isoformat(),
                    "approved": False,
                    "is_verified" : True,
                    "description": ai_data['clean_description'],
                    "location": ai_data.get('location_text') or "Remote (Global)",
"job_type": ai_data.get('job_type') or "Full-time",
                    "salary_range": ai_data.get('salary') or "Not Disclosed"
                })
                time.sleep(1)

        return payloads
    except Exception as e:
        print(f"⚠️ Error {company_name}: {e}")
        return []

# --- 6. MAIN EXECUTION ---
def run_scraper():
    print("🚀 Starting Multi-Platform Job Extraction...")
    
    for name, token, sys_type in TARGETS:
        jobs = []
        if sys_type == 'greenhouse': jobs = fetch_greenhouse(name, token)
        elif sys_type == 'lever': jobs = fetch_lever(name, token)
        elif sys_type == 'ashby': jobs = fetch_ashby(name, token)      # 👈 NEW
        elif sys_type == 'workable': jobs = fetch_workable(name, token) # 👈 NEW
        elif sys_type == 'breezy': jobs = fetch_breezy(name, token)    # 👈 NEW
        
        if jobs:
            print(f"   💾 Saving {len(jobs)} jobs...")
            for job in jobs:
                try:
                    supabase.table('jobs').upsert(job, on_conflict='link').execute()
                except: pass

# --- 🤖 BACKGROUND LOOP (JO CHALTA RAHEGA) ---
def background_scraper_loop():
    print("⏳ Background Scraper Thread Started...")
    while True:
        try:
            print(f"🚀 Starting Scan at: {datetime.now()}")
            run_scraper()  # Tumhara main function call hoga
            print("✅ Scan Complete! Sleeping for 6 hours...")
            time.sleep(21600)  # 6 Hours (21600 seconds) ka rest
        except Exception as e:
            print(f"❌ Crash prevention: {e}")
            time.sleep(60) # Error aaye to 1 min ruk kar retry karo

# --- 🌐 FAKE WEBSITE (RENDER KO KHUSH RAKHNE KE LIYE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Job Scraper Bot is Alive & Running!"

@app.route('/health')
def health():
    return "OK", 200

# --- 🚀 MAIN START POINT ---
if __name__ == "__main__":
    # 1. Background mein Scraper chalao (Thread)
    scraper_thread = threading.Thread(target=background_scraper_loop)
    scraper_thread.daemon = True # Taake main app band ho to ye bhi band ho jaye
    scraper_thread.start()
    
    # 2. Fake Website chalao
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)