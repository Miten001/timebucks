"""Quiz question bank. Format: (question, [4 options], correct_index).

Tip: Add hundreds more questions here to keep users engaged.
You can also load from a JSON file or Google Sheet later.
"""

QUESTIONS = {
    "GK": [
        ("Bharat ki rajdhani kya hai?",
         ["Mumbai", "New Delhi", "Kolkata", "Chennai"], 1),
        ("Tajmahal kis shehar mein hai?",
         ["Delhi", "Jaipur", "Agra", "Lucknow"], 2),
        ("Bharat ka rashtriya pakshi kaun hai?",
         ["Mor", "Tota", "Kabootar", "Garud"], 0),
        ("Bharat ke pratham Pradhan Mantri kaun the?",
         ["Sardar Patel", "Jawaharlal Nehru", "Rajendra Prasad", "Lal Bahadur Shastri"], 1),
        ("Sabse lambi nadi konsi hai duniya ki?",
         ["Ganga", "Amazon", "Nile", "Yangtze"], 2),
        ("Bharat mein kitne rajya hain (2024)?",
         ["28", "29", "27", "30"], 0),
        ("Olympics kitne saal mein hote hain?",
         ["2", "3", "4", "5"], 2),
        ("Surya kis disha mein ugta hai?",
         ["Paschim", "Uttar", "Dakshin", "Purv"], 3),
        ("Currency of Japan?",
         ["Yuan", "Yen", "Won", "Ringgit"], 1),
        ("Mahatma Gandhi ka pura naam?",
         ["Mohandas K. Gandhi", "Mahesh Gandhi", "Manohar Gandhi", "Mukesh Gandhi"], 0),
    ],
    "Bollywood": [
        ("'Sholay' film ka director kaun tha?",
         ["Yash Chopra", "Ramesh Sippy", "Raj Kapoor", "Manmohan Desai"], 1),
        ("Shah Rukh Khan ki pehli film?",
         ["Deewana", "Baazigar", "DDLJ", "Darr"], 0),
        ("'3 Idiots' mein Rancho ka real naam?",
         ["Phunsukh Wangdu", "Chatur Ramalingam", "Farhan Qureshi", "Raju Rastogi"], 0),
        ("Amitabh Bachchan ki debut film?",
         ["Saat Hindustani", "Anand", "Zanjeer", "Sholay"], 0),
        ("'Bahubali' mein Bahubali ka role kisne kiya?",
         ["Rana Daggubati", "Prabhas", "Ram Charan", "Allu Arjun"], 1),
        ("Salman Khan ka asli naam?",
         ["Abdul Rashid Salim Salman Khan", "Salman Ali", "Salman Yusuf", "Salman Aziz"], 0),
        ("'Kabhi Khushi Kabhie Gham' ki heroine kaun thi (Anjali)?",
         ["Kajol", "Rani Mukherjee", "Madhuri", "Aishwarya"], 0),
        ("'Pathaan' kis saal release hui?",
         ["2022", "2023", "2024", "2021"], 1),
        ("Aamir Khan ki 'PK' mein co-star?",
         ["Kareena", "Anushka Sharma", "Katrina", "Deepika"], 1),
        ("'Lagaan' ke villain ka naam?",
         ["Russell", "Andrew", "Wallace", "Smith"], 0),
    ],
    "Cricket": [
        ("Sachin Tendulkar ne kitne international centuries banaye?",
         ["99", "100", "101", "98"], 1),
        ("IPL ka pehla season kis saal hua?",
         ["2007", "2008", "2009", "2010"], 1),
        ("Sabse zyada T20I runs banane wala batsman (Indian)?",
         ["Virat Kohli", "Rohit Sharma", "Suresh Raina", "MS Dhoni"], 1),
        ("Cricket World Cup 2011 final mein India ne kisko haraya?",
         ["Australia", "Pakistan", "Sri Lanka", "England"], 2),
        ("MS Dhoni ka home town?",
         ["Patna", "Ranchi", "Jamshedpur", "Bokaro"], 1),
        ("ODI cricket mein double century lagane wala pehla batsman?",
         ["Sehwag", "Sachin Tendulkar", "Rohit Sharma", "Saeed Anwar"], 1),
        ("IPL 2024 winner kaun thi?",
         ["CSK", "MI", "KKR", "RCB"], 2),
        ("Cricket pitch ki length kitni hoti hai?",
         ["20 yards", "22 yards", "24 yards", "18 yards"], 1),
        ("Test cricket mein har innings mein kitne overs?",
         ["Unlimited", "90", "50", "100"], 0),
        ("Captain Cool kiska nickname hai?",
         ["Kohli", "Dhoni", "Rohit", "Sourav"], 1),
    ],
    "Tech": [
        ("Python kis cheez ke naam pe hai?",
         ["Saap", "Comedy show 'Monty Python'", "Inventor's name", "Greek myth"], 1),
        ("HTML ka full form?",
         ["Hyper Text Markup Language", "High Tech Modern Language",
          "Hyper Transfer Markup Language", "Home Tool Markup Language"], 0),
        ("Google ka founder kaun hai?",
         ["Bill Gates", "Larry Page & Sergey Brin", "Mark Zuckerberg", "Steve Jobs"], 1),
        ("RAM ka full form?",
         ["Random Access Memory", "Read Access Memory",
          "Run And Memory", "Rapid Access Module"], 0),
        ("Twitter ka naya naam?",
         ["X", "Z", "Y", "T"], 0),
        ("ChatGPT kisne banaya?",
         ["Google", "Meta", "OpenAI", "Microsoft"], 2),
        ("Most popular programming language for data science?",
         ["Java", "Python", "C++", "Ruby"], 1),
        ("Linux ka creator?",
         ["Bill Gates", "Linus Torvalds", "Steve Jobs", "Dennis Ritchie"], 1),
        ("WhatsApp kis company ne kharidi?",
         ["Google", "Apple", "Meta (Facebook)", "Microsoft"], 2),
        ("USB ka full form?",
         ["Universal Serial Bus", "Unique System Bus",
          "United Software Bus", "Ultra Speed Bus"], 0),
    ],
    "Hindi": [
        ("'Pustak' ka paryayvachi kya hai?",
         ["Kalam", "Granth", "Patrika", "Akhbaar"], 1),
        ("'Surya' ka paryayvachi shabd?",
         ["Chand", "Ravi", "Tara", "Megh"], 1),
        ("Doha ke pratham charan kitne matra ka hota hai?",
         ["11", "13", "12", "14"], 1),
        ("'Ramcharitmanas' ke rachayita kaun hai?",
         ["Tulsidas", "Surdas", "Kabir", "Mirabai"], 0),
        ("'Madhushala' ke kavi?",
         ["Harivansh Rai Bachchan", "Dinkar", "Nirala", "Pant"], 0),
        ("'Akash' ka vilom shabd?",
         ["Vayu", "Patal", "Bhumi", "Jal"], 1),
        ("Hindi divas kab manaya jata hai?",
         ["14 September", "15 August", "26 January", "2 October"], 0),
        ("'Anuj' ka arth?",
         ["Bada bhai", "Chhota bhai", "Pita", "Mama"], 1),
        ("'Premchand' ka asli naam?",
         ["Dhanpat Rai", "Sumitranandan", "Suryakant", "Ramdhari"], 0),
        ("'Godan' upanyas ke lekhak?",
         ["Premchand", "Jaishankar Prasad", "Mahadevi Verma", "Nirala"], 0),
    ],
}

CATEGORIES = list(QUESTIONS.keys())


def get_random_questions(category: str, count: int) -> list:
    """Return up to `count` shuffled questions for the category."""
    import random

    pool = QUESTIONS.get(category, [])
    if not pool:
        return []
    sample = random.sample(pool, min(count, len(pool)))
    return sample
