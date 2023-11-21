import evadb
import shutil
import pandas as pd
import os
from dotenv import load_dotenv

shutil.rmtree('./evadb_data')

try:
    cursor = evadb.connect().cursor()
    cursor.query("""
        CREATE DATABASE mydb WITH ENGINE = 'sqlite', PARAMETERS = {
        "database": ":memory:"
    };""").execute()
except:
    pass


# drop all tables
cursor.query("""
    DROP TABLE IF EXISTS tasks;
""").execute()
# cursor.query("""
#     DROP TABLE IF EXISTS members;
# """).df()

# Create tables
cursor.query("""
    CREATE TABLE tasks (
        id INTEGER,
        name TEXT(30),
        description	TEXT(100)
    );
""").execute()

# list tables
x = cursor.query("""
use mydb {
   SELECT 
    name
FROM 
    sqlite_schema
WHERE 
    type ='table' AND 
    name NOT LIKE 'sqlite_%'
};
""").df()

print(x)
# create tasks

# y = cursor.query("""
#  INSERT INTO tasks (id, name, description) VALUES (3, 'test name 2', 'test description');
#     """).df()
# print(y)


# drop all data in tasks

# read json using pd
json_data = pd.read_json('issues.json')
print(json_data.head())

# insert each row into table
for index, row in json_data[1:].iterrows():
    # sanitize
    desc = row['description'].replace("'", "")
    desc = desc.replace(';', '')
    desc = desc.replace(',', '')

    cursor.query("""
    INSERT INTO tasks (id, name, description) VALUES ({}, '{}', '{}');
    """.format(index, row['contributor'], desc)).execute()


tasks = cursor.table('tasks').select("*").df()
print(tasks.head())


# print(os.environ['OPENAI_KEY'])

# cursor.query("""
# CREATE FUNCTION IF NOT EXISTS OpenAIChatCompletion
# IMPL 'evadb/functions/openai_chat_completion_function.py'
# MODEL 'gpt-3.5-turbo'
# """).execute()


# sample_issue = "When training models, tuning the parameters are common. Adding a CREATE OR REPLACE to simplify the query, so users do not need to run a DROP query every time."
sample_issue = json_data['description'][0]
# sanitize
sample_issue = sample_issue.replace("'", "")
sample_issue = sample_issue.replace(';', '')
sample_issue = sample_issue.replace(',', '')

# query = f"""
# Give a similarity score between this and the sample task below. Here are all of the tasks as context:
# All tasks:
# {tasks.to_markdown()}
# """

context = tasks.to_markdown()

query = f"""
How similar is the following sample task to the given context task? {sample_issue}
 
all tasks and contributors:

{context}

"""
# query = f"""
# Which of the following tasks is this most similar to?
# All tasks:
# {tasks.to_markdown()}
# """


# query = f"Give only a value between 0 and 1 representing the similarity between the given description and the following sample issue: {sample_issue}"
# prompt = "Give only a value between 0 and 1 for similarity and limit your response to 3 words."
# prompt = "Give only the tasks.id of the most similar task. Limit your response to 3 words."
prompt = "return based on the following [not similar = 0, somewhat similar = 0.5, very similar = 1]. limit your response to 1 number between 0 and 1."
res = cursor.table("tasks").select(
    f"ChatGPT('{query}', description, '{prompt}')"
)
responses = res.df()



print(responses)


# print all of the responses in responses['chatgpt.response']


#  append this col to tasks
tasks['similarity'] = responses['chatgpt.response']


# sort by similarity
tasks = tasks.sort_values(by=['similarity'], ascending=False)
print(tasks.head())


print(f"""
This task should be assigned to: {tasks.iloc[0]['tasks.name']}
""")


