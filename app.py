import firebase_admin
from firebase_admin import credentials, firestore
from telethon.sync import TelegramClient
from dotenv import load_dotenv
from telethon.tl import types, functions
# from telethon.tl.types import InputChatAction, Message
from telethon import events
import os

cred = credentials.Certificate('treasurebot-4574d-firebase-adminsdk-i7wxi-147d3e523a.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

load_dotenv()
BOT_TOKEN = os.getenv('API_TOKEN')
API_ID=os.getenv('API_ID')
API_HASH=os.getenv('API_HASH')
SAFE_WORD=os.getenv('SAFE_WORD')

client = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Ahoy there, treasure hunters! 🏴‍☠️⚓\n\n"
        "Welcome to the most daring and mysterious treasure hunt in the seven seas!\n\n"
        "To embark on this epic journey, register your team with a unique teamname.\n\n"
        "**To register your team, use the following command:\n**"
        "`/register (team name here)\n\n\n`"
        "Type `/help` for assistance.")

@client.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    await event.respond("**Help Menu: **\n\nThis is the list of commands\n"
                "`/start` : used to start a bot and set Team Name\n"
                "`/register` : used to register your team\n"
                "`/treasure` : used to gain points for the treasure found\n"
                "`/leaderboard` : displays the current Leaderboard\n"
                "`/contact` : use this to contact the coordinators\n"
                "`/team` : displays your team name and points\n"
                "`/help` : display's all the commands\n"
                "\n If you are facing issue while scanning QR:\n"
                "send message to the coordinators with the QR code number that is written at the bottom side of QR\n"
                "\nIf you are facing issues with the bot:\n"
                "Firstly check your internet connection and try again and if doesn't work you can contact the event coordinators")

@client.on(events.NewMessage(pattern='/register'))
async def start(event):
    if(len(event.raw_text.split(' ', 1)) > 1):
        team_name = event.raw_text.split(' ', 1)[1].strip()

        existing_team = db.collection('teams').document(str(event.chat_id)).get()
        
        if existing_team.exists:
            await event.respond('You have already registered a team.')
        else:
            team_ref = db.collection('teams').document(str(event.chat_id))
            team_ref.set({
                'name': team_name,
                'points': 0,
                'treasure_progress': 0,
            })
            await event.respond(f'Team {team_name} registered successfully!')
    else:
        await event.respond("**To register your team, use the following command: \n\n**"
        "`/register (team name here)`")

treasure_codes = ['code1', 'code2', 'code3', 'code4', 'code5']
attempt = [3,3,3,3,3]
def assign_points(current_progress):
    if attempt[current_progress] == 3:
        attempt[current_progress]-=1
        return 10
    elif attempt[current_progress] == 2:
        attempt[current_progress]-=1
        return 8
    elif attempt[current_progress] == 1:
        attempt[current_progress]-=1
        return 6
    else:
        return 5
    
@client.on(events.NewMessage(pattern='/treasure'))
async def treasure(event):
    if(len(event.raw_text.split(' ', 1)) > 1):
        entered_code = event.raw_text.split(' ', 1)[1].strip()

        team_ref = db.collection('teams').document(str(event.chat_id))
        team_data = team_ref.get().to_dict()

        if team_data:
            current_progress = team_data.get('treasure_progress', 0)
            current_points = team_data.get('points', 0)

            if current_progress < len(treasure_codes):
                correct_code = treasure_codes[current_progress]

                if entered_code == correct_code:
                    points = assign_points(current_progress)
                    await event.respond(f'Correct code! You earned {points} points! ✨')
                    
                    team_ref.update({
                        'treasure_progress': current_progress + 1,
                        'points': current_points + points, 
                    })
                else:
                    await event.respond('Incorrect code. Try again! ❌')
            else:
                await event.respond('You have already completed the treasure hunt! 🔥🥂')
        else:
            await event.respond('You are not registered. Use `/register` to register your team.')
    else:
        await event.respond("**To claim your treasure, use the following command: \n\n**"
        "`\'/treasure\' (secret code here)`")

# DEV SECRET: USED TO HARD RESET ALL THE STATS
@client.on(events.NewMessage(pattern="/resetStats"))
async def start(event):
    safe_word = event.raw_text.split(' ', 1)[1].strip()
    if safe_word == SAFE_WORD:
        teams_collection = db.collection('teams')
        teams = teams_collection.stream()
        for team in teams:
            team_ref = teams_collection.document(team.id)
            team_ref.update({
                'treasure_progress':0,
                'points': 0,
            })
        await event.respond('Stats are resetted! 🔥🔥')
    else:
        await event.respond('Someone\'s trying to act all cheeky!!🌚')
    
@client.on(events.NewMessage(pattern='/leaderboard'))
async def start(event):
    teams_collection = db.collection('teams')
    teams = teams_collection.stream()

    sorted_teams = sorted(teams, key=lambda team: team.to_dict().get('points', 0), reverse=True)

    leaderboard_message = "**🎯Leaderboard: **\n\n"
    for i, team in enumerate(sorted_teams, start=1):
        team_data = team.to_dict()
        leaderboard_message += f"**{i}. {team_data['name']}** - {team_data['points']} points\n"

    await event.respond(leaderboard_message)

@client.on(events.NewMessage(pattern='/team'))
async def start(event):
    teams_collection = db.collection('teams')
    teams = teams_collection.stream()

    team_ref = db.collection('teams').document(str(event.chat_id))
    team_data = team_ref.get().to_dict()


    leaderboard_message = "**👾Your Team Details👾 **\n\n"
    leaderboard_message += f"Team Name: **{team_data['name']}**\nTeam Points: **{team_data['points']}**\n" 

    await event.respond(leaderboard_message)


@client.on(events.NewMessage)
async def echo(event):
    if event.text.startswith('/'):
        command = event.text.split()[0] 
        known_commands = ['/start', '/help', '/register', '/treasure', '/leaderboard', '/resetStats', '/team']

        if command not in known_commands:
            error_message = f"Oops! It seems like '{command}' is not a recognized command. "
            error_message += "Type '/help' for assistance with available commands."
            await event.respond(error_message)
        else:
            return
    else:
        await event.respond(f'Oops! It seems like you have entered an unrecognized command. Don\'t worry it happens best of us!\n\n **Type \'/help\' for assistance.**')

if __name__ == '__main__':
    client.start()
    client.run_until_disconnected()



