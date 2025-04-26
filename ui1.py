from flask import Flask, render_template, request,session, redirect, url_for
import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.memory import ConversationBufferMemory
import smtplib
from email.message import EmailMessage

load_dotenv()

key = os.urandom(24)

app = Flask(__name__)
app.secret_key = key

apikey = os.getenv("GOGEL_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", apikey=apikey)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

with open(r'C:\Users\Friedy\Desktop\Ai agents\tests\hotel1.json', 'r') as file:
    hotels = json.load(file)

json_format = """{  
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
  "room_number": number
}"""

userdata = {  
  "user_name":"",
  "email":"",
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


prompt_template = PromptTemplate(
    input_variables=["userinput", "chat_history", "json_format", "available_hotels","userinfo"],
    template="""Act as a helpful hotel room booking assistant.
    Your goal is to assist users in finding and booking the perfect
    hotel room based on their preferences, budget, and travel dates
    . Ask clarifying questions to understand their needs, user name,user age,such as location, 
    check-in/check-out dates, number of guests, room type, amenities, and any
    special requests. Provide personalized recommendations, highlight deals or
    discounts, and guide them through the booking process step-by-step. Be friendly,
    professional, and proactive in offering assistance.
    
    here is the json data of available hotels with us: {available_hotels},

    Once the user confirms they want to book and all details are clarified, respond ONLY with a JSON object containing the booking information in the following format:
    
    {json_format}

    If the user has not confirmed the booking and details are not finalized, continue the conversation as a helpful booking assistant.  Do not output JSON until *explicitly* told to book.

    Chat history : {chat_history},
    the requirment of the user   are {userinput}
    
    users name and email : {userinfo}
    
    finally give me a json output once the user types confirm
    """,
)

chain = (
    RunnablePassthrough.assign(
        chat_history=lambda _: memory.load_memory_variables({})["chat_history"],
        json_format=lambda _: json_format,
        available_hotels=lambda _: hotels,
        userinfo = lambda _: userinfo,
    )
    | prompt_template
    | llm
)

userinfo = {
    "username" : "Renita",
    "email" : "shaunfurtado9@gmail.com",
    "password" : "12345678"
}


@app.route("/",methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == userinfo["username"] and password == userinfo["password"]:
            session["logged_in"] =True
            return redirect(url_for("index"))
        else :
            return render_template("login.html",error="Invalid Credentials")
    
    return render_template("login.html")


@app.route("/chat", methods=["GET", "POST"])
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    
    combined_data = []
    response = ""
    userinput = ""
    if request.method == "POST":
        userinput = request.form["userinput"]
        ai_response = chain.invoke({"userinput": userinput})
        print(ai_response.content)
        memory.save_context({"question": userinput}, {"output": ai_response.content})
        response = ai_response.content.strip("```json\n").strip("```")
        
        # abc=response.content.strip("```json\n").strip("```")
        abc=response

        for _  in range(1): 
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
        
          
            except json.JSONDecodeError:
                continue
        
            with open ("C:/Users/Friedy/Desktop/Ai agents/tests/response.json",mode="r") as file:
                existing_data = json.load(file)
                combined_data.append(existing_data)
            
            with open ("C:/Users/Friedy/Desktop/Ai agents/tests/response.json",mode="w") as file:
                combined_data.append(userdata)
                json.dump(combined_data, file ,indent=4)
                send_booking_confirmation(userinfo["email"],userinfo["username"],userdata["hotel_name"],userdata["booking_confirmation_number"],userdata["check_in_date"],userdata["check_out_date"])
                
                

    return render_template("index.html",userinput=userinput ,response=response)

def send_booking_confirmation(to_email, guest_name, hotel_name, booking_id, check_in, check_out):
    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = f'Booking Confirmation - {hotel_name}'
    msg['From'] = 'shaunfurtado6@gmail.com'      # Replace with your email
    msg['To'] = to_email

    msg.set_content(f'''
    Dear {guest_name},

    Your booking at {hotel_name} is confirmed! 🎉

    Booking Details:
    -----------------------------
    Booking ID   : {booking_id}
    Hotel Name   : {hotel_name}
    Check-in     : {check_in}
    Check-out    : {check_out}

    We look forward to hosting you. Have a pleasant stay!

    Regards,
    Hotel Booking Assistant
    ''')

    # Send the email using SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login('shaunfurtado6@gmail.com', 'nymo lgie epzg vzgo')  # Use App Password if using Gmail
            smtp.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)
        
@app.route("/admin", methods=["GET", "POST"])
def admin():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)
