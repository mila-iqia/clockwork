from flask_login import UserMixin

from db import get_mongo_client

class User(UserMixin):
    """
    The methods of this class are determined by the demands of the 
    `login_manager` library. For example, the fact that `get` returns
    a `None` if it fails to find the user.
    """

    def __init__(self, id_, name, email, profile_pic, status="enabled", biblioplex_api_key=None):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic
        self.status = status
        self.biblioplex_api_key = biblioplex_api_key

    @staticmethod
    def get(user_id:str):

        mc = get_mongo_client()['biblioplex']

        L = list(mc['users'].find({'id': user_id}))
        assert len(L) in [0, 1], (
            "Found %d users with id %s. This can't be." % (len(L), user_id))

        if len(L) == 0:
            return None
        else:
            e = L[0]
            user = User(
                id_=user_id,
                name=e['name'],
                email=e['email'],
                profile_pic=e['profile_pic'],
                status=e['status'],
                biblioplex_api_key=e['biblioplex_api_key'])
            print("Retrieved entry for user with email %s." % e['email'])
            return user

    @staticmethod
    def create(id_, name, email, profile_pic, status="enabled", biblioplex_api_key=None):
        
        assert status in ['enabled', 'disabled']
        if biblioplex_api_key is None or len(biblioplex_api_key) == 0:
            biblioplex_api_key = get_new_biblioplex_api_key()

        mc = get_mongo_client()['biblioplex']
        e = {'id': id_,
            'name': name,
            'email': email,
            'profile_pic': profile_pic,
            'status': status,
            'biblioplex_api_key': biblioplex_api_key
        }
        mc['users'].update_one({'id': id_}, {"$set": e}, upsert=True)
        # No need to do a "commit" operation or something like that.
        print("Created entry for user with email %s." % e['email'])

def get_new_biblioplex_api_key(nbr_of_hex_characters = 32):
    """
    Creates a string with 32 hex characters one after the other.
    """
    import numpy as np
    return "".join(
            '%0.2x' % np.random.randint(low=0, high=256)
            for _ in range(nbr_of_hex_characters // 2))
