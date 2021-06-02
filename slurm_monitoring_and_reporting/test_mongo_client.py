from pprint import pprint
from mongo_client import get_mongo_client

def main():
    mc = get_mongo_client({"hostname":"deepgroove.local", "port":27017, "username":"mongoadmin", "password":"secret_password_okay"})
    print(mc['slurm'].list_collection_names())

    # wipe clean
    # mc['slurm']['jobs'].delete_many({"mila_user_account":"unknown"})
    # quit()

    E = list(mc['slurm']['jobs'].find({"mila_user_account":"unknown"}))
    for e in E:
        pprint(e)

if __name__ == "__main__":
    main()