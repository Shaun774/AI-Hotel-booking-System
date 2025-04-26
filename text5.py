import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.memory import ConversationBufferMemory
import json
import re


load_dotenv()

apikey = os.getenv("GOGEL_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",apikey=apikey)

memory = ConversationBufferMemory(memory_key="chat_history",return_messages=True)

json_format = """
{  
  "user_name":"string",
  "age":"integer",
  "hotel_name": "string",
  "location": "string",
  "check_in_date": "YYYY-MM-DD",
  "check_out_date": "YYYY-MM-DD",
  "number_of_guests": "integer",
  "room_type": "string",
  "amenities": ["string", "string", ...],
  "total_price": "number",
  "booking_confirmation_number": "string",
  "room_number": number,
}
"""

userdata = {  
  "user_name":"",
  "age":"",
  "hotel_name": "",
  "location": "",
  "check_in_date": "",
  "check_out_date": "",
  "number_of_guests": "",
  "room_type": "",
  "amenities": "",
  "total_price": "number",
  "booking_confirmation_number": "",
  "room_number":"",
}

with open(r'C:\Users\Friedy\Desktop\Ai agents\tests\hotel1.json','r') as file:
    hotels = json.load(file)
    
prompt_template = PromptTemplate(
    input_variables=["userinput", "chat_history", "json_format","available_hotels"],
    template="""Act as a helpful hotel room booking assistant.
    Your goal is to assist users in finding and booking the perfect
    hotel room based on their preferences, budget, and travel dates
    . Ask clarifying questions to understand their needs, user name,user age,such as location, 
    check-in/check-out dates, number of guests, room type, amenities, and any
    special requests. Provide personalized recommendations, highlight deals or
    discounts, and guide them through the booking process step-by-step. Be friendly,
    professional, and proactive in offering assistance.
    
    here is the json data of available hotels with us: {available_hotels},
    if there are no hotels list out avaliable hotels,

    Once the user confirms they want to book and all details are clarified, respond ONLY with a JSON object containing the booking information in the following format:
    
    {json_format}

    If the user has not confirmed the booking and details are not finalized, continue the conversation as a helpful booking assistant.  Do not output JSON until *explicitly* told to book.

    Chat history : {chat_history},
    the requirment of the user   are {userinput}
    
    finally give me a json output once the user types confirm
    """,
)

chain = (
    RunnablePassthrough.assign(
        chat_history=lambda _: memory.load_memory_variables({})["chat_history"],
        json_format=lambda _: json_format,  # Wrap json_format in a lambda
        available_hotels = lambda _: hotels
    )
    | prompt_template
    | llm
)

combined_data = []

while True:
    userinput = input("Userinput : ")
    if userinput.lower() in ["exit","quit"]:
        break
    response = chain.invoke({"userinput":userinput})
    
    # try:
    #     json_data = json.loads(response.content.strip("```json\n").strip("```"))  # Remove extra formatting
    # except json.JSONDecodeError:
        
    #     continue
    memory.save_context({"question": userinput}, {"output": response.content})
    print("---------------------------------------")
    print(response.content)
    
    
    abc=response.content.strip("```json\n").strip("```")
    # abc = re.sub(r"```json\n|```", "", abc).strip()
    try:
        json_data = json.loads(abc)  # Convert string to dictionary
        userdata["user_name"] = json_data.get("user_name", "Unknown")  # Extract name
        userdata["age"] = json_data.get("age", "Unknown")    # Extract age
        userdata["hotel_name"] = json_data.get("hotel_name", "Unknown") 
        userdata["location"] = json_data.get("location","Unknown")
        userdata["check_in_date"] = json_data.get("check_in_date","Unknown")
        userdata["check_out_date"] = json_data.get("check_out_date","Unknown")
        userdata["number_of_guests"] = json_data.get("number_of_gusets","Unknown")
        userdata["room_type"]= json_data.get("room_type","Unknown")
        userdata["amenities"] = json_data.get("amennites","Unknown")
        userdata["total_price"] = json_data.get("total_price","Unknown")
        userdata["booking_confirmation_number"] = json_data.get("booking_confirmation_number","Unknown")
        userdata["room_number"] = json_data.get("room_number","Unknown")
        
        # for hotel in hotels:
        #     if hotel["hotel_name"] == userdata["hotel_name"]:
        #         for room in hotel["rooms_available"]:
        #             if str(userdata["room_number"]) in room:
        #                 room[str(userdata["room_number"])] = False
                        # Exit the loop once the room is updated
        with open(r'C:\Users\Friedy\Desktop\Ai agents\tests\hotel1.json', 'r+') as file:
            data = json.load(file)
            for h in data:
                if h["hotel_name"] == userdata["hotel_name"]:
                    date_range = f"{userdata['check_in_date']} to {userdata['check_out_date']}"
                    for r in h["rooms_available"]:
                        if str(userdata["room_number"]) in r:
                                r[str(userdata["room_number"])] = {date_range: False}
                        file.seek(0)
                        json.dump(data, file, indent=4)
                        file.truncate()
                    break 
                        
        # for hotel in hotels:
        #     if hotel["hotel_name"] == userdata["hotel_name"]:
        #         for i in range(len(hotel["rooms_available"])):
        #             room = hotel["rooms_available"][i]
        #             if str(userdata["room_number"]) in room:
        #                 hotel["rooms_available"][i][str(userdata["room_number"])] = False
        #                 with open(r'C:\Users\Friedy\Desktop\Ai agents\tests\hotel1.json','w' ) as file:
        #                     json.dump(hotels, file, indent=4)
        #                 break
        
       

    except json.JSONDecodeError:
        continue 
    
    with open ("C:/Users/Friedy/Desktop/Ai agents/tests/response.json",mode="r") as file:
        existing_data = json.load(file)
        combined_data.append(existing_data)
        
    with open ("C:/Users/Friedy/Desktop/Ai agents/tests/response.json",mode="w") as file:
        combined_data.append(userdata)
        json.dump(combined_data, file ,indent=4)
        
    print("---------------------------------------")

    
    
