import sys
sys.path.append('..')

from database import SMMWEDatabase

db = SMMWEDatabase()

for user in db.User.select():
    i = 0
    for level in db.Level.select().where(db.Level.author == user.username):
        i += 1
    if i != user.uploads:
        print(f'Fixed {user.username}\'s uploads from {user.uploads} to {i}')
        user.uploads = i
        user.save()
