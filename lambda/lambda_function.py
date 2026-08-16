import json
import random
import re


ALLOWED_MOODS = {"magical", "calming", "funny", "adventurous"}

OPENINGS = {
    "magical": [
        "One quiet evening, {name} discovered a tiny golden key beneath the pillow.",
        "Just before bedtime, a sparkling letter floated through {name}'s window.",
        "When the first star appeared, it winked three times and whispered {name}'s name.",
    ],
    "calming": [
        "As the sleepy moon rose, {name} followed a ribbon of soft silver light.",
        "The evening breeze carried a gentle song all the way to {name}'s window.",
        "Wrapped in the quiet of night, {name} noticed a small cloud waiting nearby.",
    ],
    "funny": [
        "At bedtime, {name} found a very serious sock wearing a tiny crown.",
        "A hiccuping star bounced into {name}'s room and politely asked for directions.",
        "Just as {name} closed one eye, the moon sneezed glitter across the sky.",
    ],
    "adventurous": [
        "A secret map appeared in {name}'s hands just as the clock struck seven.",
        "High above the rooftops, a tiny airship arrived to collect {name}.",
        "A silver compass began to spin, pointing {name} toward a hidden adventure.",
    ],
}

ADVENTURES = [
    "A friendly {animal} was waiting, ready to travel together to {place}.",
    "There, {name} met a {animal} who guarded the secret path to {place}.",
    "With a {animal} as a guide, {name} crossed a bridge made from moonbeams and reached {place}.",
    "Soon, a {animal} invited {name} aboard a cloud-shaped boat bound for {place}.",
]

CHALLENGES = {
    "magical": [
        "The stars had forgotten how to shine, and only a truly kind wish could wake them.",
        "A jar of moonlight had tipped over, hiding silver sparkles throughout the kingdom.",
        "The last rainbow had lost its colours, so they followed a trail of glowing feathers.",
    ],
    "calming": [
        "A little cloud could not find its way home, so they followed the slow song of the wind.",
        "The flowers were too excited to sleep, and needed someone to tell them a peaceful story.",
        "A shy star was afraid to glow, so they sat beside it until it felt safe.",
    ],
    "funny": [
        "Every royal pancake had learned to dance, and nobody could convince them to sit on a plate.",
        "The king's hat had flown away and was pretending to be a very fashionable bird.",
        "A family of bubbles had stolen all the giggles and hidden them inside a teapot.",
    ],
    "adventurous": [
        "A storm had scattered the pieces of an ancient star map across the sky.",
        "The bridge to the castle would appear only for travellers brave enough to take one more step.",
        "A mysterious bell rang from the highest tower, where no one had climbed for a hundred years.",
    ],
}

SOLUTIONS = [
    "{name} listened carefully, shared a brave idea, and together they discovered that kindness was the strongest magic of all.",
    "Instead of giving up, {name} took a deep breath and noticed one tiny clue that everyone else had missed.",
    "With teamwork, imagination, and one perfectly timed giggle, {name} and the {animal} solved the mystery.",
    "{name} remembered that small steps can finish even the biggest adventure, so they continued side by side.",
]

ENDINGS = {
    "magical": [
        "That night, every star shone a little brighter as {name} drifted into a dream full of magic.",
        "The moon sent {name} home on a silver cloud, with a pocket full of stardust and a heart full of wonder.",
    ],
    "calming": [
        "Soon {name} was safely home, cosy beneath the blankets, while the moon kept watch until morning.",
        "Everything grew quiet again, and {name} fell asleep knowing that the night was gentle and kind.",
    ],
    "funny": [
        "Back in bed, {name} tried not to laugh—but one last glittery hiccup escaped from under the pillow.",
        "Everyone celebrated with upside-down cake, and {name} returned home smiling all the way to sleep.",
    ],
    "adventurous": [
        "The kingdom cheered for its newest hero, and {name} returned home ready for tomorrow's adventure.",
        "With the mission complete, {name} sailed home beneath the stars, brave, proud, and wonderfully sleepy.",
    ],
}


def clean_text(value, fallback, max_length=60):
    if not isinstance(value, str):
        return fallback
    value = re.sub(r"[^\w\s'’\-]", "", value, flags=re.UNICODE).strip()
    return value[:max_length] or fallback


def response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload, ensure_ascii=False),
    }


def lambda_handler(event, context):
    try:
        if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
            return response(204, {})

        body = json.loads(event.get("body") or "{}")
        name = clean_text(body.get("name"), "a little dreamer", 30)
        animal = clean_text(body.get("animal"), "tiny moon bunny")
        place = clean_text(body.get("place"), "the Castle Above the Clouds")
        mood = body.get("mood", "magical")
        if mood not in ALLOWED_MOODS:
            mood = "magical"

        paragraphs = [
            random.choice(OPENINGS[mood]).format(name=name),
            random.choice(ADVENTURES).format(name=name, animal=animal, place=place),
            random.choice(CHALLENGES[mood]),
            random.choice(SOLUTIONS).format(name=name, animal=animal),
            random.choice(ENDINGS[mood]).format(name=name),
        ]

        return response(200, {"story": "\n\n".join(paragraphs)})
    except (json.JSONDecodeError, TypeError, AttributeError):
        return response(400, {"error": "Please send valid story ingredients."})
    except Exception:
        return response(500, {"error": "The story could not be generated. Please try again."})
