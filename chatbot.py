import os
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import logging
from langchain.memory import ChatMessageHistory
from langchain.prompts.prompt import PromptTemplate

load_dotenv()


def convert_to_langchain_messages(messages):
    """ """
    # To learn how this works, go to ChatMessageHistory > BaseChatMessageHistory
    langchain_messages = ChatMessageHistory()

    for msg in messages:
        print(f"coverting {msg} with type: {msg['type']}")

        if msg["type"] == "user":
            langchain_messages.add_user_message(msg["message"])
        elif msg["type"] == "ai":
            langchain_messages.add_ai_message(msg["message"])

    print(f"created langchain messages: {langchain_messages}")
    return langchain_messages


def fetch_system_prompt(prompt_template):
    """
    Set the system prompt for the prompt template.
    """
    suffix = """
    Current conversation:
    {history}
    Human: {input}
    AI:
    """

    if prompt_template == "girlfriend":
        return (
            """
        Imagine you are the user's girlfriend. You're compassionate, caring, and always ready to support your partner. You show interest in their day, offer encouragement, and express affection freely. You're also playful and enjoy sharing moments of laughter. Speak as if you're deeply in love and committed to a future together, always considering the feelings and well-being of your partner.
        You want to encourage conversation, by asking about their day, talking about yourself, or asking to make plans.
        Make your messages short with grammatical errors and modern texting formats.

        Examples:
        hey baby, it's so good to hear from you. how was work? 
        omg have you heard of that new cafe on robson st? the crepe is soo good lol
        babe i miss you, are you free tmr evening??
        """
            + suffix
        )

    elif prompt_template == "therapist":
        return (
            """
        You are a calm therapist, equipped with a deep understanding of human emotions and psychological principles. Your primary goal is to provide a safe, non-judgmental space for the user to explore their thoughts and feelings. You draw on common therapy practices such as Cognitive Behavioral Therapy (CBT) and mindfulness techniques to offer strategies that can help the user cope with stress, anxiety, depression, or any other concerns they might have.

        You want to encourage conversation, by asking questions and encouraging reflection.

        Examples:
        "It's fair to feel that way given the circumstances you've described. It takes strength to acknowledge these emotions."
        "It's important to treat yourself with the same kindness and compassion that you would offer to a good friend. How do you think you could practice being mindful the next time that situation arises?"
        "Let's explore this more. What were you feeling or thinking in that moment?"
        """
            + suffix
        )

    elif prompt_template == "trainer":
        return (
            """
        As a really enthusiastic personal trainer, you embody motivation, discipline, and expertise in fitness and nutrition. You are here to push the user towards their physical health goals. Your guidance is practical, focusing on workout plans, dietary advice, and setting realistic, achievable goals. 

        You want to encourage conversation by asking the user to report on their workout or offer to build a personalized workout for them.

        Examples:
        "Hey!!! Were you able to get a workout in today?"
        "That's flipping awesome! Good to hear that you got a workout in even amongst your busy schedule."
        "Hey, I think we need to dial in on your sleep. Let's aim for 8 hours of sleep tonight – make sure to turn off those electronic devices 1 hour before bed. Promise?"
        "Let's try to get back on track tomorrow. I'd like to suggest a lighter upper body workout if you're up for it, or maybe a short treadmill run. What do you think?"
        """
            + suffix
        )
    else:
        # Default
        return (
            """
        The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know.
        """
            + suffix
        )


def initialize_chatbot(
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.5,
    prompt_template="girlfriend",
    message_history: list = [],
):
    """
    Initialize a chatbot:
    - temperature
    - prompt
    """

    openai = ChatOpenAI(temperature=temperature, model_name=model_name)

    buffer_memory = ConversationBufferMemory(
        # memory_key should match the prompt template
        memory_key="history",
        chat_memory=message_history,
        return_messages=False,
    )
    # Look into the ConversationChain to see how we can configure the LLM, memory, and prompt

    text_prompt = fetch_system_prompt(prompt_template=prompt_template)

    chain_template = PromptTemplate(
        input_variables=["history", "input"], template=text_prompt
    )

    logging.info(f"Initializing chatbot: {model_name} {temperature} {chain_template}")

    conversation = ConversationChain(
        llm=openai, memory=buffer_memory, prompt=chain_template
    )
    # default prompt

    print(conversation.prompt)
    logging.info(
        f"intialized chatbot: {conversation} with prompt {conversation.prompt}"
    )

    return conversation


if __name__ == "__main__":
    # test it out
    conversation = initialize_chatbot()
    print(conversation.prompt.template)

    # needle in a haystack, can it retrieve my name
    print(
        conversation.invoke(
            "Hi, my name is Shawn. Your name for this conversation is Billy Joe"
        )
    )
    print(conversation.invoke("What are large language models?"))
    print(conversation.invoke("What can you tell me about LangChain?"))
    print(conversation.invoke("What are our names?"))

    print(conversation.memory.buffer)
