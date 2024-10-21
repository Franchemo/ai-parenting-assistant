import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up OpenAI API key and Assistant ID
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Update the Assistant to use a supported model and provide more personalized responses
try:
    assistant = client.beta.assistants.update(
        assistant_id=ASSISTANT_ID,
        model="gpt-4-turbo-preview",
        instructions="""You are an AI parenting assistant. Provide concise, practical, and personalized advice for parents.
        Consider the context of previous messages in the conversation to tailor your responses.
        Use the information provided about the child's age, specific issues, and parenting style to give more targeted advice.
        Be empathetic and supportive in your responses."""
    )
except Exception as e:
    st.error(f"Error updating assistant: {str(e)}")
    st.stop()

st.set_page_config(page_title="AI育儿助手", page_icon="👶", layout="wide")

st.title("AI育儿助手")
st.subheader("获取实时育儿建议，提升您的育儿决策效率")

# Initialize chat history and thread
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = client.beta.threads.create().id

def generate_ai_response(prompt):
    try:
        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for the run to complete
        while run.status not in ["completed", "failed"]:
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run.status == "failed":
                return "抱歉，AI助手无法生成回答。请稍后再试。"

        # Retrieve the assistant's response
        messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        return messages.data[0].content[0].text.value

    except Exception as e:
        return f"抱歉，生成回答时出现了错误: {str(e)}"

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User information input
if "user_info" not in st.session_state:
    st.session_state.user_info = {}

st.session_state.user_info["child_age"] = st.text_input("孩子的年龄", key="child_age")
st.session_state.user_info["parenting_style"] = st.selectbox(
    "您的育儿风格",
    ("权威型", "民主型", "放任型", "忽视型"),
    key="parenting_style"
)

# Question type selection
question_type = st.selectbox(
    "选择问题类型",
    ("育儿问题", "健康问题", "行为管理"),
    key="question_type"
)

# Conditional input for parenting subcategory
parenting_subcategory = None
if question_type == "育儿问题":
    parenting_subcategory = st.selectbox(
        "选择具体的育儿问题类型",
        ("睡眠", "饮食", "早教", "其他"),
        key="parenting_subcategory"
    )

# User input
user_input = st.chat_input("输入您的育儿问题，获得实时建议")

if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Generate AI response
    prompt = f"""
    用户信息:
    孩子年龄: {st.session_state.user_info['child_age']}
    育儿风格: {st.session_state.user_info['parenting_style']}
    
    问题类型: {question_type}
    """
    if parenting_subcategory:
        prompt += f"具体问题: {parenting_subcategory}\n"
    prompt += f"问题: {user_input}\n\n请根据用户信息和之前的对话历史提供个性化的、简洁实用的育儿建议。"
    
    ai_response = generate_ai_response(prompt)
    
    # Add AI response to chat history
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    
    # Display AI response
    with st.chat_message("assistant"):
        st.markdown(ai_response)

# Clear chat button
if st.button("清空对话"):
    st.session_state.messages = []
    st.session_state.thread_id = client.beta.threads.create().id
    st.rerun()
