import os
import json
import difflib
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

# Load environment variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo")

# File paths
CATEGORIES_FILE = "categories.json"
ASSIGNMENTS_FILE = "assignment.json"
PROFILES_FILE = "example_profiles.json"

# Helper function to load JSON files
def load_json(file_path: str, default):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            # Zamiast wyświetlania błędu, logujemy go lub ignorujemy
            print(f"Error loading {file_path}: {e}")
            return default
    else:
        return default

def save_json(file_path: str, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Load data
categories = load_json(CATEGORIES_FILE, {})
assignments = load_json(ASSIGNMENTS_FILE, {})
profiles = load_json(PROFILES_FILE, [])

############################
# PROMPTS and LLM functions
############################

# PROMPT to extract skills
extract_prompt = ChatPromptTemplate(
    messages=[
        ("system",
         "Your task is to extract a list of skills from the description. Provide the output as a JSON list, e.g.: [\"skill 1\", \"skill 2\", ...]."),
        ("human", "Description: {description}")
    ],
    input_variables=["description"]
)
extract_chain = extract_prompt | llm

def extract_skills(description: str) -> list:
    raw_result = extract_chain.invoke({"description": description})
    raw_text = raw_result.content if hasattr(raw_result, "content") else raw_result
    try:
        skills = json.loads(raw_text)
        if not isinstance(skills, list):
            skills = [skills]
    except Exception as e:
        # Log error to console instead of wyświetlania komunikatu
        print(f"Error parsing skills: {e}")
        skills = []
    return skills

# PROMPT to assign category for a single skill
response_schemas = [
    ResponseSchema(name="category", description="Main skill category"),
    ResponseSchema(name="subcategory", description="Detailed skill subcategory"),
    ResponseSchema(name="justification", description="Short justification for the chosen categories")
]
output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
format_instructions = output_parser.get_format_instructions()

assign_prompt = ChatPromptTemplate(
    messages=[
        ("system",
         """For the given skill, assign it to the appropriate category and subcategory.
If the skill fits multiple domains, return a list of objects – each object should contain fields: "category", "subcategory", and "justification".
{format_instructions}"""),
        ("human", "Skill: {skill}")
    ],
    input_variables=["skill"],
    partial_variables={"format_instructions": format_instructions}
)
assign_chain = assign_prompt | llm

def assign_skill(skill: str) -> list:
    raw_result = assign_chain.invoke({"skill": skill})
    raw_text = raw_result.content if hasattr(raw_result, "content") else raw_result
    try:
        parsed = json.loads(raw_text)
        if not isinstance(parsed, list):
            parsed = [parsed]
    except Exception as e:
        # Log error to console instead of wyświetlania komunikatu
        print(f"Error parsing assignment for skill '{skill}': {e}")
        parsed = [output_parser.parse(raw_text)]
    return parsed

########################################
# Functions to update global dictionaries
########################################

def update_categories(result: dict, threshold: float = 0.8) -> None:
    global categories
    new_cat = result.get("category", "").strip()
    new_subcat = result.get("subcategory", "").strip()
    if not new_cat or not new_subcat:
        return

    matched_cat = None
    for existing_cat in categories.keys():
        similarity = difflib.SequenceMatcher(None, new_cat.lower(), existing_cat.lower()).ratio()
        if similarity >= threshold:
            matched_cat = existing_cat
            break

    if matched_cat:
        if new_subcat not in categories[matched_cat]:
            categories[matched_cat].append(new_subcat)
    else:
        categories[new_cat] = [new_subcat]

    save_json(CATEGORIES_FILE, categories)

def update_assignments(result: dict, profile: dict, skill: str) -> None:
    global assignments
    cat = result.get("category", "").strip()
    subcat = result.get("subcategory", "").strip()
    if not cat or not subcat:
        return

    if cat not in assignments:
        assignments[cat] = {}
    if subcat not in assignments[cat]:
        assignments[cat][subcat] = []

    entry = {
        "name": profile.get("name", "").strip(),
        "surname": profile.get("surname", "").strip(),
        "skill": skill,
        "description": profile.get("description", "").strip()
    }
    if entry not in assignments[cat][subcat]:
        assignments[cat][subcat].append(entry)
    save_json(ASSIGNMENTS_FILE, assignments)

####################################
# Profile processing and form
####################################

def process_profiles(profiles_list):
    log = []
    for profile in profiles_list:
        name = profile.get("name", "")
        surname = profile.get("surname", "")
        description = profile.get("description", "")
        log.append(f"Processing profile: {name} {surname}")
        skills = extract_skills(description)
        log.append(f"Extracted skills: {skills}")
        for skill in skills:
            results = assign_skill(skill)
            log.append(f"Assignment results for '{skill}': {results}")
            for res in results:
                update_categories(res)
                update_assignments(res, profile, skill)
        log.append("-----")
    return log

####################
# Streamlit Interface
####################

st.title("Profile Processing and Skill Assignment")
st.write("This application processes profiles from a JSON file and updates categories and assignments.")

# Process existing profiles
if st.button("Process Existing Profiles"):
    log = process_profiles(profiles)
    st.subheader("Processing Log:")
    for entry in log:
        st.text(entry)
    st.subheader("Updated Categories:")
    st.json(categories)
    st.subheader("Assignments:")
    st.json(assignments)

# Add new profile
st.markdown("## Add New Profile")
with st.form("new_profile_form"):
    new_name = st.text_input("First Name")
    new_surname = st.text_input("Last Name")
    new_description = st.text_area("Skill Description")
    submitted = st.form_submit_button("Add Profile")
    if submitted:
        if new_name and new_surname and new_description:
            new_profile = {"name": new_name, "surname": new_surname, "description": new_description}
            profiles.append(new_profile)
            save_json(PROFILES_FILE, profiles)
            log_new = process_profiles([new_profile])
            st.success("New profile processed!")
            st.subheader("Processing Log:")
            for entry in log_new:
                st.text(entry)
            st.subheader("Updated Categories:")
            st.json(categories)
            st.subheader("Assignments:")
            st.json(assignments)
        else:
            st.error("Please fill out all form fields.")
