from pyrogram import Client, raw
from pyrogram.raw.types import UpdateGroupCallParticipants
from SUKOON_MUSIC import app

@app.on_raw_update()
async def handle_video_chat_participants(client, update, users, chats):
    if isinstance(update, UpdateGroupCallParticipants):
        try:
            # Check if `chats` is not empty
            if chats:
                chat_id = list(chats.values())[0].id  # Extract chat ID
            else:
                print("No chat information available in the update.")
                return

            participants = update.participants

            for participant in participants:
                user = await client.get_users(participant.user_id)

                if participant.just_joined:  # Participant joined
                    text = (
                        f"🎉 #JoinVideoChat 🎉\n\n"
                        f"**Name**: {user.mention}\n"
                        f"**Action**: Joined\n\n"
                    )
                    await client.send_message(chat_id, text)

                elif participant.left:  # Participant left
                    text = (
                        f"😕 #LeftVideoChat 😕\n\n"
                        f"**Name**: {user.mention}\n"
                        f"**Action**: Left\n\n"
                    )
                    await client.send_message(chat_id, text)

        except Exception as e:
            print(f"Error handling participants: {e}")
