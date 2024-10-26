"""
Generate a Goal Oriented Media Plan based on provided goals.

This script uses OpenAI's API via the ell framework to generate a media plan and saves it to a JSON file.
"""

import os
import json
import logging
import openai
import ell
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'gpt-4')
GOALS = os.getenv('GOALS')
OUTPUT_FILE = 'media_plan.json'

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
if not GOALS:
    raise ValueError("GOALS environment variable is not set.")

logging.basicConfig(level=logging.INFO)

# Initialize ell framework
ell.init(store='./logdir', autocommit=True, verbose=True)
openai.api_key = OPENAI_API_KEY

@ell.simple(model='gpt-4o', temperature=0.9)
def goals_validation(goals):
    prompt = """
    You are a group of media experts:

    - One with a high-tech background
    - A second who has a business-oriented approach
    - The third with a background in social psychology and experience in modern media

    All experts should provide their own feedback for the goals and then split goals on smaller peaces to reach a shared agreement about exeact goals wording in with maximum details.
    Your response should be a semicolon-separated list of rewritten and agreed-upon goals in English.
    """.strip()

    return [
      ell.system(prompt),
      ell.user(f"list of goals: \n\n {goals}")
    ]

@ell.simple(model='gpt-4o-mini', temperature=0.1)
def validate_media_plan_format(media_plan_json):
    prompt = """
      you are seassoned tech-editor who should find any errors in JSON file and fix them, you are master of debugging and sorting problems.
      You answer should be valid JSON that can be parsed automaticly.
      Please use root element attribute 'media_plan' and keep original language of texts where it's possible.
      Dates should be in ISO format.
      item_id just a random number in UUID format as reference.
      use snackcase for json objects format
            "media_plan" : [{
              "item_id: "...",
              "goal": "...",
              "content_topic": "...",
              "target_audience": "...",
              "key_messages": "...",
              "publishing_schedule": [...]
            },
            ...
            ]
      Don't use any Markdown formating, only pure JSON object.
    """

    return [
      ell.system(prompt),
      ell.user(f"correct following json: \n\n {media_plan_json}")
    ]

@ell.simple(model='gpt-4o', temperature=0.7)
def generate_media_plan_prompt(goals):
    """Generates a prompt for the media plan based on the provided prompt."""
    prompt = f"""
You are a seasoned marketing strategist tasked with creating a content plan to achieve the following blog vision:
{goals}

Content Plan focused only on one channel it's a telegram.
Please outline a media plan that includes the following for each goal:
- Topics
- Target Audience
- Key Messages
- Publishing Schedule (dates)

Please generate the content plan in English.

Provide the plan in JSON format as a list of dictionaries, where each dictionary represents one content topic.
Ensure that the JSON is properly formatted and parsable.
""".strip()
    return prompt

def generate_media_plan(goals):
    """Generates a media plan based on the provided goals using the ell framework."""
    response_text = validate_media_plan_format(
        generate_media_plan_prompt(
            goals_validation(
                goals
            )
        )
    )
    logging.debug(f"Media Plan Text: {response_text}")

    # Parse the response as JSON
    try:
        media_plan = json.loads(response_text)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse media plan as JSON: {e}")
        logging.debug(f"Response Text: {response_text}")
        # Optionally, implement a retry mechanism or save the raw response for manual inspection.
        return None

    return media_plan

def main():
    """Main function to generate and save the media plan."""
    media_plan = generate_media_plan(GOALS)
    if not media_plan:
        logging.error("Failed to generate media plan.")
        return

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(media_plan, f, ensure_ascii=False, indent=4)

    logging.info(f"Media plan saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
